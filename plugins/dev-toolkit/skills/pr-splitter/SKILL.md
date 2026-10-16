---
name: pr-splitter
description: Use when a branch or PR is too big to review and the user wants it broken up, e.g. "split this PR", "this diff is 3,000 lines", "break my branch into smaller PRs", "make a stacked PR series", "reviewers won't touch this", or a PR has mixed renames, refactors and behaviour changes in one diff. Not for reviewing the PR's content or cleaning up commit messages only.
---

# PR Splitter

## Overview

Turn one large branch into an ordered stack of small PRs where each one is reviewable on its own (one intent, ~200-400 changed lines) and green on its own (builds and passes tests on top of the previous slice). The original branch is kept untouched as a backup, and the stack is proven equivalent to it before anything is pushed.

## When to use

- A branch/PR over ~400 changed lines (excluding generated files and lockfiles) or mixing several intents.
- Reviewers ask for the change to be split, or it has been stuck in review.

## When not to use

- The diff is big but a single mechanical change (one rename, one formatter run, one codemod): ship it as one PR labelled mechanical, with the command that produced it so reviewers can re-run it.
- The user only wants a code review: that is a review task, not a split.
- Interdependent changes that cannot compile apart and are < ~500 lines: splitting adds noise; say so.

## Inputs

| Input | Default |
|---|---|
| Source branch | Current branch |
| Base branch | The repo default branch (`git symbolic-ref refs/remotes/origin/HEAD`), else `main` |
| Target slice size | 200-400 changed lines of hand-written code |
| Build/test commands | Read from CI config, `package.json` scripts, `Makefile`, `pom.xml`/`build.gradle`, `pyproject.toml` |
| Hosting | Infer from `git remote -v` (GitHub/GitLab/other) |

Only ask if the base branch is ambiguous (e.g. the branch was cut from a release branch).

## Workflow

### 1. Protect the original

```bash
git status --porcelain            # must be empty; otherwise ask to commit or stash
git fetch origin
git branch backup/<branch>-$(date +%Y%m%d) <branch>
```

Never modify, rebase or delete `<branch>` itself during the split.

If the base has moved since the branch was cut (`git merge-base <base> <branch>` ≠ `git rev-parse <base>`), or the branch contains merges from the base, restoring whole files from it would revert newer base changes. Make an up-to-date source first and use it as `<branch>` for every later step:

```bash
git switch -c split/source <branch> && git merge origin/<base>   # run tests afterwards
```

If the merge conflicts in non-trivial ways, stop and ask the user to resolve them. Use `origin/<base>` as `<base>` from here on.

Check: `git rev-parse backup/<branch>-<date>` equals `git rev-parse <branch>`.

### 2. Measure and map the diff

```bash
git diff --stat <base>...<branch>          # files and size, three dots = since merge-base
git diff --numstat <base>...<branch> | sort -k1,1nr | head -40
git log --oneline <base>..<branch>         # existing commits may already be good seams
git diff -M --summary <base>...<branch>    # renames/moves/creates/deletes
```

Classify every changed file (or hunk, when a file mixes intents) into one bucket:

| Bucket | Typical content | Order |
|---|---|---|
| A. Mechanical | renames/moves, formatting, import sorting, codemods, dependency bumps with no code change | 1st |
| B. Pure refactor | extract function/module, change signatures with all callers updated, no behaviour change | 2nd |
| C. Infra / types / schema | new types, interfaces, config, migrations (additive), feature flag definitions, new unused helpers | 3rd |
| D. Behaviour | the actual feature/fix, with **its** tests in the same slice | 4th, may be several slices by feature area |
| E. Cleanup | removing old paths, flags, dead code after the switch-over | last |

Database migrations need extra care because each slice may be deployed on its own after merge:
- Additive migrations (new table/column/index) go in bucket C, in a slice before any code that reads them.
- Destructive or renaming migrations (drop/rename column, `NOT NULL` on existing data) go in bucket E, after the slice that stops reading the old shape (expand → migrate → contract). If the original branch does it in one step, flag it in the plan instead of silently reordering.
- Keep migration files byte-identical and in their original order; never renumber or regenerate them (Django `dependencies`, Rails/Flyway/Alembic version ids must match what the original branch produces).

Exclude from size counts: lockfiles, generated code, snapshots, vendored files. Note them; they travel with whichever slice causes them (regenerate, don't hand-split).

Then map dependencies: for each file in D/E, list the A/B/C symbols it uses (search the codebase for the new names). A slice may only depend on slices before it.

Check: a table of every changed file → bucket, lines, depends-on. No file left unclassified.

### 3. Propose the plan and get approval

Group buckets into slices of ~200-400 changed lines. Rules:
- One intent per slice; its title must fit "This PR <verb>s <one thing>".
- Tests go with the code they test, never in a separate "add tests" PR.
- A slice that adds code nothing uses yet (bucket C) is fine if the PR description says which slice uses it.
- If a behaviour slice is still > 400 lines, split by feature area or by layer (data → service → API → UI), each behind the flag if one exists.
- Prefer fewer, coherent slices over many tiny ones; 3-6 slices is typical. A slice < 50 lines should usually merge into a neighbour.
- If the split forces intermediate states that would ship half a feature, propose a feature flag or keep the new code unwired until the last slice.

Show the plan (Output §1) and wait for the user to approve or adjust it before creating branches.

Check: the user approved the slice list.

### 4. Build the slices as stacked branches

Each slice branches off the previous one. For slice *n*:

```bash
git switch -c split/<n>-<slug> <previous slice or base>

# whole files from the original branch
git restore --source=<branch> --staged --worktree -- path/a.ts path/b.ts
# a deleted file
git rm path/old.ts
# only some hunks of a file (interactive; answer y/n per hunk, use 's' to split, 'e' to edit)
git checkout -p <branch> -- path/mixed.ts
# when the original commits already match the slice
git cherry-pick <sha>...
```

`checkout -p` is interactive. In a non-interactive shell, take hunks through a patch instead:

```bash
git diff HEAD <branch> -- path/mixed.ts > .git/mixed.patch   # edit: delete hunks that belong to later slices
git apply --index .git/mixed.patch
```

For a mechanical slice (rename, formatter, codemod) in files the feature also edits, do not extract hunks: re-run the same tool on the slice branch (IDE rename, `git mv` + search-and-replace, `prettier --write`, the codemod), then confirm later slices still end identical to `<branch>` in step 6.

For a file whose hunks must be split along lines a patch can't separate, write the intermediate version by hand (e.g. add the new function in slice 2, switch callers in slice 3), keeping the final content identical to `<branch>`.

Regenerate derived files instead of copying them: lockfile (`npm install` / `pnpm install` / `uv lock` / `poetry lock`), codegen, snapshots (`-u` only for snapshots whose source changed in this slice).

Commit with a message that states the slice's intent. Keep one commit per slice while building: step 5's `-x` runs after every commit, so a half-done intermediate commit would fail.

Check: `git diff --stat <previous>..split/<n>-<slug>` matches the planned files and is within size.

### 5. Prove each slice is green

On each slice branch, run the project's build, typecheck, lint and tests (from CI config). Examples: `pnpm -r build && pnpm -r test`, `./mvnw -B verify`, `./gradlew build`, `go build ./... && go test ./...`, `uv run pytest`.

To test the whole stack in one go (git ≥ 2.38):

```bash
git switch split/<last>-<slug>
git rebase --update-refs -x "<build-and-test command>" <base>
```

It stops on the first slice that fails. A failure means a missing dependency between slices: move the needed hunk earlier (into the failing slice or the one defining the symbol), never patch over it with code that is not in `<branch>`.

Check: every slice passes; record the command and result per slice.

### 6. Prove the stack equals the original

```bash
git diff <branch> split/<last>-<slug> --stat     # must print nothing
```

If anything differs, a hunk was lost or a temporary edit stayed in. Fix in the slice where it belongs and re-run step 5.

Check: the diff is empty (or the only differences are regenerated files the user agreed to, listed in the report).

### 7. Prepare PRs, then ask before pushing

Write a description per slice (Output §2). Each PR targets the previous slice's branch, not the base, so reviewers see only its diff. Then ask before pushing or creating PRs. On approval:

```bash
git push -u origin split/1-<slug> split/2-<slug> ...
# slice 1 targets <base>; slice n targets slice n-1
gh pr create --draft --base <base> --head split/1-<slug> --title "..." --body-file pr1.md                    # GitHub
gh pr create --draft --base split/1-<slug> --head split/2-<slug> --title "..." --body-file pr2.md
glab mr create --draft --target-branch split/1-<slug> --source-branch split/2-<slug> --title "..." --description "$(cat pr2.md)" --yes   # GitLab
```

Drop `--draft` if the user wants them ready for review. After slice 1 merges, retarget slice 2 to the base (many hosts do this automatically when the base branch is deleted after merge).

Check: the user approved the push; PR links listed.

### 8. Maintaining the stack during review

When review changes land on slice *k*: add a new commit on `split/<k>-<slug>` (prefer new commits over amending), then rebase the slices above it in one go:

```bash
git switch split/<last>-<slug>
git rebase --update-refs split/<k>-<slug>     # replays k+1..last and moves every intermediate branch
```

Re-run step 5 and step 6 (the equivalence check now compares against `<branch>` plus the review fixes; list those fixes). Pushing rewritten branches needs `git push --force-with-lease`; ask first every time.

Optional tools that automate stacking (use only if the user already uses one): Graphite CLI (`gt`), git-branchless, ghstack (one commit per PR, GitHub), spr (one commit per PR, GitHub), Sapling. Everything above works with plain git.

## Output

### §1 Split plan (before any branch is created)

```markdown
Source: feature/billing-v2 (2,140 lines, 61 files) → base: main
Backup: backup/feature-billing-v2-20261016
Excluded from size: pnpm-lock.yaml (+310), src/gen/** (+420)

| # | Branch | Intent | Files | ±Lines | Depends on | Risk |
|---|---|---|---|---|---|---|
| 1 | split/1-rename-invoice | Rename `Bill` → `Invoice` (mechanical) | 18 | +240/-240 | – | low |
| 2 | split/2-money-type | Add `Money` value type + tests (unused) | 4 | +180 | 1 | low |
| 3 | split/3-tax-service | Compute tax via `Money` behind `billing_v2` flag + tests | 9 | +330/-40 | 2 | medium |
| 4 | split/4-invoice-api | Expose tax on invoice API + tests | 11 | +290/-60 | 3 | medium |
| 5 | split/5-remove-legacy | Delete legacy tax path | 6 | +10/-370 | 4 | low |
Unassigned files: none
```

### §2 PR description per slice

```markdown
## <Title: verb + one thing>
Part <n>/<total> of <feature>. Depends on #<prev PR> (base branch: split/<n-1>-...).

**What:** <1-3 bullets>
**Why separate:** <mechanical / no behaviour change / introduces unused type used in #<next>>
**Behaviour change:** none | <describe; flag name if gated>
**How to review:** <e.g. "rename only, generated by IDE; skim", or "start at TaxService.ts">
**Verified:** `<command>` passes on this branch.
```

### §3 Final report

Slice table with branch, PR link (if created), lines, per-slice green result, and the result of the equivalence check in step 6.

## Guardrails

- Never modify, rebase, force-push or delete the original branch; never delete the backup.
- Never push, force-push (even `--force-with-lease`), or open/retarget PRs without explicit confirmation.
- Never add code to a slice that is not in the original branch, except temporary scaffolding that a later slice removes; list any such scaffolding in the report.
- Never split tests away from the code they test, or ship a slice that only passes because a later slice fixes it.
- Uncommitted work in the tree: stop and ask; never stash or discard silently.
- Original branch is already red: report it, split anyway only if the user agrees, and mark which failures were pre-existing.

## Common mistakes

| Mistake | Fix |
|---|---|
| Splitting by file type or directory ("all backend", "all tests") | Split by intent; a slice must make sense as a change on its own |
| Slices compile only together | Move the defining hunk earlier; check with `git rebase --update-refs -x ...` |
| Hand-merging lockfiles or generated code across slices | Regenerate in the slice that changes the input |
| Every PR targets `main`, so slice 3 shows slices 1-3 | Target the previous slice's branch; retarget after each merge |
| Forgetting the equivalence check | `git diff <branch> <last-slice>` must be empty before pushing |
| Code slice merged before the migration it needs, or a column drop before the code stops reading it | Additive migrations first, destructive ones last (step 2) |
| A "refactor" slice that quietly changes behaviour | If any test assertion changes in a refactor slice, it is a behaviour slice |
| 15 tiny PRs | Aim for 3-6; merge slices < 50 lines into a neighbour |

## Example

User: "Split `feature/search-filters` into reviewable PRs." 1,480 changed lines, base `main`, pnpm monorepo.

1. Backup `backup/feature-search-filters-20261016`.
2. Map: 520 lines are a `Filter` → `SearchFilter` rename across 30 files (A); 160 lines add a `FilterSpec` type and parser (C); 610 lines wire filters into the API and UI with tests (D); 190 lines delete the old query-string parser (E).
3. Plan: (1) rename, 520 lines but mechanical, note "generated by IDE rename" (2) `FilterSpec` + parser tests (3) API filters + tests, 280 (4) UI filters + tests, 330 (5) delete old parser. User approves.
4-5. `git rebase --update-refs -x "pnpm -r build && pnpm -r test" main` stops at slice 3: the API calls `SearchFilter.toQuery()`, which was added in a hunk of `filters.ts` assigned to slice 4. Move that hunk into slice 2 with `git checkout -p`, rebase again: all five slices green.
6. `git diff feature/search-filters split/5-remove-old-parser` is empty.
7. Five descriptions written; asks "Push the 5 branches and open stacked draft PRs on GitHub?"
