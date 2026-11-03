# Authoring rules

The gate reads candidate tests literally. Write them so it can see what they touch.

## Candidate shape

A batch is a JSON array. One object per test:

```json
{
  "title": "A wrong password shows an error message",
  "category": "Negative",
  "priority": "P1",
  "requirementIds": ["R02"],
  "preconditions": "A registered user on https://app.example.com/login",
  "steps": ["Type a registered address in the email field",
            "Type a wrong password in the \"Password\" field",
            "Click \"Sign In\""],
  "expected_result": "An error message is shown and POST /api/auth/login returns 401",
  "test_data": "user@example.com / wrong-password"
}
```

- `category`: one of `Positive`, `Negative`, `Edge`, `Regression`, `Integration`, `Security`, `Accessibility`.
- `priority`: `P0` (blocks release) to `P3` (cosmetic). Default `P2`.
- `requirementIds`: the `R..` ids from `init` that this test covers. Always declare them. A declared id lowers the word overlap the coverage check needs (from half the criterion's words, including a third of its distinctive ones, to a quarter). It never makes an unrelated test count. A test whose polarity is the opposite of a criterion it declares is rejected at `propose`.
- `Regression` tests also need either a `historicalReference` or a `rationale` naming the adjacent behaviour they protect. A `historicalReference` must be an issue key stored with `history`.
- `test_data` is a plain string.

## Naming what the test touches

The grounding check finds references with these patterns. Anything else is invisible to it.

| Entity | Write it as |
|---|---|
| Control (button, link, tab, menu item) | `Click "Sign In"` · `the "Export" button` · `the "Billing" tab` |
| Field (input, dropdown, checkbox, textarea) | `the email field` · `the "Card number" field` · `the "Role" dropdown` · `the "Terms" checkbox` |
| Dropdown option | `Select "Editor" in the "Role" dropdown`. It is checked against that dropdown's options when the crawl recorded them |
| API call | `POST /api/auth/login` (method in capitals, path starting with `/`) |
| Page | a full URL on the app's host: `https://app.example.com/settings/billing` |

- Use double quotes for labels. Single quotes are not read as labels.
- Copy labels from `groundingContext` or `search`. A near-miss (`"Sign-in"` for `Sign In`) is rewritten to the app's label and reported as a repair.
- A control the app doesn't have yet is allowed only when the ticket names it word for word. The test is then marked `specification`.
- The steps or expected result must name at least one entity. A test whose only concrete reference is in its preconditions is rejected as too vague.

## Polarity

Polarity says whether the behaviour is permitted or prevented. It is not about the state the behaviour produces.

- `the Save button is disabled`, `the sidebar is hidden` and `an error is shown` are **positive** assertions of a required state. They agree with "hide the sidebar".
- A criterion that forbids something ("viewers cannot invite") is met either by a negation ("the viewer cannot invite") or by a prevented state ("the Bulk invite button is disabled", "the upload is rejected", "access is denied").
- A prevented state contradicts a criterion that requires the action ("admins can invite", tested with "the Send invites button is disabled"). The exception is a criterion that itself asks for that state ("hide the sidebar", "the upload is rejected").
- "An error message is shown" on its own neither covers nor contradicts a "cannot" criterion. Say what is prevented.
- Use `cannot`, `must not`, `never`, `is denied` or `is blocked from` only when the criterion itself forbids the action.
- Declared criterion, opposite polarity: rejected at `propose`.
- Undeclared, but clearly about the criterion (it shares three quarters of the criterion's words) with the opposite polarity: accepted with a `contradicts R..` warning, and reported as a **contradiction** by `coverage`. The loop won't stop on coverage while a contradiction is open. If a budget ends the loop first, the contradiction is reported as a caveat.

## Content

- Each step is one concrete action. The expected result is one observable outcome. "Verify it works" is not an outcome.
- Don't invent error strings, status codes, limits or timings the ticket doesn't state. Write "an error message is shown", not `"Invalid credentials (E401)"`. A status code or quoted text the ticket doesn't contain comes back as a `warning` and is listed as a caveat.
- Each candidate exercises a distinct behaviour, field or boundary. Rewording an accepted test is rejected as a duplicate. Tests are never duplicates when they differ in polarity, a number (3 rows vs 500 rows), a persona (admin vs viewer) or a UI state (enabled vs disabled). So put the distinguishing value in the title or expected result.
- Scenario labels (`Case 1: …`) and implementation notes (`use the relay client`, `props -> state`) in `requirements` are context, not criteria, and need no test.
- Boundaries: test both sides of every stated limit. "Max 100 characters" means 100 is accepted and 101 is rejected.
