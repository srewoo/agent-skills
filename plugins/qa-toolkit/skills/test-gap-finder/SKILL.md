---
name: test-gap-finder
description: Use when reviewing a diff, branch, pull/merge request or commit range and the question is what changed behaviour has no test. Triggers include "what's untested in this PR", "missing tests", "test gaps", "diff coverage", "is this change covered", "coverage on changed lines", "what tests should I add before merging", or a reviewer asking "where are the tests?"
---

# Test Gap Finder

## Overview

Find the behaviour a change introduces or alters that no test exercises, rank those gaps by the damage an escaped bug would do, and propose the exact test for each one. Diff coverage (which changed lines ran during tests) is the starting signal. It is not the answer, because a line can run with nothing asserting its result, and an untested error path or boundary can sit on a line marked as covered.

## When to use / When not to use

- Use before merging a branch or PR, when reviewing someone else's PR, or after a quick fix to check it is guarded.
- Not for measuring whether existing tests would **catch** a bug. That is mutation testing (Stryker, mutmut, PIT, go-mutesting), which you can suggest as a follow-up for the top gaps.
- Not for whole-repo coverage targets. This skill is scoped to the diff.
- Not for reproducing a reported bug. Use `bug-report-to-repro`. Not for intermittent failures. Use `flaky-test-hunter`.

## Inputs

| Input | Default if not given |
|---|---|
| Change to analyse | Current branch vs the default branch (`origin/HEAD`, else `origin/main`, else `origin/master`). A PR number/URL means its head vs its base branch. |
| Coverage tooling | Detect from config: `jest.config.*`/`vitest.config.*`, `pyproject.toml`/`.coveragerc`, `go.mod`, `jacoco` in `build.gradle(.kts)`/`pom.xml`. |
| Can tests be run? | Yes, locally. If they can't (no DB, too slow), do a static-only analysis and label every row `static`. |
| Diff-coverage threshold | 80% of changed executable lines, as a reference point only. Gaps are judged by risk, not by the percentage. |

## Workflow

### 1. Pin the diff

```sh
git fetch origin
BASE=$(git merge-base origin/main HEAD)        # use the PR's base branch
git diff --stat "$BASE"                         # size check
git diff --name-status -M "$BASE"               # added/modified/renamed/deleted
git diff -U0 "$BASE" -- . ':(exclude)*.lock'    # hunks; the @@ header names the enclosing function
```

Diffing against `$BASE`, not `origin/main`, keeps changes that landed on main after you branched out of the result. `git diff "$BASE"` includes uncommitted work. Use `git diff "$BASE" HEAD` for committed changes only. diff-cover also includes staged and unstaged changes by default. Add `--ignore-staged --ignore-unstaged` for committed changes only.
Classify each changed file as production code, test, config/flags, migration/schema, public API contract (OpenAPI, protobuf, GraphQL schema, exported types), or generated/vendored/lockfiles. Ignore the last group.
**Done when** you have a list of changed production files and hunks, and the diff exceeds neither 2,000 changed lines nor 50 files. If it does, tell the user and analyse the riskiest directories first.

### 2. Map changed behaviour

For each production hunk, read the whole enclosing function (`git diff -W "$BASE" -- <file>` shows full function context) and list the **behaviours** it adds or alters:

- New or changed branches (`if`/`switch`/`match`/ternary/guard clauses/early returns)
- Error paths: `throw`/`raise`/`return err`, `catch`/`except`, retries, fallbacks, timeouts
- Retries specifically: max attempts, which errors retry and which must not (4xx, validation, declined payment), backoff bounds, the idempotency key reused across attempts, and the state after the final failure. Test them with a fake server that fails N times (`httptest.NewServer`, WireMock, `responses`) and an injected clock or backoff, never real sleeps
- Boundaries: comparisons (`<` vs `<=`), limits, pagination, empty/null/zero/negative/max-length inputs, rounding and currency
- New config keys, env vars and feature flags: both the on and off states, and what happens when the key is missing
- Migrations: forward, rollback if one exists, behaviour on existing rows (nulls, defaults, backfill), locking on large tables
- Public contract: new or removed fields, changed status codes, renamed exports, changed defaults, and backward compatibility for existing clients
- Concurrency and side effects: new writes, events/messages emitted, cache invalidation, idempotency

Find the tests for each one. Search the test directories for the function, class, route, flag or error message name, and read the matching tests to see whether they assert on the behaviour, not just call the code.
**Done when** every changed behaviour has a row marked `tested`, `partially tested`, or `untested`, with the test file named where one exists.

### 3. Measure diff coverage

Run the tests with coverage, then intersect with the diff. [diff-cover](https://github.com/Bachmann1234/diff_cover) (`pip install diff-cover`) reads Cobertura, Clover, JaCoCo XML and `lcov.info`, and reports coverage for changed lines only.

| Stack | Coverage command | Diff coverage |
|---|---|---|
| Jest | `npx jest --coverage --coverageReporters=lcov --coverageReporters=text-summary` (add `--changedSince="$BASE"` to run only related tests, which is faster but can under-count) | `diff-cover coverage/lcov.info --compare-branch="$BASE" --show-uncovered` |
| Vitest | `npx vitest run --coverage.enabled --coverage.reporter=lcov --coverage.reporter=text-summary` (needs `@vitest/coverage-v8` or `@vitest/coverage-istanbul`) | same as Jest |
| pytest | `pytest --cov=<package> --cov-branch --cov-report=xml --cov-report=term-missing` | `diff-cover coverage.xml --compare-branch="$BASE" --show-uncovered --format markdown:diff-cover.md` (diff-cover < 9.3: `--markdown-report diff-cover.md`, deprecated from 9.3) |
| Go | `go test -covermode=atomic -coverpkg=./... -coverprofile=cover.out ./...` | Convert, then diff: `go run github.com/boumenot/gocover-cobertura@latest < cover.out > coverage.xml && diff-cover coverage.xml --compare-branch="$BASE"` |
| Gradle + JaCoCo | `./gradlew test jacocoTestReport` (enable `reports { xml.required = true }`). XML lands in `build/reports/jacoco/test/jacocoTestReport.xml` | `diff-cover build/reports/jacoco/test/jacocoTestReport.xml --compare-branch="$BASE" --src-roots src/main/java src/main/kotlin`. In multi-module builds, list each module's roots, such as `billing/src/main/kotlin` |
| Maven + JaCoCo | `mvn verify` with the `jacoco-maven-plugin` `prepare-agent` + `report` goals, which produce `target/site/jacoco/jacoco.xml` | `diff-cover target/site/jacoco/jacoco.xml --compare-branch="$BASE" --src-roots src/main/java` |

Notes:
- In monorepos, run coverage per affected package (`pnpm --filter <pkg> test -- --coverage`, `nx affected -t test`, `./gradlew :module:test`) and pass every report to diff-cover in one call: `diff-cover a/lcov.info b/lcov.info --compare-branch=…`. Paths inside the reports must resolve relative to the repo root. Check the first few lines of the output for "No lines with coverage information".
- Line coverage misses untaken branches. A one-line `if (a < 0) return 0` counts as a covered line even when the `return` never runs. Read `term-missing` partial branches in coverage.py (`12->15`) and the `BRDA` lines in `lcov.info`, or the branch column in the HTML report, for each changed function.
- If the tests can't run, skip this step and label the analysis `static`.

**Done when** you have diff-coverage % and the list of uncovered changed lines, or a recorded reason for skipping.

### 4. Look beyond line coverage

For each behaviour marked `tested` in step 2, check whether a test actually **asserts** on it:

- The line ran but no assertion checks its output. This is common with snapshot-only tests, `expect(fn).not.toThrow()`, and mocks that return before the new logic.
- The happy path is covered and the new error path is not, or is reached only through a mock that hides the real exception type.
- Boundaries: is the exact edge (limit, limit±1, zero, empty) asserted?
- Flags: is the off state tested, or only the new on state?
- Migrations: is there a test against a schema with existing data, or only against an empty one?
- Contract: is there a test that would fail if a field were renamed or a status code changed? Examples are a schema/contract test, a typed client test, or Pact.

Downgrade a row to `partially tested` if the behaviour runs but isn't asserted.
**Done when** every row has a final status with a one-line justification.

### 5. Rank by risk

Score each `untested` or `partially tested` row by the worst plausible outcome if it breaks in production:

| Risk | Examples | Rank first |
|---|---|---|
| **Critical** | Data loss or corruption, money (charges, refunds, balances, rounding), authentication/authorisation bypass, secrets or PII exposure, injection, irreversible migrations | Always list. Propose tests for all of them |
| **High** | Public API/contract breaks for existing clients, failure in a hot path with no fallback, silent wrong results, flag-off path breaking existing users | List and propose |
| **Medium** | Error handling that degrades UX but recovers, admin/internal-only paths, logging/metrics correctness | List |
| **Low** | Pure refactors with an unchanged contract that is already covered, copy text, dead code | Mention as a count only |

Within a level, put higher change size and lower existing coverage first.
**Done when** the table is sorted and Critical/High rows each have a concrete test proposal.

### 6. Report, then offer to write the top tests

Produce the output below. Then offer to write tests for the top 3-5 Critical/High gaps, following the repo's test conventions. Only write them after the user confirms. If you do write them, run them and show that they pass. For any test that should catch a bug, show that it fails when the guarded line is deliberately broken, then revert the break.

## Output

```markdown
## Test gaps: <branch> vs <base> (<merge-base short sha>)

**Scope:** N production files, +A/-D lines. Analysis: measured | static
**Diff coverage:** 64% of changed lines (diff-cover, <report path>). Reference threshold 80%
**Verdict:** <1 sentence: e.g. "2 critical gaps: refund rounding and the new admin-only route have no tests">

| # | Location | Changed behaviour | Status | Risk | Suggested test | Layer |
|---|---|---|---|---|---|---|
| 1 | `billing/refund.py:88` | Partial refund now rounds half-even | untested | Critical | `test_partial_refund_rounds_half_even`: 10.125 → 10.12; 10.135 → 10.14; full refund → original amount | unit |
| 2 | `api/routes/admin.ts:41` | New `DELETE /admin/users/:id` requires `role=admin` | untested | Critical | Non-admin token → 403; admin → 204; unknown id → 404 | API |
| 3 | `db/migrations/0042_add_status.sql` | `status` NOT NULL with default on existing rows | partially tested | High | Migrate a fixture DB that has rows; assert `status='active'`; run rollback | integration |
| … | | | | | | |

**Low-risk gaps:** 4 (refactors with unchanged contract), not listed.
**Not analysed:** <generated files, vendored code, anything skipped and why>
**Follow-up:** run mutation testing on <files> to check assertion strength (e.g. `npx stryker run --mutate <file>`, mutmut with `paths_to_mutate` set under `[tool.mutmut]` then `mutmut run`, PIT `pitest` with `targetClasses`).

Want me to write tests 1-3?
```

## Guardrails

- Read-only by default. Don't write, change or delete tests or production code until the user confirms which gaps to address.
- Never "fix" a gap by lowering coverage thresholds, adding coverage-ignore pragmas (`/* istanbul ignore */`, `/* v8 ignore */`, `# pragma: no cover`) or excluding files in the coverage config or deleting the code path.
- Never run the suite against shared or production databases or services to get coverage. Use the project's local or test configuration. Ask if the only option touches shared infrastructure.
- Don't install coverage tools globally or change the project's dependencies without asking. `pip install diff-cover` into a virtualenv, `npx`/`pipx` one-off runs, or `go run …@version` are fine.
- A high diff-coverage % is not evidence of good tests. Never report "fully tested" on coverage alone.

## Common mistakes

| Mistake | Fix |
|---|---|
| Diffing against `origin/main` directly, so other people's changes show up | Diff against `git merge-base origin/main HEAD` |
| Treating covered lines as tested behaviour | Step 4: check that an assertion depends on the changed line |
| Reporting only line gaps, so new branches, error paths and flag-off states are missed | Step 2 maps behaviours first; coverage only supports it |
| diff-cover reports "No lines with coverage information" | The report paths don't match repo paths. Run from the repo root, use `--src-roots` for JaCoCo, or fix `<source>` in the Cobertura XML |
| Running `--changedSince` only, and missing tests elsewhere that cover the change | Use the full suite for the final numbers |
| A 40-row table with equal weight | Rank by risk and list Low as a count |
| Calling mutation testing and coverage the same thing | Coverage = executed. Mutation = asserted. Recommend mutation runs for the top-risk files only |

## Example

**Input:** "What's untested in my branch `feat/partial-refunds`?" (Python/Django, pytest)

1. `BASE=$(git merge-base origin/main HEAD)`. The diff has 6 production files, +214/-31 lines, and one migration.
2. Behaviours: partial-refund amount calculation, a new `InsufficientBalance` error, `REFUNDS_V2` flag gating, migration `0042` adding `refund.status`, and a serializer field `refunded_amount` added to the public API.
3. `pytest --cov=billing --cov-branch --cov-report=xml` then `diff-cover coverage.xml --compare-branch="$BASE" --show-uncovered` gives 71%. Uncovered: `refund.py:88-95` (rounding), `refund.py:120` (`InsufficientBalance`).
4. `test_refund_flow` covers `refund.py:60-80` but asserts only `status_code == 200`, so the amount calculation is `partially tested`. The `REFUNDS_V2=False` path is untested.
5. Ranked: rounding (Critical, money), `InsufficientBalance` (Critical, money), flag-off path (High), migration on existing rows (High), serializer field (High, contract).
6. Table delivered, with an offer to write the two Critical unit tests and the migration integration test.
