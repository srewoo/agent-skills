#!/usr/bin/env python3
"""Compare two eval runs (baseline vs candidate) produced by eval-builder's run_evals.py --out.

Per case it computes the pass rate in each run and assigns one category:
  format_break  candidate fails a json_valid/json_keys check that baseline passed (always a blocker)
  regressed     baseline majority-pass, candidate majority-fail
  improved      baseline majority-fail, candidate majority-pass
  unstable      same majority outcome, but either run has mixed pass/fail samples
  neutral       same outcome, every sample agrees
Also prints an exact McNemar test on the discordant cases, and latency / token deltas
(tokens are read from each row's "usage": input_tokens/output_tokens or prompt_tokens/completion_tokens).

Exit code: 0 if no format breaks and regressions <= --max-regressions, 1 otherwise, 2 on bad input.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys


def load(path: str) -> dict:
    by_case: dict = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    row = json.loads(line)
                    if not isinstance(row.get("passed"), bool) or not isinstance(row.get("failures"), list):
                        raise ValueError("row needs boolean 'passed' and list 'failures' (run_evals.py --out format)")
                    by_case.setdefault(str(row["id"]), []).append(row)
    except (OSError, ValueError, KeyError, AttributeError) as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        sys.exit(2)
    return by_case


def mcnemar_p(b: int, c: int) -> float:
    """Two-sided exact binomial test on discordant pairs (b = pass->fail, c = fail->pass)."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def tokens(rows: list[dict]) -> tuple[float, float] | None:
    ins, outs = [], []
    for r in rows:
        u = r.get("usage") or {}
        i = u.get("input_tokens", u.get("prompt_tokens"))
        o = u.get("output_tokens", u.get("completion_tokens"))
        if i is not None and o is not None:
            ins.append(i)
            outs.append(o)
    return (statistics.mean(ins), statistics.mean(outs)) if ins else None


def pct(values: list[float], q: float) -> float:
    v = sorted(values)
    return v[min(len(v) - 1, int(len(v) * q))] if v else float("nan")


def rate(rows: list[dict]) -> float:
    return sum(r["passed"] for r in rows) / len(rows)


def categorise(old: list[dict], new: list[dict]) -> str:
    def fmt_broken(rows: list[dict]) -> bool:
        return any(f.startswith("format_break") for r in rows for f in r["failures"])

    ro, rn = rate(old), rate(new)
    if fmt_broken(new) and not fmt_broken(old):
        return "format_break"
    if ro > 0.5 >= rn:
        return "regressed"
    if rn > 0.5 >= ro:
        return "improved"
    if 0 < ro < 1 or 0 < rn < 1:
        return "unstable"
    return "neutral"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True, help="baseline results JSONL")
    ap.add_argument("--new", required=True, help="candidate results JSONL")
    ap.add_argument("--max-regressions", type=int, default=0, help="allowed regressed cases (default 0)")
    ap.add_argument("--tag", help="only compare cases carrying this tag (e.g. must)")
    args = ap.parse_args()
    old, new = load(args.old), load(args.new)
    if args.tag:
        old = {k: v for k, v in old.items() if args.tag in (v[0].get("tags") or [])}
        new = {k: v for k, v in new.items() if args.tag in (v[0].get("tags") or [])}
    shared = [cid for cid in old if cid in new]
    only = sorted(set(old) ^ set(new))
    if not shared:
        print("error: no case ids in common", file=sys.stderr)
        return 2
    if only:
        print(f"warning: {len(only)} case(s) in only one run, ignored: {', '.join(only[:10])}", file=sys.stderr)

    cats: dict = {}
    print(f"{'case':<28} {'old':>6} {'new':>6}  category")
    for cid in shared:
        cat = categorise(old[cid], new[cid])
        cats.setdefault(cat, []).append(cid)
        ro, rn = rate(old[cid]), rate(new[cid])
        if cat != "neutral":
            print(f"{cid[:28]:<28} {ro:>6.0%} {rn:>6.0%}  {cat}")

    # McNemar counts every majority flip, including format_break cases that flipped pass->fail
    maj = {cid: (rate(old[cid]) > 0.5, rate(new[cid]) > 0.5) for cid in shared}
    b = sum(o and not n for o, n in maj.values())
    c = sum(n and not o for o, n in maj.values())
    regressed = len(cats.get("regressed", []))
    print("\nsummary: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(cats.items())) + f" (of {len(shared)})")
    print(f"McNemar exact p={mcnemar_p(b, c):.3f} on {b} pass->fail vs {c} fail->pass cases (majority of samples)"
          + ("  (n<10 discordant: underpowered, read cases not p)" if b + c < 10 else ""))

    rows_o = [r for cid in shared for r in old[cid]]
    rows_n = [r for cid in shared for r in new[cid]]
    lo = [r["latency_s"] for r in rows_o if isinstance(r.get("latency_s"), (int, float))]
    ln = [r["latency_s"] for r in rows_n if isinstance(r.get("latency_s"), (int, float))]
    if lo and ln:
        print(f"latency p50 {pct(lo, .5):.2f}s -> {pct(ln, .5):.2f}s; p95 {pct(lo, .95):.2f}s -> {pct(ln, .95):.2f}s")
    else:
        print("latency: not recorded in one or both runs")
    to, tn = tokens(rows_o), tokens(rows_n)
    if to and tn:
        print(f"mean tokens in/out {to[0]:.0f}/{to[1]:.0f} -> {tn[0]:.0f}/{tn[1]:.0f}")
    else:
        print("tokens: no usage data in one or both runs")
    blocked = bool(cats.get("format_break")) or regressed > args.max_regressions
    print("gate: " + ("FAIL" if blocked else "PASS") + f" (format_break={len(cats.get('format_break', []))}, "
          f"regressed={regressed}, allowed={args.max_regressions})")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
