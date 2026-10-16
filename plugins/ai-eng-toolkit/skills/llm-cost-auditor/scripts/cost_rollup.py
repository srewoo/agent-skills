#!/usr/bin/env python3
"""Roll up LLM usage logs into estimated monthly cost per call site and model.

Usage log: JSONL, one line per LLM call:
  {"site": "support_bot.answer", "model": "model-a", "input_tokens": 2400, "output_tokens": 180,
   "cached_input_tokens": 2000, "prompt_hash": "9f2c..."}
  site               call-site label (file:function or feature name)        required
  model              model id as billed                                       required
  input_tokens       total input tokens INCLUDING cached ones                 required
  output_tokens      output tokens, including any reasoning/thinking tokens   required
  cached_input_tokens  portion of input read from the provider's cache      optional
  cache_write_input_tokens  portion of input written to the cache (Anthropic
                     cache_creation_input_tokens), billed at the cache_write price  optional
  prompt_hash        hash of the full request (model+messages+params)        optional, enables duplicate detection

Prices file (JSON, USD per 1M tokens, filled in from the providers' CURRENT pricing pages):
  {"model-a": {"input": 0.0, "output": 0.0, "cached_input": 0.0, "cache_write": 0.0}}
  cached_input and cache_write are optional (default to the input price). Models missing from the file
  are flagged, not guessed.
Rows where cached + cache-write tokens exceed input_tokens are rejected: that usually means input_tokens was
copied from a provider field that excludes cached tokens (Anthropic) without adding them back.

--days is the number of days the log covers; costs are scaled to 30 days.
Batch discounts and explicit-cache storage fees are not modelled; apply them by hand where they apply.
"p95 in" far above "avg in" on one site points at unbounded growth (e.g. full chat history resent each turn).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="usage JSONL")
    ap.add_argument("--prices", required=True, help="JSON prices per 1M tokens")
    ap.add_argument("--days", type=float, required=True, help="days covered by the log")
    args = ap.parse_args()
    if args.days <= 0:
        ap.error("--days must be > 0")
    try:
        with open(args.prices, encoding="utf-8") as fh:
            prices = json.load(fh)
        if not isinstance(prices, dict):
            raise ValueError("must be a JSON object keyed by model id")
        log = open(args.log, encoding="utf-8")
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    agg: dict = defaultdict(lambda: {"calls": 0, "in": 0, "cached": 0, "write": 0, "out": 0, "dupes": 0, "ins": []})
    seen: set = set()
    bad = 0
    with log as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                key = (str(r["site"]), str(r["model"]))
                tin, tout = int(r["input_tokens"]), int(r["output_tokens"])
                cached = int(r.get("cached_input_tokens") or 0)
                write = int(r.get("cache_write_input_tokens") or 0)
                if min(tin, tout, cached, write) < 0 or cached + write > tin:
                    raise ValueError("token counts negative, or cached + cache-write > input_tokens")
            except (ValueError, KeyError, TypeError, AttributeError):
                bad += 1
                continue
            a = agg[key]
            a["calls"] += 1
            a["in"] += tin
            a["ins"].append(tin)
            a["out"] += tout
            a["cached"] += cached
            a["write"] += write
            h = r.get("prompt_hash")
            if h:
                if h in seen:
                    a["dupes"] += 1
                seen.add(h)
    if bad:
        print(f"warning: skipped {bad} malformed line(s) (missing fields, non-integer or negative tokens, "
              f"or cached + cache-write > input_tokens)", file=sys.stderr)
    if not agg:
        print("error: no usable rows", file=sys.stderr)
        return 2

    scale = 30 / args.days
    rows, missing = [], set()
    for (site, model), a in agg.items():
        p = prices.get(model)
        if not (isinstance(p, dict) and isinstance(p.get("input"), (int, float))
                and isinstance(p.get("output"), (int, float))):
            missing.add(model)
            cost = None
        else:
            uncached = a["in"] - a["cached"] - a["write"]
            cost = (uncached * p["input"] + a["cached"] * p.get("cached_input", p["input"])
                    + a["write"] * p.get("cache_write", p["input"]) + a["out"] * p["output"]) / 1e6 * scale
        rows.append((cost, site, model, a))
    rows.sort(key=lambda x: -(x[0] or 0))
    total = sum(r[0] for r in rows if r[0] is not None)

    print(f"{'site':<32} {'model':<20} {'calls/mo':>9} {'avg in':>7} {'p95 in':>7} {'avg out':>7} "
          f"{'cached':>6} {'dupes':>6} {'$/mo':>10} {'share':>6}")
    for cost, site, model, a in rows:
        n = a["calls"]
        ins = sorted(a["ins"])
        p95 = ins[min(n - 1, int(n * 0.95))]
        cost_s = f"{cost:,.2f}" if cost is not None else "price?"
        share = f"{cost / total:.0%}" if cost is not None and total else "-"
        print(f"{site[:32]:<32} {model[:20]:<20} {n * scale:>9,.0f} {a['in'] / n:>7,.0f} {p95:>7,} {a['out'] / n:>7,.0f} "
              f"{a['cached'] / max(a['in'], 1):>6.0%} {a['dupes'] / n:>6.0%} {cost_s:>10} {share:>6}")
    print(f"total estimated $/month (priced models only): {total:,.2f}")
    if missing:
        print(f"no price for: {', '.join(sorted(missing))} — add them to the prices file", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
