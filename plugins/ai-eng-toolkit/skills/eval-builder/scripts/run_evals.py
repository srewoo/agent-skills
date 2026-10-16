#!/usr/bin/env python3
"""Stdlib-only eval harness: run a command per JSONL case, grade with assertions, report pass rates.

Each case line:  {"id": "c1", "input": <any JSON>, "tags": ["happy"], "assert": [<assertion>, ...]}
The command receives the case's "input" as JSON on stdin (and the case id in env EVAL_CASE_ID).
It prints either plain text, or JSON {"output": "...", "tool_calls": [{"name": ...}], "usage": {...}}.
Text assertions apply to "output" when present, otherwise to the whole stdout.

Assertion types:
  equals {value}            contains {value}           not_contains {value}
  icontains {value}         regex {pattern}            not_regex {pattern}
  json_valid                json_keys {keys: [...]}    max_chars {value}
  tool_called {name}        tool_not_called {name}     tool_sequence {names: [...]}  (in order, gaps allowed)
  command {cmd}             external grader: gets {"input","output","tool_calls","case"} JSON on stdin, exit 0 = pass

Exit code: 0 if the --gate metric (mean pass rate, or pass^k) >= --threshold, 1 otherwise, 2 on bad input or when every call fails.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time


def wilson(passed: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = passed / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def parse_stdout(stdout: str) -> dict:
    try:
        obj = json.loads(stdout)
    except ValueError:
        return {"output": stdout, "tool_calls": None, "usage": None}
    if isinstance(obj, dict) and "output" in obj:
        out = obj["output"] if isinstance(obj["output"], str) else json.dumps(obj["output"])
        return {"output": out, "tool_calls": obj.get("tool_calls"), "usage": obj.get("usage")}
    return {"output": stdout, "tool_calls": None, "usage": None}


def tool_names(parsed: dict) -> list[str | None] | None:
    calls = parsed["tool_calls"]
    if not isinstance(calls, list):
        return None
    return [c.get("name") if isinstance(c, dict) else str(c) for c in calls]


def check(a: dict, parsed: dict, case: dict, timeout: float) -> str | None:
    """Return None on pass, or a short failure reason."""
    t, out = a.get("type"), parsed["output"]
    if t == "equals":
        return None if out.strip() == str(a["value"]).strip() else "not equal"
    if t == "contains":
        return None if str(a["value"]) in out else f"missing {a['value']!r}"
    if t == "icontains":
        return None if str(a["value"]).lower() in out.lower() else f"missing {a['value']!r}"
    if t == "not_contains":
        return None if str(a["value"]) not in out else f"contains {a['value']!r}"
    if t == "regex":
        return None if re.search(a["pattern"], out) else f"no match /{a['pattern']}/"
    if t == "not_regex":
        return None if not re.search(a["pattern"], out) else f"matched /{a['pattern']}/"
    if t == "max_chars":
        return None if len(out) <= int(a["value"]) else f"{len(out)} chars > {a['value']}"
    if t in ("json_valid", "json_keys"):
        try:
            obj = json.loads(out)
        except ValueError:
            return "format_break: invalid JSON"
        if t == "json_keys":
            if not isinstance(obj, dict):
                return "format_break: JSON is not an object"
            missing = [k for k in a["keys"] if k not in obj]
            return f"format_break: missing keys {missing}" if missing else None
        return None
    if t in ("tool_called", "tool_not_called", "tool_sequence"):
        names = tool_names(parsed)
        if names is None:
            return "no tool_calls in output"
        if t == "tool_called":
            return None if a["name"] in names else f"tool {a['name']} not called"
        if t == "tool_not_called":
            return None if a["name"] not in names else f"tool {a['name']} called"
        it = iter(names)
        return None if all(n in it for n in a["names"]) else f"sequence {a['names']} not in {names}"
    if t == "command":
        payload = json.dumps({"input": case.get("input"), "output": out, "tool_calls": parsed["tool_calls"], "case": case})
        try:
            r = subprocess.run(a["cmd"], shell=True, input=payload, capture_output=True,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "grader timeout"
        return None if r.returncode == 0 else f"grader: {(r.stdout or r.stderr).strip()[:200]}"
    return f"unknown assertion type {t!r}"


REQUIRED = {"equals": "value", "contains": "value", "icontains": "value", "not_contains": "value",
            "regex": "pattern", "not_regex": "pattern", "json_valid": None, "json_keys": "keys",
            "max_chars": "value", "tool_called": "name", "tool_not_called": "name",
            "tool_sequence": "names", "command": "cmd"}


def assertion_error(a: object) -> str | None:
    """Validate one assertion up front, so a typo can't crash the run after paid calls."""
    if not isinstance(a, dict) or a.get("type") not in REQUIRED:
        return f"unknown assertion {a!r}"
    field = REQUIRED[a["type"]]
    if field and field not in a:
        return f"{a['type']} needs {field!r}"
    if a["type"] in ("regex", "not_regex"):
        try:
            re.compile(a["pattern"])
        except re.error as e:
            return f"bad regex {a['pattern']!r}: {e}"
    if a["type"] == "max_chars" and not isinstance(a["value"], int):
        return "max_chars value must be an integer"
    if a["type"] in ("json_keys", "tool_sequence") and not isinstance(a[field], list):
        return f"{a['type']} {field} must be a list"
    return None


def run_case(case: dict, cmd: str, timeout: float) -> dict:
    env = dict(os.environ, EVAL_CASE_ID=str(case["id"]))
    start = time.monotonic()
    try:
        r = subprocess.run(cmd, shell=True, input=json.dumps(case.get("input")), capture_output=True,
                           text=True, timeout=timeout, env=env)
        stdout, err = r.stdout, (None if r.returncode == 0 else f"exit {r.returncode}: {r.stderr.strip()[:200]}")
    except subprocess.TimeoutExpired:
        stdout, err = "", "timeout"
    latency = round(time.monotonic() - start, 3)
    parsed = parse_stdout(stdout)
    failures = [err] if err else [f for f in (check(a, parsed, case, timeout) for a in case.get("assert", [])) if f]
    return {"id": case["id"], "tags": case.get("tags", []), "passed": not failures, "failures": failures,
            "output": parsed["output"], "tool_calls": parsed["tool_calls"], "usage": parsed["usage"],
            "latency_s": latency}


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def load_cases(path: str, tag: str | None) -> list[dict]:
    cases, seen = [], set()
    try:
        fh = open(path, encoding="utf-8")
    except OSError as e:
        die(f"cannot read {path}: {e}")
    with fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except ValueError as e:
                die(f"{path}:{n}: invalid JSON ({e})")
            if not isinstance(case, dict) or not isinstance(case.get("id"), (str, int)) or case["id"] in seen:
                die(f"{path}:{n}: not an object, or id missing/duplicate/not a string or integer")
            seen.add(case["id"])
            for a in case.get("assert", []):
                err = assertion_error(a)
                if err:
                    die(f"{path}:{n}: case {case['id']}: {err}")
            if not case.get("assert"):
                print(f"warning: case {case['id']} has no assertions (always passes)", file=sys.stderr)
            if tag is None or tag in case.get("tags", []):
                cases.append(case)
    return cases


def summarise(rows: list[dict], samples: int) -> tuple[float, float, str]:
    by_case: dict = {}
    for r in rows:
        by_case.setdefault(r["id"], []).append(r)
    n = len(by_case)
    mean = sum(r["passed"] for r in rows) / len(rows) if rows else 0.0
    all_pass = sum(all(r["passed"] for r in rs) for rs in by_case.values())
    any_pass = sum(any(r["passed"] for r in rs) for rs in by_case.values())
    lo, hi = wilson(all_pass, n)
    lines = [f"cases={n} samples/case={samples}",
             f"mean pass rate      {mean:.1%}",
             f"pass^{samples} (all pass)  {all_pass}/{n} = {all_pass / max(n, 1):.1%}  95% CI [{lo:.1%}, {hi:.1%}]",
             f"pass@{samples} (any pass)  {any_pass}/{n} = {any_pass / max(n, 1):.1%}"]
    tags = sorted({t for r in rows for t in r["tags"]})
    for t in tags:
        tr = [r for r in rows if t in r["tags"]]
        lines.append(f"  tag {t:<16} {sum(r['passed'] for r in tr) / len(tr):.1%}  ({len(tr)} samples)")
    lat = sorted(r["latency_s"] for r in rows)
    if lat:
        lines.append(f"latency p50={lat[len(lat) // 2]:.2f}s p95={lat[min(len(lat) - 1, int(len(lat) * 0.95))]:.2f}s")
    failing = [(cid, rs) for cid, rs in by_case.items() if not all(r["passed"] for r in rs)]
    if failing:
        lines.append("failing cases:")
        for cid, rs in failing:
            reasons = sorted({f for r in rs for f in r["failures"]})
            lines.append(f"  {cid}: {sum(r['passed'] for r in rs)}/{len(rs)} pass; {'; '.join(reasons)[:300]}")
    return mean, all_pass / max(n, 1), "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", required=True, help="JSONL dataset")
    ap.add_argument("--cmd", required=True, help="shell command run once per case per sample")
    ap.add_argument("--samples", type=int, default=1, help="samples per case (use >=3 for non-zero temperature)")
    ap.add_argument("--timeout", type=float, default=120.0, help="seconds per command call")
    ap.add_argument("--tag", help="only run cases with this tag")
    ap.add_argument("--out", help="write per-sample results JSONL here")
    ap.add_argument("--threshold", type=float, default=0.0, help="exit 1 if the --gate metric is below this (0-1)")
    ap.add_argument("--gate", choices=("mean", "passk"), default="mean",
                    help="metric --threshold applies to: mean sample pass rate, or pass^k (share of cases "
                         "where every sample passed; use for Must-criteria suites)")
    args = ap.parse_args()
    if args.samples < 1:
        ap.error("--samples must be >= 1")
    cases = load_cases(args.cases, args.tag)
    if not cases:
        print("error: no cases selected", file=sys.stderr)
        return 2
    out_fh = None
    if args.out:  # open before the run so a bad path can't discard paid results
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            out_fh = open(args.out, "w", encoding="utf-8")
        except OSError as e:
            die(f"cannot write --out: {e}")
    rows = []
    for case in cases:
        for s in range(args.samples):
            row = run_case(case, args.cmd, args.timeout)
            row["sample"] = s
            rows.append(row)
            if out_fh:
                out_fh.write(json.dumps(row) + "\n")
                out_fh.flush()
    if out_fh:
        out_fh.close()
    mean, passk, report = summarise(rows, args.samples)
    print(report)
    if all(r["failures"][:1] and r["failures"][0].startswith(("exit ", "timeout")) for r in rows):
        print("error: every call failed or timed out; check --cmd", file=sys.stderr)
        return 2
    return 0 if (passk if args.gate == "passk" else mean) >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
