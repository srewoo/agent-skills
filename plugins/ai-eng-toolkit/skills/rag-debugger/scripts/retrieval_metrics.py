#!/usr/bin/env python3
"""Retrieval metrics from a JSONL of queries with labelled relevant ids and the ids your retriever returned.

Each line: {"id": "q1", "query": "...", "relevant": ["doc7#3", "doc7#4"], "retrieved": ["doc2#1", "doc7#3", ...]}
  relevant   ids of chunks (or documents) a human marked as containing the answer
  retrieved  ids in ranked order, exactly as the retriever returned them (before or after reranking);
             repeated ids (e.g. several chunks of one document mapped to its doc id) keep their first rank

Prints, for each k in --k: recall@k (share of relevant ids found in top k, averaged over queries),
hit@k (share of queries with at least one relevant id in top k), precision@k, plus MRR,
and lists the queries with zero relevant ids retrieved at the largest k (pure retrieval misses).
Compare two retriever configs by running this on each file.
"""
from __future__ import annotations

import argparse
import json
import sys


def metrics(rows: list[dict], ks: list[int]) -> tuple[dict, list[str]]:
    out: dict = {}
    for k in ks:
        rec = hit = prec = 0.0
        for r in rows:
            rel, top = set(r["relevant"]), r["retrieved"][:k]
            found = len(rel.intersection(top))
            rec += found / len(rel)
            hit += 1.0 if found else 0.0
            prec += found / k
        n = len(rows)
        out[k] = {"recall": rec / n, "hit": hit / n, "precision": prec / n}
    mrr = 0.0
    for r in rows:
        rel = set(r["relevant"])
        rank = next((i for i, d in enumerate(r["retrieved"], 1) if d in rel), None)
        mrr += 1 / rank if rank else 0.0
    out["mrr"] = mrr / len(rows)
    kmax = max(ks)
    misses = [r["id"] for r in rows if not set(r["relevant"]).intersection(r["retrieved"][:kmax])]
    return out, misses


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="JSONL with id, relevant, retrieved")
    ap.add_argument("--k", default="1,3,5,10", help="comma-separated cut-offs (default 1,3,5,10)")
    args = ap.parse_args()
    try:
        ks = sorted({int(x) for x in args.k.split(",")})
    except ValueError:
        ap.error("--k must be comma-separated integers")
    if not ks or ks[0] < 1:
        ap.error("--k values must be >= 1")
    rows = []
    try:
        fh = open(args.file, encoding="utf-8")
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    with fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                assert isinstance(r["relevant"], list) and isinstance(r["retrieved"], list)
            except (ValueError, KeyError, AssertionError, TypeError):
                print(f"error: line {n}: need JSON object with list fields relevant, retrieved", file=sys.stderr)
                return 2
            if not r["relevant"]:
                print(f"warning: line {n}: no relevant ids, skipped", file=sys.stderr)
                continue
            r["id"] = str(r.get("id", f"line{n}"))
            # duplicates appear when chunk ids are mapped to doc ids; keep the first (best) rank
            r["retrieved"] = list(dict.fromkeys(r["retrieved"]))
            rows.append(r)
    if not rows:
        print("error: no labelled queries", file=sys.stderr)
        return 2
    m, misses = metrics(rows, ks)
    print(f"queries={len(rows)}")
    print(f"{'k':>4} {'recall@k':>9} {'hit@k':>7} {'prec@k':>7}")
    for k in ks:
        print(f"{k:>4} {m[k]['recall']:>9.1%} {m[k]['hit']:>7.1%} {m[k]['precision']:>7.1%}")
    print(f"MRR {m['mrr']:.3f}")
    if misses:
        print(f"no relevant id in top {max(ks)} ({len(misses)}): {', '.join(misses[:30])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
