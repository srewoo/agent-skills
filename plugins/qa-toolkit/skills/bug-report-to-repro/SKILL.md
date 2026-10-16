---
name: bug-report-to-repro
description: Use when someone hands over a vague bug report (a ticket, Slack or email message, customer complaint, screenshot description, stack trace or log snippet) and needs it turned into reliable reproduction steps or a failing test. Triggers include "reproduce this bug", "can you repro", "write a failing test for this issue", "steps to reproduce", "cannot reproduce", "when did this break", or "triage this ticket into a repro".
---

# Bug Report to Repro

## Overview

A bug report is a mix of facts, guesses and noise. Separate the facts, get the missing critical ones in a single question, reproduce the symptom deterministically, shrink it to the fewest steps, and capture it as an automated test at the lowest layer that still shows the symptom. That test must fail for the reported reason. This skill stops at a proven failing test and a repro report. It does not fix the bug unless the user asks.

## When to use / When not to use

- Use for a report of wrong behaviour that has no reliable repro yet.
- Use for "this used to work", to find the breaking commit with `git bisect`.
- Not for a test that already exists and fails only sometimes. Use `flaky-test-hunter`.
- Not for finding untested code in a diff. Use `test-gap-finder`.
- Not for production incidents still in progress. Mitigate first, reproduce afterwards.

## Inputs

| Input | Default if not given |
|---|---|
| The report (text, log, screenshot description, ticket link content) | Required. Ask for it if missing. |
| Repository access | Assume the current repo. If there is none, produce the report with manual steps and mark the test as `not written: no code access`. |
| Version/commit where it was seen | Production's deployed tag if known, otherwise `HEAD` of the default branch. Record which you used. |
| Last known good version | None. Bisect only if the user or the history supplies one. |
| Environment (OS, browser, locale, tenant config, feature flags, data shape) | Use the repo's default local setup and mark each value as an **assumption**. |

Ask the user **once**, in one message, and only for facts that block reproduction and cannot be found in the repo, logs or report. Typical blockers are the exact input or payload, the account role or plan, the feature flag state, and the version. Give a default you will use if they don't answer, and keep working with that default.

## Workflow

### 1. Extract facts, assumptions and unknowns

Read the whole report, including attachments and thread replies. Sort every claim into one of these three lists:

- **Facts**: directly observed and quoted, such as an error text, status code, timestamp, request id, version string, or stack frame.
- **Assumptions**: the reporter's guesses ("probably after the upgrade", "seems random") and anything you infer.
- **Unknowns**: anything needed to reproduce that nobody stated.

Restate the **symptom** in one testable sentence: `When <action> with <input> as <role>, <observed> instead of <expected>`.
**Done when** the symptom sentence uses only facts, and every assumption is labelled as one.

### 2. Gather evidence from the codebase and logs

- Search the codebase for the exact error string, log message, status code or UI label in the report. This usually finds the code path within minutes.
- Map the stack trace frames to files and lines **at the reported version** (`git show <tag>:path/to/file`), not at `HEAD`.
- If there is a request id or timestamp and log access, pull the surrounding log lines for the request.
- Check `git log --since=<a week before first report> -- <suspected paths>` for recent changes.

**Done when** you have a short list of suspect code paths (file:function) with the reason each one is on it.

### 3. Build the environment matrix

List only the dimensions that could plausibly change the outcome: version, OS/browser, locale/timezone, role/permissions, feature flags, data shape (empty, huge, unicode, null field), and concurrency (single user or simultaneous). Mark each value as reported, assumed or untested. Start reproducing with the reported values, then vary one dimension at a time.
**Done when** the matrix is written down and you know which cell you will try first.

### 4. Reproduce manually, as cheaply as possible

Try the cheapest entry point that reaches the suspect code:

1. A unit-level call in a REPL or scratch test (`node -e`, `python -c`, `go test -run`, a JShell snippet).
2. A direct API call: `curl -sS -X POST localhost:8080/api/orders -H 'content-type: application/json' -d @payload.json`.
3. The UI, only if the symptom lives in the UI. For "on mobile" reports, emulate the device first (`npx playwright open --device="iPhone 13" <url>`, or browser devtools device mode) and vary viewport, touch input, orientation and the WebKit engine (iOS browsers all use WebKit), since each is a separate matrix dimension.

Run it 3 times. If it reproduces every time, it is deterministic. If it reproduces only some of the time, record the rate and which variable you suspect (timing, data, concurrency). An intermittent repro still counts. Pin the variable before you move on.
If it does not reproduce after working through the matrix, stop and report `cannot reproduce`. List what you tried, cell by cell, and the single most useful piece of missing information.
**Done when** the symptom appears on demand, or the cannot-reproduce report is ready.

### 5. Bisect if it is a regression

Bisect only with a known good version and a scripted check that runs in under a few minutes:

```sh
git bisect start <bad-sha> <good-sha>
git bisect run sh -c '<build step> || exit 125; <repro command>'
# exit 0 = good, 1-124/126/127 = bad, 125 = skip this commit (e.g. it doesn't build)
git bisect log > bisect.log
git bisect reset
```

The repro command must exit non-zero **only** for the reported symptom. If it fails for an unrelated reason, the bisect blames the wrong commit. Use a scratch test file that is not tracked, or one outside the repo, so checkouts don't remove it. In a monorepo, add `-- <path>` to `git bisect start` so it only considers commits that touch the suspect package.
**Done when** you have the first bad commit, and you have confirmed it by checking out its parent (passes) and the commit itself (fails).

### 6. Minimise

Remove one step, field, record or config value at a time. Keep the removal if the symptom still appears. Shrink inputs as well: the smallest payload, one row instead of 10,000, and the shortest string that still triggers it.
**Done when** removing any remaining step or field makes the symptom disappear.

### 7. Write the failing test at the lowest feasible layer

Choose the layer in this order, and stop at the first one that can show the symptom:

| Layer | Use when the defect is in | Typical location |
|---|---|---|
| Unit | Pure logic, parsing, calculation, a single class/function | Next to the existing unit tests for that module |
| Integration | DB queries, ORM mapping, transactions, message handling, cache | The repo's integration suite (Testcontainers, test DB fixtures) |
| API/contract | Status codes, serialisation, auth middleware, validation across a request | API test suite (supertest, `httpx`/`TestClient`, `httptest`, MockMvc/RestAssured) |
| End-to-end | Rendering, browser behaviour, multi-service flows that only fail together | Playwright/Cypress suite |

Follow the repo's existing test conventions: framework, file naming, fixtures and factories. If the layer you need has no infrastructure in the repo (for example only Jest + jsdom, but the bug depends on real layout, CSS, scrolling or touch), first try the logic-level test the layer below allows (Testing Library with a mocked `matchMedia`/`innerWidth`); jsdom does no layout, so it cannot show visual bugs. If that cannot show the symptom, ask before adding a new test framework or dependency, and meanwhile deliver the repro as an untracked one-off script with the test marked `not written: no <layer> infrastructure`. Name the test after the behaviour and the ticket, for example `test_discount_not_applied_twice_when_cart_refreshed_BUG_482`. If the project tags known failures, mark it expected-to-fail so CI stays green until the fix (`it.failing`, `test.fails`, `@pytest.mark.xfail(strict=True, reason="BUG-482")`, `test.fail()`). Without such a convention, leave it failing and tell the user.

**Done when** the test is saved in the working tree. Do not commit or push it.

### 8. Prove it fails for the right reason

Run only the new test (`npx jest path -t "BUG-482"`, `npx vitest run path -t "BUG-482"`, `pytest path::test_name`, `go test -run '^TestBug482$' ./pkg/x`, `./gradlew test --tests '*Bug482*'`, `mvn test -Dtest='OrderTest#bug482'`, `npx playwright test -g "BUG-482" --retries=0`).

Check all of the following:

- It **fails**, and the failure message shows the reported symptom (the wrong value, status or error), not a setup error, import error, timeout or missing fixture.
- The assertion targets the **reported symptom** (`expect(total).toBe(90)` where the user saw 80), not an implementation detail.
- It is deterministic: run it 5 times and confirm 5/5 failures with the same message.
- If you found the bad commit, the test passes on the parent of that commit, when that is practical.

**Done when** all checks hold. Paste the failure output into the report.

## Output

```markdown
## Repro: <one-line symptom>

**Status:** reproduced (deterministic) | reproduced (intermittent, n/N) | cannot reproduce
**Environment:** <version/commit>, <OS/browser>, <locale/TZ>, <role>, <flags>. Assumptions are marked (A)
**Preconditions:** <data/setup needed, minimal>

**Steps:**
1. ...
2. ...

**Expected:** <what should happen, and the source: spec, docs, previous behaviour>
**Actual:** <what happens, quoted exactly>
**Evidence:** <error text, log lines with request id, screenshot reference, bisect result>

**Failing test:** `<path>::<test name>` (layer: unit|integration|API|e2e)
Command: `<exact command>`. Result: fails 5/5 with `<assertion message>`

**Regression:** first bad commit `<sha>` "<subject>" (verified against its parent) | not a regression | not bisected (<reason>)
**Suspected area:** `<file:function>`, because <one line of reasoning>. This is a lead, not a diagnosis.

**Facts / Assumptions / Unknowns:**
- F: ...
- A: ...
- U: ... (asked reporter on <date> | not blocking)
```

## Guardrails

- Never fix the bug in this skill unless the user asks. A fix in the same change hides whether the test actually caught the bug.
- Never run reproduction steps against production or shared environments, or with real customer data or accounts, without explicit permission. Copy and anonymise any data you need. Never paste secrets, tokens or personal data from logs into the report.
- Never weaken or delete existing tests to make room for the repro.
- Don't push, open PRs or comment on the ticket without confirmation. Produce the report text for the user to post.
- `git bisect` checks out old commits. Start from a clean working tree (`git stash -u` first, with the user's consent) and always finish with `git bisect reset`.
- Ask clarifying questions only once and in one message. After that, proceed on labelled assumptions.

## Common mistakes

| Mistake | Fix |
|---|---|
| Treating the reporter's theory ("it's the cache") as a fact | Put it under Assumptions and test it like any other hypothesis |
| Jumping straight to an e2e test | Climb the layer table from the bottom. Most bugs reproduce at unit or API level faster and more stably |
| The test fails on a `TypeError` in setup, which looks like a repro | Read the failure message. It must show the reported symptom |
| Asserting on internals (a mock was called) instead of the outcome the user saw | Assert on the observable value, status or output from the report |
| A bisect script that fails on unrelated build breaks | `exit 125` for commits that don't build, and verify the result on the parent commit |
| Mapping stack frames against `HEAD` | Read the code at the reported version |
| Asking five rounds of questions | One message with defaults, then proceed |

## Example

**Report (Slack):** "Checkout total is wrong for some EU customers since last week, screenshot shows €80 instead of €90. Maybe the new tax thing?"

1. Facts: the total was €80 and the expected total was €90. The currency is EUR. It started "last week". Assumptions: it affects "some EU customers", and "the new tax thing" is the cause. Unknowns: country, cart contents, coupon.
2. Ask once: "Which country and cart (or an order id)? Until I hear back I'll assume DE, a single item, no coupon." The reply is "order 5512, AT, coupon WELCOME10".
3. Searching for `WELCOME10` leads to `pricing/discount.py`. `git log --since=2026-10-01 -- pricing/` shows that commit `a1b2c3d` reordered discount and VAT.
4. API repro: `curl` with the minimised cart (one item, AT, WELCOME10) returns `80.00` on 3 out of 3 runs.
5. Bisect between `v2.14.0` (good) and `HEAD` with that curl inside a script points to `a1b2c3d`. Its parent returns `90.00`.
6. Unit test `test_coupon_applied_after_vat_BUG_771` in `pricing/tests/test_discount.py` asserts `total == Decimal("90.00")`. It fails 5/5 with `Decimal('80.00') != Decimal('90.00')`.
7. Report delivered. Suspected area: `apply_discounts()` now runs before `add_vat()`. Not fixed, as requested.
