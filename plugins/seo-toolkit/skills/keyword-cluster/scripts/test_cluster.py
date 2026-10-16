#!/usr/bin/env python3
"""Tests for cluster.py. Run: python3 test_cluster.py"""
import csv
import io
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cluster  # noqa: E402

SEMRUSH = """Keyword,Position,Previous position,Search Volume,Keyword Difficulty,URL
crm software,8,9,"12,000",78,https://ex.com/crm
best crm software,12,12,5400,74,https://ex.com/blog/best-crm
top crm softwares,15,20,900,70,https://ex.com/crm
crm pricing,4,4,1600,40,https://ex.com/pricing
how to choose a crm,22,30,700,25,https://ex.com/blog/choose-crm
acme login,1,1,3000,10,https://ex.com/login
CRM Software,9,9,12000,78,https://ex.com/features
"""


def run(args, text, name="kw.csv", encoding="utf-8"):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, name)
        with open(path, "w", encoding=encoding, newline="") as f:
            f.write(text)
        out = subprocess.run([sys.executable, cluster.__file__, path, *args], check=True,
                             capture_output=True, text=True)
    return list(csv.DictReader(io.StringIO(out.stdout))), out.stderr


class ClusterTest(unittest.TestCase):
    def test_semrush_clusters_and_cannibalisation(self):
        rows, err = run(["--brand", "acme"], SEMRUSH)
        by_primary = {r["primary_keyword"]: r for r in rows}
        top = by_primary["crm software"]
        # "best crm software" and "top crm softwares" share the topic and are compatible with the seed's intent
        self.assertEqual(set(top["members"].split("; ")), {"crm software", "best crm software", "top crm softwares"})
        self.assertEqual(top["total_volume"], "18300")  # duplicate "CRM Software" row merged, not double-counted
        self.assertIn("CANNIBALISATION", top["action"])  # /crm, /features and /blog/best-crm all rank
        self.assertEqual(by_primary["acme login"]["intent"], "navigational")
        self.assertEqual(by_primary["crm pricing"]["intent"], "transactional")
        self.assertEqual(by_primary["how to choose a crm"]["intent"], "informational")
        self.assertEqual(rows[0]["primary_keyword"], "crm software")  # sorted by total volume
        self.assertIn("volume='Search Volume'", err)

    def test_serp_overlap_beats_lexical(self):
        serp = "keyword,url,position\n" + "".join(
            f"{kw},https://www.site{i}.com/,{i}\n" for kw in ("crm software", "customer database tool")
            for i in range(1, 5)) + "".join(f"crm pricing,https://other{i}.com/,{i}\n" for i in range(1, 5))
        kws = "keyword,volume\ncrm software,100\ncustomer database tool,50\ncrm pricing,40\n"
        with tempfile.TemporaryDirectory() as d:
            sp = os.path.join(d, "serp.csv")
            with open(sp, "w") as f:
                f.write(serp)
            rows, _ = run(["--serp", sp], kws)
        top = next(r for r in rows if r["primary_keyword"] == "crm software")
        self.assertEqual(top["members"], "crm software; customer database tool")  # no shared words, shared SERP
        self.assertEqual(top["method"], "serp")

    def test_gsc_and_keyword_planner_formats(self):
        rows, _ = run(["--level", "keyword"], "Top queries,Clicks,Impressions,CTR,Position\nfoo bar,3,120,2.5%,7.1\n")
        self.assertEqual((rows[0]["keyword"], rows[0]["volume"], rows[0]["position"]), ("foo bar", "120", "7.1"))
        planner = ("Keyword Stats 2026-10-01 at 10_00_00\nAll locations\n"
                   "Keyword\tCurrency\tAvg. monthly searches\tCompetition\nwidget repair\tUSD\t1K - 10K\tLow\n")
        rows, _ = run(["--level", "keyword"], planner, name="kp.csv", encoding="utf-16")
        self.assertEqual((rows[0]["keyword"], rows[0]["volume"]), ("widget repair", "1000"))

    def test_missing_keyword_column_fails_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "bad.csv")
            with open(p, "w") as f:
                f.write("term,vol\nx,1\n")
            res = subprocess.run([sys.executable, cluster.__file__, p], capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("--map keyword=", res.stderr)
            ok = subprocess.run([sys.executable, cluster.__file__, p, "--map", "keyword=term", "--map", "volume=vol"],
                                capture_output=True, text=True, check=True)
            self.assertIn("x", ok.stdout)

    def test_tool_intent_brand_modifiers_and_bad_input(self):
        rows, err = run(["--brand", "acme", "--level", "keyword"],
                        "Keyword,Intent,Volume\nacme pricing,Transactional,10\nacme,Navigational,50\n"
                        "how to choose running shoes,Informational,5\nhow to clean running shoes,Informational,4\n"
                        "mens running shoes,Commercial,9\ntrail running shoes,Commercial,8\n")
        by = {r["keyword"]: r for r in rows}
        self.assertEqual(by["acme pricing"]["intent_guess"], "transactional")  # modifier beats bare brand
        self.assertEqual(by["acme"]["intent_guess"], "navigational")
        self.assertEqual(by["acme pricing"]["tool_intent"], "Transactional")
        self.assertIn("intent='Intent'", err)
        self.assertNotEqual(by["how to choose running shoes"]["cluster_id"], by["how to clean running shoes"]["cluster_id"])
        self.assertNotEqual(by["mens running shoes"]["cluster_id"], by["trail running shoes"]["cluster_id"])
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "empty.csv")
            with open(p, "w") as f:
                f.write("Keyword,Volume\n,10\n")
            res = subprocess.run([sys.executable, cluster.__file__, p], capture_output=True, text=True)
            self.assertIn("empty in every row", res.stderr)
            res = subprocess.run([sys.executable, cluster.__file__, p, "--map", "volume"], capture_output=True, text=True)
            self.assertIn("FIELD=HEADER", res.stderr)

    def test_helpers(self):
        self.assertEqual(cluster.number("1,200"), 1200)
        self.assertEqual(cluster.number("2.5K"), 2500)
        self.assertIsNone(cluster.number(""))
        self.assertEqual(cluster.topic_tokens("best CRM softwares for agencies".lower()),
                         frozenset({"crm", "software", "agency"}))


if __name__ == "__main__":
    unittest.main()
