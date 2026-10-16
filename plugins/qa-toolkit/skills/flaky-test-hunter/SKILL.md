---
name: flaky-test-hunter
description: Use when a test passes and fails intermittently without code changes - "flaky test", "flake", "fails on CI but passes locally", "only fails in the full suite", "passes on rerun", "intermittent failure", "randomly red build", "works on my machine", "timing issue in tests", "quarantine this test", or a CI retry plugin keeps masking the same failure.
---

# Flaky Test Hunter

## Overview

A flaky test is a deterministic program with a hidden input: time, order, randomness, the network, shared state, or scheduling. Reproduce the flake on demand, name the hidden input, remove it, then prove the fix with enough consecutive green runs. Sleeps and retries hide the hidden input. They are never the fix.

## When to use / When not to use

- Use for one named test (or a small cluster) that flips between pass and fail on the same commit.
- Use when a suite only fails in CI, only in parallel, or only after another test.
- Not for a test that fails every time. That is a real failure, so debug it directly.
- Not for turning a vague bug report into a failing test. Use `bug-report-to-repro`.
- Not for whole-suite slowness or infrastructure outages (runner OOM, registry down). Fix the infrastructure.

## Inputs

| Input | Default if not given |
|---|---|
| Test identifier (file + name) | Ask. Without it there is nothing to hunt. If the user only has a CI link, read the log and extract it. |
| Failing CI log or error text | Ask once. Rerun locally to capture it if they have none. |
| Test runner and command | Detect from `package.json`, `pyproject.toml`/`pytest.ini`, `go.mod`, `build.gradle(.kts)`/`pom.xml`, `playwright.config.*`, `cypress.config.*`. |
| Observed failure rate | Unknown. Step 2 measures it. |
| Verification budget (runs) | Computed in step 6 from the measured rate. |

## Workflow

### 1. Capture the failure signature

Read the CI log for the failing run and for a passing run of the same commit. Record the assertion message, stack top frame, test duration, worker/shard id, the test that ran just before it, OS, runtime version, timezone and locale.
**Done when** you can state the exact failure in one line, such as `expected 3 items, got 2 at cart.test.ts:88, on shard 2/4, after inventory.test.ts`.

### 2. Reproduce by repetition, in isolation

Run only the test, many times, with retries **off**. Prefer the runner's native repeat. Otherwise use the bundled script, which works for any command. The `scripts/` path is relative to this skill's folder. Run the test command from the directory CI uses, which in monorepos usually means the package directory, or wrap it with `pnpm --filter <pkg> exec …` / `yarn workspace <pkg> …`:

```sh
python3 scripts/rerun.py --runs 100 --timeout 300 --json runs.json -- <test command>
```

It prints pass/fail counts, the failure rate with a 95% upper bound, the duration spread and the tail of the first failing output. It exits 1 if any run failed.

| Runner | Isolate and repeat one test |
|---|---|
| Jest | No repeat flag. `python3 scripts/rerun.py --runs 100 -- npx jest path/to/file.test.ts -t "test name" --runInBand`. Shuffle order inside a file: `--randomize --seed=<n>` (`--randomize` needs Jest ≥ 29.5; `--seed`/`--showSeed` exist since 29.2) |
| Vitest | No CLI repeat flag. Temporarily add `test('name', { repeats: 99 }, () => {...})` (the count is extra runs, so 99 gives 100 runs), or loop with rerun.py over `npx vitest run path -t "name"`. Shuffle: `--sequence.shuffle --sequence.seed=<n>`. Make sure `--retry` is 0 |
| pytest | `pip install pytest-repeat`, then `pytest "tests/test_x.py::test_y" --count=100 -p no:randomly`. Add `-x` to stop at the first failure, but leave it off when you are measuring the rate. Use `--repeat-scope=session` to repeat the whole selection in order. Do not run `pytest-rerunfailures` (`--reruns`) during the hunt |
| Go | `go test -run '^TestY$' -count=100 -race ./pkg/x` (`-count` also bypasses the test cache). Add `-shuffle=on` for order and `-cpu=1,2,8` for scheduling |
| JUnit 5 | Temporarily swap `@Test` for `@RepeatedTest(100)`. Gradle: `./gradlew test --tests 'com.acme.CartTest.appliesCoupon' --rerun-tasks`. Maven: `mvn test -Dtest='CartTest#appliesCoupon' -Dsurefire.rerunFailingTestsCount=0` |
| Playwright | `npx playwright test cart.spec.ts -g "applies coupon" --repeat-each=100 --retries=0 --workers=1` |
| Cypress | No native repeat. With `@cypress/grep`: `npx cypress run --spec cypress/e2e/cart.cy.ts --expose grep="applies coupon",burn=50 --config retries=0` (`--expose` is @cypress/grep v6+ on Cypress ≥ 15.10; v5 and earlier take `--env grep=…,burn=50`). Without it, wrap the test in `Cypress._.times(50, () => it(...))` temporarily |

Then check the result against these outcomes:

- **Fails in isolation**: the cause is inside the test or the code under test (timing, randomness, time, concurrency, network).
- **Never fails in 100+ isolated runs**: go to step 3, because it probably depends on order, load or environment.
- **Done when** you have a command that reproduces the failure at least once in a known number of runs, with the failure rate written down.

### 3. If isolation is green, widen the blast radius

Try these in order. Stop as soon as it fails.

1. **Full file, then full suite, same order as CI.** Use CI's shard or worker split, such as `npx jest --shard=2/4`, the same Playwright `--shard`, or the same pytest-xdist `-n` setting.
2. **Order.** Shuffle with a fixed seed so the failure replays: `pytest -p randomly --randomly-seed=12345`, `go test -shuffle=on` (it prints the seed, and you replay with `-shuffle=<seed>`), `jest --randomize --seed=12345`, `vitest --sequence.shuffle --sequence.seed=12345`, or JUnit 5 via `src/test/resources/junit-platform.properties`: `junit.jupiter.testmethod.order.default=org.junit.jupiter.api.MethodOrderer$Random`, `junit.jupiter.testclass.order.default=org.junit.jupiter.api.ClassOrderer$Random` (class order matters for shared DB/Spring context state) and `junit.jupiter.execution.order.random.seed=12345`. For pytest-xdist, order is per worker: take the tests the verbose CI log (`-v` prints `[gw2] PASSED …`) shows on the victim's worker before it, and replay them serially with `-n 0 -p no:randomly`; `pip install detect-test-pollution` then `detect-test-pollution --failing-test <nodeid> --tests <dir>` automates the bisect. Once a seed fails, bisect the preceding tests: run `<suspect-half> + target` and keep halving until a single polluter is left.
3. **Load.** Use more workers than cores (`--maxWorkers=16`, `-n 16`, `--workers=8`, Gradle `maxParallelForks`, Surefire `-DforkCount=4`), `rerun.py --parallel 4`, or a CPU limit (`docker run --cpus=0.5 …`, `taskset -c 0 …` on Linux). For browser tests, slow the CPU with Chrome DevTools Protocol `Emulation.setCPUThrottlingRate` (rate 4).
4. **Environment.** Try `TZ=Pacific/Kiritimati`, `TZ=America/St_Johns`, `LANG=tr_TR.UTF-8`, a clock near midnight, month-end, DST changeover or Feb 29, the CI container image, and a clean checkout with no local caches or `.env`.

**Done when** one of these reproduces the failure, or you have run all four and recorded what you tried. In that case, go to step 7 with that evidence.

### 4. Name the root cause

Match the signature and the trigger that reproduced it against the taxonomy in [references/root-causes.md](references/root-causes.md). It covers nine classes: async/timing, order and shared state, time/timezone, randomness, network/external services, resource leaks and ports, concurrency/races, environment/locale, and UI animation/selectors. Each class lists its symptoms, how to confirm it, and the deterministic fix.
Confirm the cause before you fix anything. Change only the suspected input (pin the seed, freeze the clock, run the polluter first, block the network) and show the failure rate flip from >0% to 0%, or from 0% to 100%.
**Done when** you can force the failure on purpose, or prevent it on purpose, by controlling one named input.

### 5. Fix by removing the non-determinism

- Fix whichever side owns the bug. If production code has a real race (a missing `await`, an unsynchronised map, a check-then-act sequence), fix the product and tell the user it was a real bug, not a test problem.
- Use the deterministic fixes from the reference: wait on a condition instead of a duration, inject or freeze the clock, seed or inject RNG, give each test fresh state, use a hermetic fake for the network, bind port 0, and use web-first assertions with role-based locators.
- Banned as fixes: `sleep`/`setTimeout`/`Thread.sleep`/`time.Sleep`, larger timeouts on their own, retries (`jest.retryTimes`, `--reruns`, `retries:` config, `@Flaky`-style rerun annotations), and catch-and-ignore. A timeout increase is acceptable only when the measured legitimate duration exceeds the current limit. State the numbers if you make one.
- Remove any temporary `repeats`, `@RepeatedTest` or `Cypress._.times` you added.

**Done when** the diff touches the cause you named in step 4 and nothing else.

### 6. Verify with enough consecutive green runs

Rerun the exact reproduction from step 2 or 3, with the same seed, load and environment, until you reach N consecutive passes. Pick N so that a flake at the measured rate `p` would very likely have shown up: `N = ceil(ln(0.05) / ln(1 - p))`, which gives 95% confidence.

| Measured failure rate | Consecutive green runs needed |
|---|---|
| 20% | 14 |
| 5% | 59 |
| 2% | 149 |
| 1% | 299 |
| < 1% or unknown | ≥ 300, or prove the cause is gone by forcing the trigger (seed/order/clock) and showing a pass |

Also run the full suite once in the CI configuration to make sure the fix did not break neighbouring tests.
**Done when** rerun.py reports `failed: 0` for N runs and you have pasted its summary block into the report.

### 7. Quarantine only if a fix is not possible now

Quarantine only when the cause is outside your control (a third-party sandbox, or a hardware-dependent test) or the fix needs a decision from the owning team. Get the user's confirmation first. Then:

- Skip it with a linked ticket in the reason, such as `test.skip` / `@pytest.mark.skip(reason="FLAKY-123 …")` / `t.Skip("FLAKY-123 …")` / `@Disabled("FLAKY-123 …")` / `test.fixme`. Alternatively, move it to a separate non-blocking CI job that still runs and reports.
- Record the owner, root-cause hypothesis, failure rate, evidence and a review-by date (default: 14 days).
- Never quarantine a test that guards money, auth, data integrity or security without the owner's explicit approval.

**Done when** the ticket exists and the skip reason links to it.

## Output

```markdown
## Flaky test: <file>::<test name>

**Verdict:** fixed | real product bug fixed | quarantined (<ticket>) | not reproduced
**Root cause class:** <one of the nine classes>; **hidden input:** <e.g. wall clock crosses midnight UTC>

| | Before | After |
|---|---|---|
| Reproduction command | `<exact command incl. seed/env>` | same |
| Runs / failures | 200 / 9 (4.5%) | 300 / 0 |
| Trigger | <order: runs after inventory.test.ts / load / TZ / none> | - |

**Evidence:** <one or two lines showing the forced failure or forced pass from step 4>
**Fix:** <what changed and why it removes the non-determinism> (`path:line`)
**Verification:** <rerun.py summary block>
**Follow-ups:** <sibling tests with the same pattern (search for it), product bug ticket, quarantine review date>
```

## Guardrails

- Never ship a sleep, a bigger timeout on its own, or a retry as "the fix". If the user insists, label it a mitigation in the report and keep the ticket open.
- Never delete a flaky test, or weaken its assertion until it passes, without explicit user approval. A weaker assertion is a lost test.
- Never quarantine without confirmation, and never without a ticket.
- Keep the repeat runs off shared environments (staging databases, paid third-party APIs, real email/SMS). 100 runs against a live payment sandbox has real cost. Ask first.
- `rerun.py --parallel` runs share the machine. Parallel collisions on ports or files are a valid finding only if CI also runs in parallel.
- Revert temporary repeat annotations, seeds and env overrides before you finish.

## Common mistakes

| Mistake | Fix |
|---|---|
| Rerunning with CI retries still on, so every run "passes" | Pass `--retries=0` / `--retry=0` / `--config retries=0`, and remove `--reruns` and `jest.retryTimes` during the hunt |
| Declaring it fixed after 10 green runs | Use the table in step 6. 10 runs miss a 5% flake 60% of the time |
| Isolating only, so order-dependent flakes never show | Step 3: full suite in CI order, then shuffle with a fixed seed |
| Shuffling without recording the seed | Always pass or print the seed so the failing order can be replayed |
| Fixing the test when the product has the race | If the race can happen in production, fix the product and say so |
| Mocking the clock in one test but leaking it | Restore in teardown (`jest.useRealTimers()`, `vi.useRealTimers()`, fixture finaliser, `t.Cleanup`) |
| Treating "cannot start" or a timeout as a flake | rerun.py separates `error` and `timeout` from `fail`. A hang is its own root cause (deadlock, open handle) |

## Example

**Input:** "`test_invoice_due_date` in `billing/tests/test_invoice.py` fails maybe once a week on CI, never locally."

1. The CI log shows `assert date(2026, 3, 1) == date(2026, 2, 28)`. Every failing run started between 00:00 and 05:00 UTC. CI runs in UTC and the developers are in New York.
2. `python3 scripts/rerun.py --runs 100 -- pytest "billing/tests/test_invoice.py::test_invoice_due_date" -p no:randomly` gives 0/100 locally.
3. Environment: 00:00-05:00 UTC is exactly when the UTC date is a day ahead of the New York date. That points to the time/timezone class.
4. Confirm: the test computes "today" with `date.today()` (host timezone). The code computes it in the business timezone `America/New_York`. With `@freeze_time("2026-03-01 02:00:00")` and `TZ=UTC` the test fails 100/100. With `@freeze_time("2026-03-01 12:00:00")` it passes 100/100.
5. Fix: the test freezes the clock at `2026-03-01T02:00Z` and asserts an explicit expected due date. No sleep, no retry.
6. The trigger is now controlled, so the forced-trigger run plus 300 runs under `TZ=UTC` and `TZ=America/New_York` (`failed: 0`) is sufficient.
