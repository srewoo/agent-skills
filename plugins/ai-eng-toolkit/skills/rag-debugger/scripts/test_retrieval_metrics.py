"""Run: python3 test_retrieval_metrics.py  (stdlib unittest, no install needed)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieval_metrics import metrics  # noqa: E402

SCRIPT = str(Path(__file__).with_name("retrieval_metrics.py"))

ROWS = [{"id": "q1", "relevant": ["a", "b"], "retrieved": ["x", "a", "b"]},
        {"id": "q2", "relevant": ["c"], "retrieved": ["y", "z", "w"]}]


class Pure(unittest.TestCase):
    def test_metrics_by_hand(self):
        m, misses = metrics(ROWS, [1, 3])
        self.assertEqual(m[1], {"recall": 0.0, "hit": 0.0, "precision": 0.0})
        # k=3: q1 finds 2/2 (precision 2/3), q2 finds 0
        self.assertAlmostEqual(m[3]["recall"], 0.5)
        self.assertAlmostEqual(m[3]["hit"], 0.5)
        self.assertAlmostEqual(m[3]["precision"], 1 / 3)
        self.assertAlmostEqual(m["mrr"], (1 / 2 + 0) / 2)  # q1 first relevant at rank 2
        self.assertEqual(misses, ["q2"])

    def test_partial_recall(self):
        m, _ = metrics([{"id": "q", "relevant": ["a", "b", "c", "d"], "retrieved": ["a", "x", "c"]}], [2, 3])
        self.assertAlmostEqual(m[2]["recall"], 0.25)
        self.assertAlmostEqual(m[3]["recall"], 0.5)
        self.assertEqual(m["mrr"], 1.0)


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "q.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, lines, *args):
        self.path.write_text("".join((x if isinstance(x, str) else json.dumps(x)) + "\n" for x in lines))
        return subprocess.run([sys.executable, SCRIPT, str(self.path), *args], capture_output=True, text=True)

    def test_report(self):
        r = self.run_cli(ROWS, "--k", "3,1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("queries=2", r.stdout)
        self.assertRegex(r.stdout, r"\n\s+3\s+50\.0%\s+50\.0%\s+33\.3%")
        self.assertIn("MRR 0.250", r.stdout)
        self.assertIn("no relevant id in top 3 (1): q2", r.stdout)

    def test_duplicate_ids_keep_first_rank(self):
        # Without dedup, top-2 would be [d, d] and miss; dedup makes it [d, a].
        r = self.run_cli([{"id": "q", "relevant": ["a"], "retrieved": ["d", "d", "a"]}], "--k", "2")
        self.assertRegex(r.stdout, r"\n\s+2\s+100\.0%")
        self.assertIn("MRR 0.500", r.stdout)

    def test_empty_relevant_skipped_and_missing_id(self):
        r = self.run_cli([{"relevant": [], "retrieved": ["a"]}, {"relevant": ["a"], "retrieved": ["a"]}], "--k", "1")
        self.assertEqual(r.returncode, 0)
        self.assertIn("queries=1", r.stdout)
        self.assertIn("line 1: no relevant ids, skipped", r.stderr)

    def test_bad_input_exits_2(self):
        self.assertEqual(self.run_cli(["{oops"]).returncode, 2)
        self.assertEqual(self.run_cli([{"relevant": "a", "retrieved": []}]).returncode, 2)
        self.assertEqual(self.run_cli([{"relevant": [], "retrieved": []}]).returncode, 2)
        self.assertEqual(self.run_cli(ROWS, "--k", "0").returncode, 2)
        self.assertEqual(self.run_cli(ROWS, "--k", "a").returncode, 2)
        missing = subprocess.run([sys.executable, SCRIPT, str(self.path) + ".nope"], capture_output=True)
        self.assertEqual(missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()
