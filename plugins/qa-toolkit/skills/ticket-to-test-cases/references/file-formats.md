# File formats

All files are JSON unless noted. Paths are examples. Keep one run directory per ticket, such as `.test-cases/PROJ-123/`.

## ticket.json (you write it)

Build it from any tracker (Jira, Linear, GitHub/GitLab issues, Azure Boards, Shortcut) or from pasted text. Only `summary` and either `acceptanceCriteria` or `description` are required.

```json
{
  "key": "PROJ-123",
  "summary": "Users can sign in with email and password",
  "issueType": "Story",
  "description": "Plain text. Flatten rich text, but keep list items and 'Case N:' lines on their own lines.",
  "acceptanceCriteria": "One criterion per line. Keep Given/When/Then on consecutive lines.",
  "comments": [{"author": "pm", "text": "Lockout applies to SSO users too"}],
  "links": [{"type": "blocks", "key": "PROJ-99", "summary": "Session timeout"}],
  "documents": [{"title": "Auth spec (Confluence)", "text": "extracted text"}]
}
```

If the tracker has no acceptance-criteria field, put the "Acceptance criteria" section of the description in `acceptanceCriteria`. If there is none, leave it empty, and `init` derives requirements from description lines that make claims ("should", "must", "can", "cannot").

Comments and linked documents often settle ambiguities. Fold decisions from them into `acceptanceCriteria` as extra lines, and say in the report that you did.

## page.json (from the page extractor)

The object returned by [page-extractor.js](page-extractor.js):

```json
{"url": "https://app.example.com/login", "title": "Sign in",
 "features": [{"type": "form", "name": "login", "submitText": "Sign In",
               "fields": [{"name": "email", "label": "Email", "type": "email", "required": true},
                          {"name": "role", "label": "Role", "type": "select", "options": ["Admin", "Viewer"]}]},
              {"type": "button", "text": "Forgot password"},
              {"type": "link", "text": "Dashboard", "href": "https://app.example.com/dashboard"}],
 "links": ["https://app.example.com/dashboard"]}
```

A page is stored under its `url`. Pass `kg-add --url <url>#<state>` to keep several states of one URL (wizard steps, tabs, dialogs) as separate pages.

## requests file (optional, for `kg-add --requests`)

Any of these:

- a browser tool's request log, one request per line, containing a method and URL: `[POST] https://app.example.com/api/auth/login => [401]` or `POST https://app.example.com/api/auth/login 401`;
- a HAR export (DevTools → Network → right-click → *Save all as HAR*);
- a JSON array of `{"method", "url"}`.

Static assets (`.js`, `.css`, images, fonts) are dropped. Other origins are dropped unless `--all-origins` is passed. Numeric and UUID path segments become `:id`.

## issues.json (optional, for `history`)

Past defects in the same area, from any tracker: `[{"key": "PROJ-77", "summary": "Lockout counter not reset after password reset"}]`.

## verdicts.json (optional, for `finalize --verdicts`)

Your judgement of each accepted test's expected result against the ticket:

```json
{"verdicts": [{"id": "T-03", "verdict": "contradictory", "issue": "ticket says lock after 5, test says never lock"}]}
```

`verdict` is one of `supported`, `contradictory`, `unverifiable` or `unknown`. Prefer `unknown` to guessing. `--strict` drops `contradictory` tests and recomputes coverage without them.

## Outputs of finalize

- `test-cases.json`: `testCases[]` (id, title, category, priority, preconditions, steps, expected_result, test_data, requirementIds, `_grounding`, `_refs`, `_repairs`, `_warnings`, `_assertion`), plus `coverage`, `requirements`, `stopReason`, `rejectedByStage`, `caveats`, `clarifications`.
- `test-cases.md`: a summary table, caveats, questions for the product owner, then every test.

`_grounding` is `verified` (every reference exists in the crawl), `specification` (it references only things the ticket introduces), or `unverified` (no crawl was available).
