# Review — blast radius & independent review

Read this during Phase 4b. A reviewer that shares your context shares your
blind spots, so the reviewer starts **fresh**: its only inputs are the diff,
the repo, the brief and the blast-radius file you write first. A different
model from yours, if your agent lets you choose one, catches more.

## Step 1 — you write the blast radius

For each changed symbol, contract, config key, event and data shape, find
every caller/consumer:

- In this repo: search for the name and its other spellings (snake/camel/kebab,
  constants, string keys), plus imports and reflection/route registrations
  (e.g. `rg -n 'get_report|getReport|"report_id"'`; Java: `rg -n 'ReportService\b' --type java`
  across all Gradle/Maven modules, not only the one you changed).
- Across repos: the org's code search if available (e.g. `gh search code
  '<symbol>' --owner <org>`). Unavailable → the file's first line says
  `Cross-repo search unavailable: cross-repo impact not checked`.

Write `.devloop/<ID>/blast-radius.md`:

```
| symbol/contract changed | impacted (repo:file:line) | how found (local / cross-repo) | covered by test? |
```

## Step 2 — snapshot, then start the reviewer

**Snapshot the round.** Copy every changed and new file (test and non-test)
into `.devloop/<ID>/review-r<N>/` keeping paths, and save
`git diff <base> --stat` beside it. The final-delta pass diffs against the
last snapshot; without it nobody can tell which code the reviewer never saw.

Write the prompt below to `.devloop/<ID>/review-prompt.md` and hand it to the
reviewer, in order of preference:

1. **A separate non-interactive agent session** started from the worktree,
   with tool permissions limited to reading files, `git status/diff/log`, the
   repo's test commands, and editing files matching the test glob. Save its
   output to `.devloop/<ID>/review.md` and its stderr separately (CLI warnings
   must not land in the review).
2. **A fresh-context subagent** given the same prompt. Its limits are only
   its prompt, so enforce them: before it starts, save `git diff --stat`,
   `git stash list` and a copy of every non-test file you changed; afterwards
   compare. Any difference (edited source, a stash, a checkout) → restore
   from your copy (leave a new stash for the user to handle) and report
   `reviewer broke its limits: <what>`.
3. **Cold re-read**, only if neither is possible: set your working notes
   aside, read only the diff, the brief and this prompt, and answer it
   yourself as if seeing the change for the first time. Report
   `Review: cold re-read — <why no reviewer>`.

Wait for the reviewer to finish before reading its output; never end your turn
or move to Phase 5 while it runs.

**Test glob** examples: Python `tests/**`, `**/test_*.py`; JS/TS
`**/*.{test,spec}.{ts,tsx,js}`, `**/__tests__/**`; Go `**/*_test.go`; Gradle/Maven
`**/src/test/**`, `**/src/testFixtures/**`.

## The prompt (fill the `<…>`; nothing else)

```
Review a local change and test its blast radius. Work only in <worktree path>.
You may create or edit test files only (<test glob>); never edit other files,
never run git commands other than status/diff/log, never commit.

Change: <ID> — <summary>. Base: <base ref>. Diff: `git diff <base>`.
Brief (ACs, Design table, change plan, repo rules): <path to brief.md>
Blast radius (written by the author): <path to blast-radius.md>
Test commands: <from the brief>. Pre-existing failures: <path to baseline.txt>.

1. Review the diff against the brief and the repo's AGENTS.md/CLAUDE.md/
   CONTRIBUTING: correctness vs each AC, edge cases and error paths, the Design
   table actually implemented (no silent extra decisions), security at trust
   boundaries, conventions, dead code. Every finding cites file:line.
2. Check the blast radius, don't trust it. For each changed symbol, contract,
   config key, event and data shape, search for callers/consumers yourself
   (local search; cross-repo search if available). Each one missing from
   blast-radius.md goes under MISSED.
3. Unit-test the blast radius in this repo: run the existing tests of every
   impacted module (not only the ones the author ran). For an impacted path
   whose behaviour the change can alter and no test covers, add a focused unit
   test. Impacted code in other repos: list it, don't test it.
4. A failing test not in baseline.txt: say which change it points at. Don't fix
   non-test code.
5. Answer every CHECKS row. Each answer is a FINDINGS #, or "clear — <what you
   opened or ran>", or "n/a — <why it cannot apply>". "clear" without evidence
   counts as not checked.

Return exactly:
FINDINGS: | # | severity (blocker/major/minor) | file:line | issue | suggested fix |
CHECKS:
| # | check | answer |
| C1 | Real input shape: every test input standing for another component's output (parser, API/DB response, LLM output, file) was produced by that component or copied from its real output — run the real producer on a sample and compare | |
| C2 | Copied strings: every heading, key, marker, enum value or regex that must match text another module emits — open the emitter and compare the exact string, case and suffixes included | |
| C3 | Closed sets: a new category, type, tag or state — including one introduced only in prose, a prompt or a comment — is present in every enum, allowlist, switch, schema, prompt list or map that lists its siblings. Grep an existing sibling's prose name AND its slug, constant and enum forms ("Date range" → `date-range`, `DATE_RANGE`, `DateRange`) | |
| C4 | Stale results: name each cache, frozen plan, fingerprint or persisted artifact the changed code feeds, and its key. A key built only from input data doesn't change when code changes, so old results survive: the key needs a code-version part this diff bumps | |
| C5 | Consumers: for every output whose size, order or shape changed, each consumer was opened and what it does with it (slice, parse, index, sort) still holds | |
| C6 | Tests that can fail: each new assertion fails when the code is wrong. A test that builds N items asserts all N; no default makes it trivially true; it doesn't assert a mock's own return; the input puts the triggering data where real input puts it | |
| C7 | Prose vs code: comments, docstrings and the brief describe what the code actually does | |
| C8 | One value, one path: logic another module or sibling function also computes resolves it the same way | |
| C9 | Fail loudly: no default that hides a missing argument, no empty catch, no fail-open path without a log | |
| C10 | Out-of-diff wiring: every env var, secret, flag or config value the change needs is set in each environment it ships to | |
| C11 | Evidence kind: an AC that depends on LLM output or a live service is marked "needs live run" unless a real run was done | |
| C12 | Copies: every block, string, schema, fixture or predicate appearing twice or more in the diff (grep added lines for each literal and each 3+ line block). Two copies with different wording are a finding, and so is a new copy of an idiom the file already repeats | |
| C13 | Meaning changes: an existing field, param, return value or count whose meaning changes while its type does not. Name its readers (in this repo and returned to clients) and what each assumes; prefer a new field | |
| C14 | Repo rules: every row of the brief's Repo rules, plus any imperative line in AGENTS.md/CLAUDE.md/CONTRIBUTING the diff touches — met / not met with file:line. "The neighbouring code does it too" is not met | |
| C15 | Doc placement and casts: every doc comment the diff touches sits directly above its declaration; no new `as any` / `as unknown as` / `type: ignore` / `@SuppressWarnings` / `//nolint` without a comment saying why | |
MISSED: | symbol/contract changed | impacted (repo:file:line) | how found | covered by test? |   ("none" if blast-radius.md was complete)
TESTS RUN: <commands + pass/fail counts copied from output>
TESTS ADDED: <file — what each asserts>
NOT CHECKED: <anything skipped and why>
```

## Acting on the result

- **Malformed output** (empty, or missing FINDINGS/CHECKS) → the reviewer
  failed; rerun once, then drop to the next option in Step 2.
- **A CHECKS row blank, or "clear" with no evidence** → one more reviewer run
  whose prompt is the same header plus only those rows; still unanswered →
  NOT CHECKED in the report. (This is a gap-fill, not a re-review.)
- **MISSED not "none"** → add those rows to `blast-radius.md` and report
  `Blast radius: author missed <n>`.
- **The reviewer's tests are not trusted either.** For each test file it added
  or changed, answer C6 yourself and run the revert proof ([testing.md](testing.md) §2)
  before keeping it. A test that passes with the change reverted is rewritten or deleted.
- **Verify before fixing.** Read each blocker/major at its file:line; a finding
  you can't reproduce or that contradicts the brief → rejected, with why.
  Minor → report, don't fix.
- **Fix** confirmed blockers/majors (run budget applies), then redo Phase 4's
  Final run including the reviewer's new tests.
- **A blast-radius test failing** that isn't in `baseline.txt`: classify it
  with the revert proof in [testing.md](testing.md) §2 — fails with your change
  reverted → pre-existing (report); passes reverted → yours (fix).
- **Re-review** only if fixes changed non-test code: one more round, same
  reviewer kind, the **whole** prompt with every CHECKS row. Never narrow a
  re-review to a few rows — fixes are new code. Two rounds max; anything still
  open goes in the report.
- Cross-repo impact → "Prerequisites not done here", with the owning team if known.

## Final-delta pass (after the last round)

Whatever changed after the last snapshot was reviewed by nobody. Before the report:

1. Diff it: `git diff --no-index .devloop/<ID>/review-r<last>/<path> <path>`
   for each existing file, plus every file created since. Save to
   `.devloop/<ID>/final-delta.diff`. Empty → record "final-delta: none" and stop here.
2. Put that delta through the self-review checklist in [testing.md](testing.md) §3 and answer every CHECKS
   row against it yourself, with evidence, in `.devloop/<ID>/final-delta.md`.
3. Run the revert proof for every test the delta adds or changes.
4. A finding → fix it and repeat 1–3, within the run budget. This never starts a third reviewer round.
5. Report: `final-delta: <n files>, <findings fixed / open>`.
