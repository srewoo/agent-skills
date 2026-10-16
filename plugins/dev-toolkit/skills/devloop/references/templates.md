# devloop templates

Fill these exactly; leave no section out. Write `none` rather than deleting a heading.

## Brief (`.devloop/<ID>/brief.md`, written in Phase 2)

```
# <ID> — <summary>
Fetched: <ISO time>   Ticket updated: <updated | pasted>   Phase done: 2
## Acceptance criteria   (verbatim or tight paraphrase, each with its source: description / comment by X on <date> / doc; `derived` if inferred)
## Review constraints    (what the review adds or overrides, with source)
## Conflicts             (plan says A, review says B, with dates and sources)
## Repo rules            (quoted, file:line)
## Code map              (file:line for each place that changes + the pattern copied)
## Design                (Phase 2b table, or "not needed — <reason>")
## Change plan           (one line per file: what changes, which AC)
## Test commands         (build/typecheck, lint, unit — and the file each came from)
## Not doing             (mentioned but not required; noticed but out of scope)
## Open questions
```

## Final report (Phase 5, appended to the brief and printed)

```
<ID> — <branch or worktree path>   brief: .devloop/<ID>/brief.md
| AC | Status (done/partial/not done) | Evidence (test name, command + result, or file:line) | Kind (run: failed without, passed with / reasoned, not run / manual check) |
Design: <decision — chosen option, class, source>; ADR suggested: yes/no
Changed: <n files, +x/−y> — one line per file → AC
Prerequisites not done here: <what, owner, which AC waits>
Tests: <final-run commands with pass/fail counts copied from output>
Review: <subagent / separate session (model) / cold re-read + why>; rounds; findings fixed / rejected (why) / open; final-delta: <files, findings>
Blast radius: <tested here (tests run/added) | other repos (listed, owner) | author missed <n> | cross-repo not checked?>
Not done / out of scope: …
Pre-existing failures (baseline.txt): …
Gaps: <unread comments, sources that failed to load, Preflight items missing>
Stopped early: <run-budget limit hit, if any>
Next: review the diff, then commit and open a PR (split first with pr-splitter if it grew past ~400 lines)
```
