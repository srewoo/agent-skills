"""Run: python3 test_char_count.py  (stdlib unittest, no install needed)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from char_count import report, split_posts, x_length  # noqa: E402

SCRIPT = str(Path(__file__).with_name("char_count.py"))


def run_cli(*args, stdin=""):
    return subprocess.run([sys.executable, SCRIPT, *args], input=stdin, capture_output=True, text=True)


class XWeight(unittest.TestCase):
    def test_latin_is_one(self):
        self.assertEqual(x_length("hello world"), 11)
        self.assertEqual(x_length("café"), 4)

    def test_cjk_and_emoji_are_two(self):
        self.assertEqual(x_length("日本語"), 6)
        self.assertEqual(x_length("hi 👍"), 5)
        self.assertEqual(x_length("❤️"), 2)  # VS16 adds nothing

    def test_typographic_punctuation_is_one(self):
        self.assertEqual(x_length("“ok” —"), 6)

    def test_urls_count_23(self):
        self.assertEqual(x_length("https://example.com/" + "a" * 100), 23)
        self.assertEqual(x_length("a https://x.io and b.dev."), 2 + 23 + 5 + 23 + 1)
        self.assertEqual(x_length("(see example.org)"), 5 + 23 + 1)

    def test_nfc_normalised(self):
        self.assertEqual(x_length("e\u0301"), 1)  # e + combining acute -> one NFC char


class Report(unittest.TestCase):
    def test_split_posts(self):
        self.assertEqual(split_posts("one\n---\n\ntwo\n  ---  \nthree"), ["one", "two", "three"])
        self.assertEqual(split_posts("---\n---\n"), [])

    def test_limit_boundary(self):
        out, over = report(["a" * 280, "a" * 281], "x", 280)
        self.assertEqual(over, 1)
        self.assertIn("Post 1: 280 chars / 280 OK", out)
        self.assertIn("Post 2: 281 chars / 280 OVER by 1", out)

    def test_non_x_counts_code_points(self):
        out, over = report(["日本 https://example.com"], "threads", 500)
        self.assertIn("Post 1: 22 chars", out)
        self.assertEqual(over, 0)


class Cli(unittest.TestCase):
    def test_stdin_x_over_exits_1(self):
        r = run_cli("-", "--platform", "x", stdin="short\n---\n" + "日" * 141)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Post 2: 282 chars / 280 OVER by 2", r.stdout)
        self.assertIn("2 post(s), 1 over the limit", r.stdout)

    def test_limit_override_and_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "post.txt"
            p.write_text("abcdef", encoding="utf-8")
            self.assertEqual(run_cli(str(p), "--platform", "x").returncode, 0)
            r = run_cli(str(p), "--platform", "x", "--limit", "5")
            self.assertEqual(r.returncode, 1)
            self.assertIn("OVER by 1", r.stdout)

    def test_linkedin_see_more_preview(self):
        r = run_cli("-", "--platform", "linkedin", stdin="line one\nline two")
        self.assertEqual(r.returncode, 0)
        self.assertIn('before "see more" (mobile ~140): line one / line two', r.stdout)

    def test_none_platform_counts_only(self):
        r = run_cli("-", stdin="x" * 5000)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Post 1: 5000 chars\n", r.stdout)

    def test_bad_input(self):
        r = run_cli("/definitely/not/here.txt")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cannot read", r.stderr)
        self.assertEqual(run_cli("-", "--platform", "myspace").returncode, 2)

    def test_selftest(self):
        r = run_cli("--selftest")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "selftest ok"))


if __name__ == "__main__":
    unittest.main()
