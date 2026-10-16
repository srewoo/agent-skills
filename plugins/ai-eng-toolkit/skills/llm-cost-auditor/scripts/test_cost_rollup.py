"""Run: python3 test_cost_rollup.py  (stdlib unittest, no install needed)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).with_name("cost_rollup.py"))
PRICES = {"m": {"input": 3, "output": 15, "cached_input": 0.3}, "w": {"input": 2, "output": 10, "cache_write": 4}}
TOTAL = "total estimated $/month (priced models only): "


def call(site="s", model="m", tin=1_000_000, tout=100_000, **extra):
    return {"site": site, "model": model, "input_tokens": tin, "output_tokens": tout, **extra}


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.prices = self.dir / "prices.json"
        self.prices.write_text(json.dumps(PRICES))

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, rows, days="30", prices=None):
        log = self.dir / "log.jsonl"
        log.write_text("".join((x if isinstance(x, str) else json.dumps(x)) + "\n" for x in rows))
        return subprocess.run([sys.executable, SCRIPT, str(log), "--prices", str(prices or self.prices),
                               "--days", days], capture_output=True, text=True)

    def test_cached_cost_scaled_to_month(self):
        # 2 calls: uncached 1.2M*$3 + cached 0.8M*$0.3 + out 0.2M*$15 = $6.84 per 15 days -> $13.68/mo
        rows = [call(cached_input_tokens=400_000)] * 2
        r = self.run_cli(rows, days="15")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(TOTAL + "13.68", r.stdout)
        self.assertRegex(r.stdout, r"\bs\s+m\s+4 ")  # 2 calls * 30/15 -> 4 calls/mo

    def test_cache_write_price_and_default(self):
        # w: uncached 0.5M*$2 + write 0.5M*$4 + out 0.1M*$10 = $4.00
        r = self.run_cli([call(model="w", cache_write_input_tokens=500_000)])
        self.assertIn(TOTAL + "4.00", r.stdout)
        # m has no cache_write price -> billed at input: 1M*$3 + 0.1M*$15 = $4.50
        r = self.run_cli([call(cache_write_input_tokens=500_000)])
        self.assertIn(TOTAL + "4.50", r.stdout)

    def test_sites_sorted_by_cost_with_share(self):
        r = self.run_cli([call(site="cheap", tin=1_000_000, tout=0), call(site="dear", tin=3_000_000, tout=0)])
        self.assertIn(TOTAL + "12.00", r.stdout)
        body = r.stdout.splitlines()[1:3]
        self.assertTrue(body[0].startswith("dear") and body[0].rstrip().endswith("75%"), body)
        self.assertTrue(body[1].startswith("cheap") and body[1].rstrip().endswith("25%"), body)

    def test_unpriced_model_flagged_not_guessed(self):
        r = self.run_cli([call(), call(model="mystery")])
        self.assertIn("price?", r.stdout)
        self.assertIn(TOTAL + "4.50", r.stdout)
        self.assertIn("no price for: mystery", r.stderr)

    def test_duplicate_prompt_hash(self):
        r = self.run_cli([call(prompt_hash="h"), call(prompt_hash="h")])
        self.assertRegex(r.stdout, r"\s50%\s+9\.00")

    def test_malformed_rows_skipped(self):
        r = self.run_cli([call(), "{bad", call(tin=10, cached_input_tokens=20), call(tin=-1), {"site": "s"}])
        self.assertEqual(r.returncode, 0)
        self.assertIn("skipped 4 malformed", r.stderr)
        self.assertIn(TOTAL + "4.50", r.stdout)

    def test_bad_input_exits_2(self):
        self.assertEqual(self.run_cli(["{bad"]).returncode, 2)               # no usable rows
        self.assertEqual(self.run_cli([call()], days="0").returncode, 2)
        bad_prices = self.dir / "p.json"
        bad_prices.write_text("[1]")
        self.assertEqual(self.run_cli([call()], prices=bad_prices).returncode, 2)
        self.assertEqual(self.run_cli([call()], prices=self.dir / "nope.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
