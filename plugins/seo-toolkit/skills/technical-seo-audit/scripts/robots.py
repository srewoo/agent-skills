"""robots.txt parsing and fetching for crawl.py (standard library only)."""
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class Robots:
    """robots.txt rules as Google applies them: the most specific matching user-agent group,
    `*` and `$` wildcards, longest matching rule wins, Allow wins a tie (RFC 9309)."""

    def __init__(self, text="", ua="", disallow_all=False):
        self.disallow_all, self.rules, self.delay = disallow_all, [], None
        token = re.split(r"[/\s(]", ua.strip().lower(), maxsplit=1)[0]
        groups, agents, body = [], [], None
        for line in text.splitlines():
            key, _, val = line.split("#", 1)[0].partition(":")
            key, val = key.strip().lower(), val.strip()
            if key == "user-agent":
                if body is not None:
                    agents, body = [], None
                agents.append(val.lower())
                if len(agents) == 1:
                    groups.append((agents, []))
            elif key in ("allow", "disallow", "crawl-delay") and agents:
                body = groups[-1][1]
                body.append((key, val))
        named = [a for ags, _ in groups for a in ags if a != "*" and token.startswith(a)]
        best = max(named, key=len) if named else "*"
        for ags, lines in groups:
            if best in ags:
                for key, val in lines:
                    if key == "crawl-delay":
                        try:
                            self.delay = float(val)
                        except ValueError:
                            pass
                    elif val:
                        pat = re.escape(val).replace(r"\*", ".*")
                        pat = pat[:-2] + "$" if pat.endswith(r"\$") else pat
                        self.rules.append((len(val), key == "allow", re.compile(pat)))

    def can_fetch(self, url):
        parts = urlsplit(url)
        path = (parts.path or "/") + ("?" + parts.query if parts.query else "")
        if self.disallow_all:
            return False
        hits = [(length, allow) for length, allow, rx in self.rules if rx.match(path)]
        return max(hits)[1] if hits else True


def load_robots(start, ua, timeout):
    """Fetch robots.txt with our own User-Agent. 401/403/429/5xx => crawl nothing (polite default)."""
    parts = urlsplit(start)
    url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return Robots(resp.read(500_000).decode("utf-8", errors="replace"), ua)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429) or e.code >= 500:
            print(f"warning: robots.txt returned {e.code}; not crawling. (Google treats 4xx other than 429 as "
                  "'no robots.txt'; on 429/5xx it stops crawling, then falls back to a cached copy.)", file=sys.stderr)
            return Robots(disallow_all=True)
    except (urllib.error.URLError, OSError) as e:
        print(f"warning: robots.txt unreachable ({e}); crawling as if none exists", file=sys.stderr)
    return Robots()
