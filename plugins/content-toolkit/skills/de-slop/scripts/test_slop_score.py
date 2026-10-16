"""Run: python3 test_slop_score.py  (stdlib unittest, no install needed)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slop_score import analyse  # noqa: E402

SLOPPY = """Great question! In today's fast-paced digital world, it's important to note that teams must leverage robust tools.

Why does this matter? Here's the thing: it's not just a tool, it's a mindset.

Let's dive in. We will delve into the tapestry of seamless workflows that unlock and elevate growth.

- 🚀 Faster shipping
- ✅ Fewer bugs

In conclusion, the right tools play a crucial role — and that is a testament to good planning.
"""

HUMAN = """We shipped the billing rewrite on 3 March. Refund tickets fell from 41 a week to 9.

The fix was dull. We moved proration into one function and deleted the other four copies, which had drifted apart over two years.

Two things surprised us. Support noticed first, a full week before the dashboard did. And nobody missed the old admin screen.

Next quarter we tackle invoices. That code is older, and worse.
"""

FENCED = "Plain sentence here.\n```\nleverage robust seamless delve\n```\n"


class SlopScoreTest(unittest.TestCase):
    def test_sloppy_text_scores_high_with_line_numbers(self):
        r = analyse(SLOPPY)
        self.assertGreaterEqual(r["score"], 71)
        for cat in ("vocabulary", "structure", "hedging", "sycophancy", "punctuation"):
            self.assertIn(cat, r["hits"], cat)
        lines = {h["line"] for h in r["hits"]["sycophancy"]}
        self.assertEqual(lines, {1})
        self.assertTrue(any("question opener" in h["match"] for h in r["hits"]["structure"]))

    def test_human_text_scores_clean(self):
        r = analyse(HUMAN)
        self.assertLessEqual(r["score"], 15, r["hits"])

    def test_technical_usage_is_not_flagged(self):
        text = ("The test harness injects faults. The job needs elevated privileges. "
                "The estimator is robust against outliers. Unlock the device first. "
                "Certificates renew over ACME. Run `leverage --robust` to check.")
        self.assertNotIn("vocabulary", analyse(text)["hits"])
        self.assertNotIn("generic-example", analyse(text)["hits"])

    def test_marketing_usage_is_flagged(self):
        text = "Harness the power of AI to unlock new levels of growth and elevate your team."
        self.assertEqual(len(analyse(text)["hits"]["vocabulary"]), 3)

    def test_single_question_and_triad_are_free(self):
        r = analyse("What did we learn? We cut setup, support and churn costs.\n")
        self.assertEqual(r["points"], 0)

    def test_code_fences_are_ignored(self):
        self.assertEqual(analyse(FENCED)["hits"], {})

    def test_uniform_rhythm_is_flagged(self):
        flat = " ".join(["The team met today to review the plan."] * 10)
        self.assertTrue(analyse(flat)["uniform_sentence_length"])

    def test_empty_input(self):
        r = analyse("")
        self.assertEqual((r["score"], r["words"]), (0, 0))


if __name__ == "__main__":
    unittest.main()
