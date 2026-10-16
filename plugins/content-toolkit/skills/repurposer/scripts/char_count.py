#!/usr/bin/env python3
"""Check social posts against platform character limits.

Put each post in one file (or stdin), separated by a line containing only ---
  python3 char_count.py thread.txt --platform x
  python3 char_count.py - --platform linkedin < post.txt

Platforms and limits (defaults, as of 2026; platforms change them, override with --limit):
  x         280, weighted like X: URLs = 23, most CJK/emoji = 2
  linkedin  3000, also shows the text before the "see more" cut (~140 mobile, ~210 desktop)
  threads   500    bluesky 300 (graphemes; links count in full)    instagram 2200 (caption)
  none      count only

Counts are code points (X: weighted). Complex emoji (flags, ZWJ families) may be
over-counted, which errs on the safe side. Exit code 1 if any post is over, 2 if the input cannot be read.
Run `python3 char_count.py --selftest` to verify. Standard library only; Python 3.9+.
"""
import argparse
import re
import sys
import unicodedata

LIMITS = {"x": 280, "linkedin": 3000, "threads": 500, "bluesky": 300, "instagram": 2200, "none": None}
# Trailing punctuation after a URL ("see https://a.com/x.") is text, not part of the link.
URL = re.compile(r"(?:https?://|\b[\w-]+\.(?:com|org|net|io|co|ai|dev|app)\b)(?:\S*[^\s.,!?;:)\]'\"])?", re.IGNORECASE)
# twitter-text v3: these ranges weigh 1, everything else weighs 2.
X_LIGHT = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
VS16_ZWJ = {0xFE0F, 0x200D}


def x_length(text):
    text = unicodedata.normalize("NFC", text)
    total, pos = 0, 0
    for m in URL.finditer(text):
        total += _x_weight(text[pos:m.start()]) + 23
        pos = m.end()
    return total + _x_weight(text[pos:])


def _x_weight(chunk):
    n = 0
    for ch in chunk:
        cp = ord(ch)
        if cp in VS16_ZWJ:
            continue  # modifiers don't add visible length
        n += 1 if any(lo <= cp <= hi for lo, hi in X_LIGHT) else 2
    return n


def split_posts(text):
    posts = [p.strip("\n") for p in re.split(r"^\s*---\s*$", text, flags=re.MULTILINE)]
    return [p for p in posts if p.strip()]


def report(posts, platform, limit):
    rows, over = [], 0
    for i, post in enumerate(posts, 1):
        n = x_length(post) if platform == "x" else len(unicodedata.normalize("NFC", post))
        status = "" if limit is None else ("OK" if n <= limit else "OVER by %d" % (n - limit))
        over += status.startswith("OVER")
        rows.append("Post %d: %d chars%s%s" % (i, n, "" if limit is None else " / %d " % limit, status))
        if platform == "linkedin":
            flat = post.replace("\n", " / ")
            rows.append('  before "see more" (mobile ~140): ' + flat[:140])
            rows.append('  before "see more" (desktop ~210): ' + flat[:210])
    rows.append("%d post(s), %d over the limit" % (len(posts), over))
    return "\n".join(rows), over


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="text file, or - for stdin")
    ap.add_argument("--platform", choices=sorted(LIMITS), default="none")
    ap.add_argument("--limit", type=int, help="override the platform limit")
    args = ap.parse_args(argv)
    try:
        text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    except OSError as exc:
        print("error: cannot read %s: %s" % (args.file, exc), file=sys.stderr)
        sys.exit(2)
    out, over = report(split_posts(text), args.platform, args.limit or LIMITS[args.platform])
    print(out)
    sys.exit(1 if over else 0)


def _selftest():
    assert x_length("hello") == 5
    assert x_length("see https://example.com/a/very/long/path/that/is/long") == 4 + 23
    assert x_length("日本") == 4
    assert x_length("ok 👍") == 5
    assert x_length("read https://example.com/post.") == 5 + 23 + 1
    assert x_length("example.com") == 23
    assert split_posts("a\n---\nb\n---\n") == ["a", "b"]
    _, over = report(["x" * 281], "x", 280)
    assert over == 1
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
    else:
        main()
