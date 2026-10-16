#!/usr/bin/env python3
"""Polite same-host SEO crawler (standard library only).

Breadth-first crawl from a start URL. Respects robots.txt (including Crawl-delay),
stays on the start host, waits between requests, does not follow redirects
automatically (so every hop is recorded), and writes one row per URL.

Columns: url, status, redirect_target, content_type, title, meta_description,
canonical, meta_robots, x_robots_tag, h1_count, word_count, internal_links,
inlinks, depth, in_sitemap, hreflang_count, img_missing_alt, jsonld_count,
jsonld_errors, mixed_content, has_viewport, error

depth is the click depth from the start URL. It is empty for URLs that were only
found in the sitemap (--sitemap): those are orphan candidates.

Examples:
  python3 crawl.py https://example.com/ --output crawl.csv
  python3 crawl.py https://example.com/ --sitemap https://example.com/sitemap.xml \
      --max-pages 500 --delay 1 --format json --output crawl.json
  python3 crawl.py https://shop.example/ --exclude '[?&](color|size|sort|page)=' --output crawl.csv
"""
import argparse
import csv
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit

from robots import Robots, load_robots  # noqa: F401  (Robots re-exported for tests)

DEFAULT_UA = "seo-audit-crawler/1.0 (python-stdlib; respects robots.txt)"
MAX_BYTES = 5_000_000
FIELDS = ["url", "status", "redirect_target", "content_type", "title", "meta_description",
          "canonical", "meta_robots", "x_robots_tag", "h1_count", "word_count", "internal_links",
          "inlinks", "depth", "in_sitemap", "hreflang_count", "img_missing_alt", "jsonld_count",
          "jsonld_errors", "mixed_content", "has_viewport", "error"]
SKIP_TEXT = {"title", "script", "style", "noscript", "template", "svg"}
SUBRESOURCE = {"img": "src", "script": "src", "iframe": "src", "source": "src",
               "audio": "src", "video": "src", "link": "href"}


class PageParser(HTMLParser):
    """Collects the on-page SEO signals from one HTML document."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.description, self.robots, self.canonical = None, None, [], None
        self.h1 = self.hreflang = self.img_missing_alt = self.words = 0
        self.mixed = self.jsonld_count = self.jsonld_errors = 0
        self.viewport = False
        self.links = []
        self._in_title = self._in_jsonld = False
        self._skip = 0
        self._title_buf, self._jsonld_buf = [], []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag in SKIP_TEXT:
            self._skip += 1
        if tag == "title" and self.title is None:
            self._in_title = True
        elif tag == "meta":
            name = a.get("name", "").lower()
            if name == "description" and self.description is None:
                self.description = a.get("content", "").strip()
            elif name in ("robots", "googlebot"):
                self.robots.append(a.get("content", "").strip())
            elif name == "viewport":
                self.viewport = True
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            if "canonical" in rel and self.canonical is None:
                self.canonical = a.get("href", "").strip()
            if "alternate" in rel and a.get("hreflang"):
                self.hreflang += 1
        elif tag == "h1":
            self.h1 += 1
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"].strip())
        elif tag == "img" and "alt" not in a:
            self.img_missing_alt += 1  # alt="" is valid for decorative images; only a missing attribute counts
        if tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in_jsonld, self._jsonld_buf = True, []
        attr = SUBRESOURCE.get(tag)
        if attr and a.get(attr, "").lower().startswith("http://") and (tag != "link" or "stylesheet" in a.get("rel", "")):
            self.mixed += 1

    def handle_endtag(self, tag):
        if tag in SKIP_TEXT and self._skip:
            self._skip -= 1
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = " ".join("".join(self._title_buf).split())
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            self.jsonld_count += 1
            try:
                json.loads("".join(self._jsonld_buf))
            except ValueError:
                self.jsonld_errors += 1

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)
        if self._in_jsonld:
            self._jsonld_buf.append(data)
        elif not self._skip:
            self.words += len(data.split())


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # surface 3xx as HTTPError so each hop is recorded


def normalise(url):
    url, _ = urldefrag(url)
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return None
    return parts._replace(netloc=parts.netloc.lower(), path=parts.path or "/").geturl()


def fetch(opener, url, ua, timeout):
    """Return (status, headers, body_bytes_or_None, error)."""
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,*/*;q=0.5"})
    try:
        resp = opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        return e.code, e.headers, None, ""
    except (urllib.error.URLError, OSError, ValueError) as e:
        return "", {}, None, str(getattr(e, "reason", e))
    with resp:
        ctype = resp.headers.get("Content-Type", "")
        body = resp.read(MAX_BYTES) if "html" in ctype.lower() else None
        return resp.status, resp.headers, body, ""


def sitemap_urls(url, opener, ua, timeout, depth=0):
    """URLs from a sitemap or sitemap index (follows one level of nesting per index)."""
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read(60_000_000)
        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        root = ET.fromstring(data)
    except (urllib.error.URLError, OSError, ET.ParseError, EOFError) as e:
        print(f"warning: sitemap {url} unreadable: {e}", file=sys.stderr)
        return []
    locs = [el.text.strip() for el in root.iter() if el.tag.endswith("loc") and el.text]
    if root.tag.endswith("sitemapindex") and depth < 2:
        return [u for sm in locs for u in sitemap_urls(sm, opener, ua, timeout, depth + 1)]
    return locs


def crawl(start, max_pages, delay, ua, timeout, sitemap=None, exclude=None):
    start = normalise(start)
    if not start:
        raise SystemExit("start URL must be http(s)")
    host = urlsplit(start).netloc
    opener = urllib.request.build_opener(NoRedirect)
    robots = load_robots(start, ua, timeout)
    delay = max(delay, robots.delay or 0)
    in_sitemap = set()
    if sitemap:
        in_sitemap = {u for u in map(normalise, sitemap_urls(sitemap, opener, ua, timeout)) if u}
    queue, seen, rows, inlinks = deque([(start, 0)]), {start}, [], {}
    leftovers = deque((u, "") for u in sorted(in_sitemap) if urlsplit(u).netloc == host)
    while (queue or leftovers) and len(rows) < max_pages:
        if queue:
            url, depth = queue.popleft()
        else:  # sitemap URLs never reached by links: orphan candidates, depth left empty
            url, depth = leftovers.popleft()
            if url in seen:
                continue
            seen.add(url)
        if exclude and exclude.search(url) and url != start:
            continue
        row = dict.fromkeys(FIELDS, "")
        row.update(url=url, depth=depth, in_sitemap=url in in_sitemap)
        if not robots.can_fetch(url):
            row.update(status="blocked_by_robots")
            rows.append(row)
            continue
        if rows:
            time.sleep(delay)
        status, headers, body, err = fetch(opener, url, ua, timeout)
        row.update(status=status, error=err, content_type=headers.get("Content-Type", "") if headers else "",
                   x_robots_tag=headers.get("X-Robots-Tag", "") if headers else "")
        nxt = depth + 1 if depth != "" else ""
        if isinstance(status, int) and 300 <= status < 400:
            target = normalise(urljoin(url, headers.get("Location", "")))
            row["redirect_target"] = target or ""
            if target and urlsplit(target).netloc == host and target not in seen:
                seen.add(target)
                queue.append((target, nxt))
            elif target and url == start and urlsplit(target).netloc != host:
                print(f"warning: start URL redirects to another host ({target}); re-run with that URL",
                      file=sys.stderr)
        if body is not None:
            charset = headers.get_content_charset() if hasattr(headers, "get_content_charset") else None
            p = PageParser()
            p.feed(body.decode(charset or "utf-8", errors="replace"))
            internal = []
            for href in p.links:
                link = normalise(urljoin(url, href))
                if link and urlsplit(link).netloc == host:
                    internal.append(link)
            for link in set(internal):
                inlinks[link] = inlinks.get(link, 0) + 1
                if link not in seen:
                    seen.add(link)
                    queue.append((link, nxt))
            canonical = urljoin(url, p.canonical) if p.canonical else ""
            row.update(title=p.title or "", meta_description=p.description or "", canonical=canonical,
                       meta_robots=", ".join(p.robots), h1_count=p.h1, word_count=p.words,
                       internal_links=len(internal), hreflang_count=p.hreflang,
                       img_missing_alt=p.img_missing_alt, jsonld_count=p.jsonld_count,
                       jsonld_errors=p.jsonld_errors,
                       mixed_content=p.mixed if url.startswith("https://") else 0,
                       has_viewport=p.viewport)
        rows.append(row)
    for row in rows:
        row["inlinks"] = inlinks.get(row["url"], 0)
    left = len(queue) + sum(u not in seen for u, _ in leftovers)
    if left:
        print(f"warning: stopped at --max-pages {max_pages}; {left} URLs not crawled",
              file=sys.stderr)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("start_url")
    ap.add_argument("--max-pages", type=int, default=200, help="stop after this many URLs (default 200)")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="seconds between requests (default 1.0; robots.txt Crawl-delay wins if larger)")
    ap.add_argument("--user-agent", default=DEFAULT_UA, help="User-Agent header and robots.txt token")
    ap.add_argument("--timeout", type=float, default=15.0, help="per-request timeout in seconds")
    ap.add_argument("--sitemap", help="sitemap or sitemap-index URL; its URLs are crawled after link discovery")
    ap.add_argument("--exclude", metavar="REGEX",
                    help="skip URLs matching this regex (still counted in inlinks), e.g. '[?&](color|size|sort)='")
    ap.add_argument("--format", choices=["csv", "json"], default="csv")
    ap.add_argument("--output", help="file to write (default stdout)")
    args = ap.parse_args(argv)
    if args.max_pages < 1 or args.delay < 0:
        ap.error("--max-pages must be >= 1 and --delay >= 0")
    try:
        exclude = re.compile(args.exclude) if args.exclude else None
    except re.error as e:
        ap.error(f"--exclude: {e}")
    rows = crawl(args.start_url, args.max_pages, args.delay, args.user_agent, args.timeout, args.sitemap, exclude)
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        if args.format == "json":
            json.dump(rows, out, indent=2, ensure_ascii=False)
            out.write("\n")
        else:
            w = csv.DictWriter(out, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
    finally:
        if out is not sys.stdout:
            out.close()
    print(f"crawled {len(rows)} URLs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
