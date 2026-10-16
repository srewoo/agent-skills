#!/usr/bin/env python3
"""Run a test command N times and report its failure rate.

Usage:
  python3 rerun.py --runs 50 -- npx jest src/cart.test.ts -t "applies coupon"
  python3 rerun.py --runs 200 --parallel 4 --json runs.json -- go test -run TestX ./pkg/cart

A run passes when the command exits 0. Each run gets RERUN_INDEX=<n> in its
environment so parallel runs can pick unique ports or temp dirs.
Exit code: 0 if every run passed, 1 if any failed, 2 on usage error or a
command that cannot start.
Stdlib only (Python 3.9+). No network access.
"""
import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_once(index, cmd, timeout, cwd):
    env = dict(os.environ, RERUN_INDEX=str(index))
    start = time.monotonic()
    try:
        # Own process group so a timeout kills the whole tree (jest/gradle
        # workers), not just the wrapper, and leaks nothing into later runs.
        proc = subprocess.Popen(
            cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, start_new_session=(os.name == "posix"),
        )
    except OSError as exc:  # missing binary, not executable, bad --cwd
        code, out, status = None, str(exc).encode(), "error"
    else:
        try:
            out, _ = proc.communicate(timeout=timeout)
            code = proc.returncode
            status = "pass" if code == 0 else "fail"
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            out, _ = proc.communicate()
            code, status = None, "timeout"
    return {
        "run": index,
        "status": status,
        "exit_code": code,
        "seconds": round(time.monotonic() - start, 3),
        "output": (out or b"").decode("utf-8", "replace"),
    }


def upper_bound_95(failures, runs):
    """95% upper bound on the true failure rate (Wilson score interval)."""
    if runs == 0:
        return 1.0
    z = 1.96
    p = failures / runs
    centre = p + z * z / (2 * runs)
    margin = z * math.sqrt(p * (1 - p) / runs + z * z / (4 * runs * runs))
    return min(1.0, (centre + margin) / (1 + z * z / runs))


def summarise(results, tail_lines):
    runs = len(results)
    failed = [r for r in results if r["status"] != "pass"]
    secs = sorted(r["seconds"] for r in results)
    print("\n=== rerun summary ===")
    print(f"runs: {runs}  passed: {runs - len(failed)}  failed: {len(failed)}")
    if runs:
        print(f"failure rate: {len(failed) / runs:.2%}  "
              f"(95% upper bound: {upper_bound_95(len(failed), runs):.2%})")
        print(f"duration s: min {secs[0]:.2f}  median {secs[len(secs) // 2]:.2f}  "
              f"max {secs[-1]:.2f}")
    if failed:
        first = min(failed, key=lambda r: r["run"])
        kinds = sorted({r["status"] for r in failed})
        print(f"failing runs: {[r['run'] for r in sorted(failed, key=lambda r: r['run'])]}"
              f"  kinds: {kinds}")
        print(f"\n--- first failure (run {first['run']}, status {first['status']}, "
              f"exit {first['exit_code']}), last {tail_lines} lines ---")
        print("\n".join(first["output"].splitlines()[-tail_lines:]))
        if all(r["status"] == "error" for r in failed):
            print("\ncommand could not start; fix the command before reading this as flakiness")
            return 2
        if len(failed) == runs:
            print("\nfailed every run: this is a consistent failure, not a flake")
    return 1 if failed else 0


def parse_args(argv):
    p = argparse.ArgumentParser(
        description="Run a test command N times; report pass/fail, durations, "
                    "failure rate and the first failing output.",
        epilog="Put the test command after '--'. Example: "
               "rerun.py --runs 100 -- pytest -p no:randomly tests/test_x.py::test_y",
    )
    p.add_argument("--runs", type=int, default=20, help="number of runs (default 20)")
    p.add_argument("--parallel", type=int, default=1,
                   help="concurrent runs (default 1). >1 adds stress but runs may "
                        "collide on shared ports/files; use RERUN_INDEX to separate them")
    p.add_argument("--timeout", type=float, default=None,
                   help="seconds before a single run is killed and counted as 'timeout'")
    p.add_argument("--stop-on-fail", action="store_true",
                   help="stop scheduling new runs after the first failure")
    p.add_argument("--tail", type=int, default=60,
                   help="lines of the first failing output to print (default 60)")
    p.add_argument("--json", metavar="PATH", help="write every run (with output) to PATH")
    p.add_argument("--cwd", default=None, help="working directory for the command")
    p.add_argument("--quiet", action="store_true", help="no per-run progress lines")
    p.add_argument("cmd", nargs=argparse.REMAINDER, help="test command, after '--'")
    args = p.parse_args(argv)
    if args.cmd and args.cmd[0] == "--":
        args.cmd = args.cmd[1:]
    if not args.cmd:
        p.error("no test command given; put it after '--'")
    if args.runs < 1 or args.parallel < 1:
        p.error("--runs and --parallel must be >= 1")
    return args


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results = []
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        pending = {}
        next_index = 1
        stop = False
        while pending or (next_index <= args.runs and not stop):
            while not stop and next_index <= args.runs and len(pending) < args.parallel:
                fut = pool.submit(run_once, next_index, args.cmd, args.timeout, args.cwd)
                pending[fut] = next_index
                next_index += 1
            done = next(as_completed(pending))
            del pending[done]
            r = done.result()
            results.append(r)
            if not args.quiet:
                print(f"run {r['run']:>4}: {r['status']:<7} {r['seconds']:.2f}s", flush=True)
            if r["status"] != "pass" and args.stop_on_fail:
                stop = True
    results.sort(key=lambda r: r["run"])
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"command": args.cmd, "runs": results}, fh, indent=2)
    return summarise(results, args.tail)


if __name__ == "__main__":
    sys.exit(main())
