"""Self-check for rerun.py: python3 test_rerun.py"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT = str(Path(__file__).with_name("rerun.py"))


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, "--quiet", *args],
                          capture_output=True, text=True)


ok = run("--runs", "4", "--parallel", "2", "--", sys.executable, "-c", "pass")
assert ok.returncode == 0 and "failed: 0" in ok.stdout, ok.stdout

# Fails only on run 3: rate 25%, first failing output shown.
flaky = run("--runs", "4", "--", sys.executable, "-c",
            "import os,sys; i=os.environ['RERUN_INDEX']; print('out', i); sys.exit(i == '3')")
assert flaky.returncode == 1, flaky.stdout
assert "failure rate: 25.00%" in flaky.stdout and "failing runs: [3]" in flaky.stdout
assert "out 3" in flaky.stdout

slow = run("--runs", "1", "--timeout", "0.2", "--", sys.executable, "-c",
           "import time; time.sleep(2)")
assert slow.returncode == 1 and "timeout" in slow.stdout, slow.stdout

missing = run("--runs", "1", "--", "definitely-not-a-command-xyz")
assert missing.returncode == 2 and "could not start" in missing.stdout, missing.stdout

assert run().returncode == 2

if os.name == "posix":
    # A timeout must kill grandchildren too (test runners spawn workers).
    marker = Path(tempfile.mkdtemp()) / "orphan"
    tree = run("--runs", "1", "--timeout", "0.3", "--", "sh", "-c",
               f"(sleep 1; touch {marker}) & wait")
    time.sleep(1.5)
    assert tree.returncode == 1 and not marker.exists(), "orphan survived timeout"

    # A file without +x is a start error, not a crash.
    noexec = Path(tempfile.mkdtemp()) / "t.sh"
    noexec.write_text("exit 0\n")
    bad = run("--runs", "1", "--", str(noexec))
    assert bad.returncode == 2 and "could not start" in bad.stdout, bad.stdout + bad.stderr

always = run("--runs", "2", "--", sys.executable, "-c", "raise SystemExit(1)")
assert always.returncode == 1 and "not a flake" in always.stdout, always.stdout
print("ok")
