"""Run: python3 test_compare_runs.py  (stdlib unittest, no install needed)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_runs import categorise, mcnemar_p, tokens  # noqa: E402

SCRIPT = str(Path(__file__).with_name("compare_runs.py"))


def r(cid, passed, failures=None, latency=1.0, usage=None):
    return {"id": cid, "passed": passed, "failures": failures or ([] if passed else ["x"]),
            "latency_s": latency, "usage": usage, "tags": ["must"] if cid.startswith("m") else []}


class Pure(unittest.TestCase):
    def test_mcnemar_by_hand(self):
        self.assertEqual(mcnemar_p(0, 0), 1.0)
        self.assertAlmostEqual(mcnemar_p(0, 5), 2 / 32)          # 2 * C(5,0)/2^5
        self.assertAlmostEqual(mcnemar_p(1, 4), 2 * 6 / 32)      # 2 * (1+5)/2^5
        self.assertAlmostEqual(mcnemar_p(4, 1), 2 * 6 / 32)      # symmetric
        self.assertEqual(mcnemar_p(3, 3), 1.0)                   # capped

    def test_categorise(self):
        T, F = r("a", True), r("a", False)
        brk = r("a", False, ["format_break: invalid JSON"])
        self.assertEqual(categorise([T, T], [F, F]), "regressed")
        self.assertEqual(categorise([F, F], [T, T]), "improved")
        self.assertEqual(categorise([T, T], [T, F, T]), "unstable")
        self.assertEqual(categorise([T], [T]), "neutral")
        self.assertEqual(categorise([T], [brk]), "format_break")
        self.assertEqual(categorise([brk], [brk]), "neutral")

    def test_tokens_accepts_both_usage_shapes(self):
        rows = [r("a", True, usage={"input_tokens": 100, "output_tokens": 10}),
                r("a", True, usage={"prompt_tokens": 300, "completion_tokens": 30}),
                r("a", True)]
        self.assertEqual(tokens(rows), (200, 20))
        self.assertIsNone(tokens([r("a", True)]))


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, rows):
        p = self.dir / name
        p.write_text("".join(json.dumps(x) + "\n" for x in rows))
        return str(p)

    def run_cli(self, old, new, *args):
        return subprocess.run([sys.executable, SCRIPT, "--old", old, "--new", new, *args],
                              capture_output=True, text=True)

    def test_regression_gate(self):
        old = self.write("old.jsonl", [r("a", True), r("b", True), r("c", False)])
        new = self.write("new.jsonl", [r("a", False), r("b", True), r("c", True)])
        res = self.run_cli(old, new)
        self.assertEqual(res.returncode, 1)
        self.assertIn("improved=1, neutral=1, regressed=1 (of 3)", res.stdout)
        self.assertIn("McNemar exact p=1.000 on 1 pass->fail vs 1 fail->pass", res.stdout)
        self.assertEqual(self.run_cli(old, new, "--max-regressions", "1").returncode, 0)

    def test_format_break_always_blocks(self):
        old = self.write("old.jsonl", [r("a", True)])
        new = self.write("new.jsonl", [r("a", False, ["format_break: invalid JSON"])])
        res = self.run_cli(old, new, "--max-regressions", "5")
        self.assertEqual(res.returncode, 1)
        self.assertIn("format_break=1", res.stdout)

    def test_latency_tokens_and_tag(self):
        old = self.write("old.jsonl", [r("m1", True, latency=1.0, usage={"input_tokens": 10, "output_tokens": 2}),
                                       r("x", True)])
        new = self.write("new.jsonl", [r("m1", True, latency=3.0, usage={"input_tokens": 20, "output_tokens": 4}),
                                       r("x", False)])
        res = self.run_cli(old, new, "--tag", "must")
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("(of 1)", res.stdout)
        self.assertIn("latency p50 1.00s -> 3.00s", res.stdout)
        self.assertIn("mean tokens in/out 10/2 -> 20/4", res.stdout)

    def test_bad_input_exits_2(self):
        good = self.write("good.jsonl", [r("a", True)])
        other = self.write("other.jsonl", [r("z", True)])
        self.assertEqual(self.run_cli(good, other).returncode, 2)      # no shared ids
        bad = self.dir / "bad.jsonl"
        bad.write_text('{"id": "a", "passed": "yes", "failures": []}\n')
        self.assertEqual(self.run_cli(good, str(bad)).returncode, 2)
        self.assertEqual(self.run_cli(good, str(self.dir / "nope")).returncode, 2)


if __name__ == "__main__":
    unittest.main()
