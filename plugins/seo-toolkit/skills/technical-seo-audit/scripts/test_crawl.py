#!/usr/bin/env python3
"""Tests for crawl.py against a local http.server fixture (no real sites).

Run: python3 test_crawl.py
"""
import functools
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crawl  # noqa: E402

FIXTURE = {
    "robots.txt": "User-agent: *\nDisallow: /private/\n",
    "index.html": """<!doctype html><html><head><title> Home  Page </title>
<meta name="description" content="Welcome">
<meta name="viewport" content="width=device-width">
<link rel="canonical" href="/">
<script type="application/ld+json">{"@type": "Organization",}</script>
<script>var ignored = "not counted as words";</script>
</head><body><h1>Hello world</h1><p>one two three</p>
<img src="/logo.png"><img src="/deco.png" alt="">
<a href="/about.html">About</a> <a href="/blog">Blog</a> <a href="/missing.html#x">Gone</a>
<a href="/private/secret.html">Secret</a> <a href="https://other.example/">Ext</a>
<a href="mailto:a@b.c">Mail</a></body></html>""",
    "about.html": """<html><head><title>About</title><meta name="robots" content="noindex, follow">
</head><body><h1>A</h1><h1>B</h1><a href="/">Home</a></body></html>""",
    "blog/index.html": '<html><head><title>Blog</title></head><body><a href="post.html">Post</a></body></html>',
    "blog/post.html": "<html><head><title>Post</title></head><body><p>deep</p></body></html>",
    "orphan.html": "<html><head><title>Orphan</title></head><body>alone</body></html>",
    "private/secret.html": "<html><title>Secret</title></html>",
}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class CrawlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        for name, body in FIXTURE.items():
            path = os.path.join(cls.tmp.name, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(body)
        cls.server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(Quiet, directory=cls.tmp.name))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        with open(os.path.join(cls.tmp.name, "sitemap.xml"), "w") as f:
            f.write('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    f"<url><loc>{cls.base}/</loc></url><url><loc>{cls.base}/about.html</loc></url>"
                    f"<url><loc>{cls.base}/orphan.html</loc></url></urlset>")
        rows = crawl.crawl(cls.base + "/", 50, 0, "test-bot/1.0", 5, cls.base + "/sitemap.xml")
        cls.rows = {r["url"].replace(cls.base, ""): r for r in rows}

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def test_home_signals(self):
        r = self.rows["/"]
        self.assertEqual(r["status"], 200)
        self.assertEqual(r["title"], "Home Page")
        self.assertEqual(r["meta_description"], "Welcome")
        self.assertEqual(r["canonical"], self.base + "/")
        self.assertEqual((r["h1_count"], r["depth"], r["img_missing_alt"]), (1, 0, 1))
        self.assertEqual((r["jsonld_count"], r["jsonld_errors"]), (1, 1))
        self.assertTrue(r["has_viewport"])
        self.assertEqual(r["word_count"], 11)  # h1(2) + p(3) + 6 link texts; title/script excluded
        self.assertEqual(r["internal_links"], 4)

    def test_redirect_recorded_and_followed(self):
        r = self.rows["/blog"]
        self.assertEqual(r["status"], 301)
        self.assertEqual(r["redirect_target"], self.base + "/blog/")
        self.assertEqual(self.rows["/blog/"]["depth"], 2)
        self.assertEqual(self.rows["/blog/post.html"]["depth"], 3)

    def test_status_robots_noindex(self):
        self.assertEqual(self.rows["/missing.html"]["status"], 404)
        self.assertEqual(self.rows["/private/secret.html"]["status"], "blocked_by_robots")
        about = self.rows["/about.html"]
        self.assertEqual(about["meta_robots"], "noindex, follow")
        self.assertEqual(about["h1_count"], 2)
        self.assertTrue(about["in_sitemap"])

    def test_orphan_and_inlinks(self):
        orphan = self.rows["/orphan.html"]
        self.assertEqual((orphan["depth"], orphan["inlinks"], orphan["status"]), ("", 0, 200))
        self.assertTrue(orphan["in_sitemap"])
        self.assertEqual(self.rows["/"]["inlinks"], 1)
        self.assertNotIn("https://other.example/", [r["url"] for r in self.rows.values()])

    def test_max_pages_and_cli_json(self):
        out = os.path.join(self.tmp.name, "out.json")
        subprocess.run([sys.executable, crawl.__file__, self.base + "/", "--max-pages", "2", "--delay", "0",
                        "--format", "json", "--output", out], check=True, capture_output=True)
        with open(out) as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)
        self.assertEqual(set(data[0]), set(crawl.FIELDS))

    def test_exclude_skips_but_counts_inlinks(self):
        import re
        rows = crawl.crawl(self.base + "/", 50, 0, "test-bot/1.0", 5, exclude=re.compile(r"/blog"))
        urls = [r["url"].replace(self.base, "") for r in rows]
        self.assertNotIn("/blog", urls)
        self.assertIn("/about.html", urls)


class RobotsTest(unittest.TestCase):
    def test_google_style_matching(self):
        txt = ("User-agent: *\nDisallow: /\n\nUser-agent: other-bot\nUser-agent: seo-audit-crawler\n"
               "Disallow: /*?*sort=\nDisallow: /*.pdf$\nDisallow: /shop/\nAllow: /shop/shoes\nCrawl-delay: 2\n")
        r = crawl.Robots(txt, crawl.DEFAULT_UA)
        self.assertEqual(r.delay, 2.0)
        self.assertFalse(r.can_fetch("https://x.com/c?color=red&sort=price"))  # wildcard
        self.assertTrue(r.can_fetch("https://x.com/c?color=red"))
        self.assertFalse(r.can_fetch("https://x.com/a/b.pdf"))
        self.assertTrue(r.can_fetch("https://x.com/a/b.pdf?v=1"))  # $ anchors the end
        self.assertTrue(r.can_fetch("https://x.com/shop/shoes/red"))  # longer Allow wins
        self.assertFalse(r.can_fetch("https://x.com/shop/hats"))
        self.assertFalse(crawl.Robots(txt, "unknown-bot").can_fetch("https://x.com/"))  # falls back to *


class CrossHostRedirect(Quiet):
    def do_GET(self):
        self.send_response(404 if self.path == "/robots.txt" else 301)
        self.send_header("Location", "http://localhost:1/")
        self.end_headers()


class StartRedirectTest(unittest.TestCase):
    def test_start_redirect_to_other_host_is_reported_not_followed(self):
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), CrossHostRedirect)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            res = subprocess.run([sys.executable, crawl.__file__, f"http://127.0.0.1:{server.server_address[1]}/",
                                  "--delay", "0"], capture_output=True, text=True, check=True)
        finally:
            server.shutdown()
            server.server_close()
        self.assertIn("redirects to another host", res.stderr)
        self.assertEqual(len(res.stdout.strip().splitlines()), 2)  # header + the single 301 row


if __name__ == "__main__":
    unittest.main()
