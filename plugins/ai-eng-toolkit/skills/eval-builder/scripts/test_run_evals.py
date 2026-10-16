"""Run: python3 test_run_evals.py  (stdlib unittest, no install needed)."""
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_evals import assertion_error, check, parse_stdout, summarise, wilson  # noqa: E402

SCRIPT = str(Path(__file__).with_name("run_evals.py"))
PY = shlex.quote(sys.executable)
# App under test: echoes the case input back as plain text.
ECHO = f"{PY} -c \"import json,sys; print(json.load(sys.stdin))\""


def row(cid, passed, tags=(), latency=0.1):
    return {"id": cid, "tags": list(tags), "passed": passed, "failures": [] if passed else ["x"],
            "latency_s": latency}


class Pure(unittest.TestCase):
    def test_wilson_by_hand(self):
        # 8/10, z=1.96: centre=(0.8+0.19208)/1.38416, half=1.96*sqrt(0.025604)/1.38416
        lo, hi = wilson(8, 10)
        self.assertAlmostEqual(lo, 0.49016, places=4)
        self.assertAlmostEqual(hi, 0.94332, places=4)
        self.assertEqual(wilson(0, 0), (0.0, 0.0))
        self.assertEqual(wilson(5, 5)[1], 1.0)

    def test_summarise_mean_passk_passat(self):
        rows = [row("a", True, ["happy"]), row("a", False, ["happy"]), row("b", True), row("b", True)]
        mean, passk, report = summarise(rows, 2)
        self.assertEqual((mean, passk), (0.75, 0.5))
        self.assertIn("pass@2 (any pass)  2/2 = 100.0%", report)
        self.assertIn("tag happy", report)
        self.assertIn("a: 1/2 pass; x", report)

    def test_parse_stdout_json_and_text(self):
        p = parse_stdout(json.dumps({"output": "hi", "tool_calls": [{"name": "search"}]}))
        self.assertEqual(p["output"], "hi")
        self.assertEqual(parse_stdout("plain")["output"], "plain")

    def test_check_assertions(self):
        p = {"output": '{"a": 1}', "tool_calls": [{"name": "s"}, {"name": "f"}, {"name": "w"}], "usage": None}
        self.assertIsNone(check({"type": "json_keys", "keys": ["a"]}, p, {}, 5))
        self.assertTrue(check({"type": "json_keys", "keys": ["b"]}, p, {}, 5).startswith("format_break"))
        self.assertIsNone(check({"type": "tool_sequence", "names": ["s", "w"]}, p, {}, 5))
        self.assertIsNotNone(check({"type": "tool_sequence", "names": ["w", "s"]}, p, {}, 5))
        self.assertIsNotNone(check({"type": "max_chars", "value": 3}, p, {}, 5))
        self.assertEqual(check({"type": "json_valid"}, {"output": "no", "tool_calls": None}, {}, 5),
                         "format_break: invalid JSON")

    def test_assertion_error(self):
        self.assertIsNone(assertion_error({"type": "contains", "value": "x"}))
        self.assertIn("needs", assertion_error({"type": "contains"}))
        self.assertIn("bad regex", assertion_error({"type": "regex", "pattern": "("}))
        self.assertIn("integer", assertion_error({"type": "max_chars", "value": "3"}))
        self.assertIn("unknown", assertion_error({"type": "nope"}))


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def cases(self, *lines):
        p = self.dir / "cases.jsonl"
        p.write_text("\n".join(lines) + "\n")
        return str(p)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)

    def test_pass_rate_threshold_and_out(self):
        path = self.cases(
            json.dumps({"id": "c1", "input": "hello", "assert": [{"type": "contains", "value": "hello"}]}),
            json.dumps({"id": "c2", "input": "x", "assert": [{"type": "equals", "value": "y"}]}))
        out = self.dir / "res" / "out.jsonl"
        r = self.run_cli("--cases", path, "--cmd", ECHO, "--threshold", "0.5", "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("mean pass rate      50.0%", r.stdout)
        rows = [json.loads(line) for line in out.read_text().splitlines()]
        self.assertEqual([(x["id"], x["passed"]) for x in rows], [("c1", True), ("c2", False)])
        r = self.run_cli("--cases", path, "--cmd", ECHO, "--threshold", "0.6")
        self.assertEqual(r.returncode, 1)

    def test_case_id_env_and_tag_filter(self):
        path = self.cases(
            json.dumps({"id": "c1", "tags": ["t"], "assert": [{"type": "equals", "value": "c1"}]}),
            json.dumps({"id": "c2", "assert": [{"type": "equals", "value": "nope"}]}))
        cmd = f"{PY} -c \"import os; print(os.environ['EVAL_CASE_ID'])\""
        r = self.run_cli("--cases", path, "--cmd", cmd, "--tag", "t", "--threshold", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("cases=1", r.stdout)

    def test_bad_input_exits_2(self):
        bad_json = self.cases("{not json")
        self.assertEqual(self.run_cli("--cases", bad_json, "--cmd", ECHO).returncode, 2)
        bad_assert = self.cases(json.dumps({"id": "c", "assert": [{"type": "regex", "pattern": "("}]}))
        self.assertEqual(self.run_cli("--cases", bad_assert, "--cmd", ECHO).returncode, 2)
        dup = self.cases(json.dumps({"id": "c"}), json.dumps({"id": "c"}))
        self.assertEqual(self.run_cli("--cases", dup, "--cmd", ECHO).returncode, 2)
        missing = str(self.dir / "missing.jsonl")
        self.assertEqual(self.run_cli("--cases", missing, "--cmd", ECHO).returncode, 2)

    def test_every_call_failing_exits_2(self):
        path = self.cases(json.dumps({"id": "c", "assert": [{"type": "contains", "value": "a"}]}))
        r = self.run_cli("--cases", path, "--cmd", f"{PY} -c \"raise SystemExit(3)\"")
        self.assertEqual(r.returncode, 2)
        self.assertIn("every call failed", r.stderr)


if __name__ == "__main__":
    unittest.main()
