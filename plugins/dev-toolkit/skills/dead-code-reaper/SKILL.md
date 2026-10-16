---
name: dead-code-reaper
description: Use when the user wants to find or remove unused code, e.g. "find dead code", "remove unused exports", "what files are unused", "clean up unused dependencies", "delete stale feature flags", "this flag has been at 100% for months", or before a refactor or migration to shrink the surface. Covers JS/TS, Python, Go and Java/Kotlin. Not for removing code that is used but deprecated, or for upgrading dependencies.
---

# Dead Code Reaper

## Overview

Static analysers produce **candidates**, not proof. Every candidate is checked against the ways code is reached without a direct import (reflection, string-based lookup, framework conventions, config, other repos), sorted by confidence, and shown to the user as a table. Code is deleted only after the user approves the list, in small batches with build and tests green between each.

## When to use

- Unused exports, files, functions, classes, dependencies, or feature flags fully rolled out or abandoned.
- Shrinking a codebase before a migration, refactor or upgrade.

## When not to use

- Code that is used but deprecated: migrate callers first (deprecation is a migration, not a deletion).
- Upgrading a dependency: use the `dependency-upgrader` skill.
- Coverage gaps (code that runs but is untested): use the `test-gap-finder` skill. Zero coverage is not evidence of dead code.

## Inputs

| Input | Default |
|---|---|
| Scope | Whole repo; in a monorepo, every workspace/module |
| Categories | exports, files, dependencies, private members, feature flags |
| Is this a published library? | Detect: `"private": true` missing in package.json, `[project]` published to PyPI, Maven `distributionManagement`, Go module imported elsewhere. If published, every public symbol is out of scope unless the user says otherwise |
| Stale-flag threshold | Flag at 100% (or 0%) in **all** environments, no targeting rules, unchanged for ≥ 30 days |
| Flag data source | Ask once if flags are in scope: flag service export/API, or a config file in the repo |

## Workflow

### 1. Establish a green baseline

Clean tree (`git status --porcelain` empty), new branch `chore/remove-dead-code`, then run build, typecheck, tests and lint the way CI does. Record results. If the baseline is red, stop and report: deletions cannot be verified against a red build. If there are no tests, say so; only the compiler/type checker will verify, so restrict deletions to **high** confidence.

Check: baseline results recorded.

### 2. Map the entry points

Before running any tool, list how code is reached so you can recognise false positives:

- Executables: `main` functions, `package.json` `bin`/`main`/`exports`, `[project.scripts]`/`console_scripts`, `if __name__ == "__main__"`, Dockerfile `CMD`/`ENTRYPOINT`, cron/CI scripts.
- Framework conventions: Next.js/Remix/Nuxt/SvelteKit routes (`app/**/page.tsx`, `route.ts`, `pages/**`, `middleware.ts`), Django (`INSTALLED_APPS`, `urls.py`, admin, signals, management commands, migrations), Spring (`@Component`, `@Bean`, `@Controller`, `@EventListener`, `@Scheduled`), Rails-style autoloading, test fixtures (pytest `conftest.py`), Storybook stories.
- Config-wired handlers: `serverless.yml`/`template.yaml` (SAM)/Terraform `handler = "..."`, Kubernetes job commands, queue consumers registered by name, Celery task names, `META-INF/services` (Java ServiceLoader), `META-INF/spring/*.imports`, plugin registries, DI containers.
- Dynamic access: `import()` with template strings, `require(variable)`, `importlib.import_module`, `getattr`, `__all__`, Java reflection / `Class.forName`, Go `reflect`, `//go:linkname`, cgo `//export`, serialisation (Jackson/Pydantic/JPA accessors), codegen output (protobuf/GraphQL/OpenAPI clients).
- Consumers outside this repo: published packages, shared libraries in other repos, public HTTP/gRPC APIs, scheduled jobs in other systems.

Check: an entry-point list exists and is fed to the tool config (e.g. Knip `entry`) where the tool supports it.

### 3. Run the analysers

| Ecosystem | Code | Dependencies |
|---|---|---|
| JS/TS | `npx knip` (monorepo-aware; use `--reporter compact`, `--production` to ignore test-only usage, `--include files,exports,types`). prefer Knip over `ts-prune` (last npm release 0.10.3, 2021), which covers exports only. Knip does not report unused exports of entry files (a package's `exports`/`main`) unless you pass `--include-entry-exports`; leave it off for published packages. Never run `knip --fix` / `--allow-remove-files`: it deletes before step 6 approval | `npx knip --dependencies` (`depcheck` is archived; Knip replaces it) |
| Python | `vulture src/ --sort-by-size` (unused functions/classes/attributes are reported at 60% confidence, imports at 90%, unreachable code at 100%; `--min-confidence 80` hides most dead functions). Record confirmed false positives with `--make-whitelist > vulture_whitelist.py` and pass that file on later runs | `deptry .` (DEP002 = declared but unused) |
| Go | `staticcheck -checks U1000 ./...` (unused); `go run golang.org/x/tools/cmd/deadcode@latest -test ./...` (unreachable from `main`; needs a main package) | `go mod tidy` then `git diff go.mod` |
| Java | PMD: `pmd check -d src/main/java -R category/java/bestpractices.xml/UnusedPrivateMethod,category/java/bestpractices.xml/UnusedPrivateField -f text`; IntelliJ "Unused declaration" inspection (Code > Inspect Code, or headless `inspect.sh`) for non-private code | Maven `./mvnw dependency:analyze` ("Unused declared"); Gradle `com.autonomousapps.dependency-analysis` plugin, `./gradlew buildHealth` |
| Kotlin | detekt unused-member rules (`UnusedPrivateMember`/`UnusedPrivateProperty` family), IntelliJ inspection | same as Java |

Knip reads framework plugins (Next.js, Vite, Jest, Storybook, …) automatically, so Next.js App Router convention exports (`default`, `GET`/`POST`, `generateMetadata`, `generateStaticParams`, `metadata`, `revalidate`, `dynamic`) in `app/**` are entry exports, not dead; if it reports config files or route files as unused, fix `knip.json` (`entry`, `project`, `ignore`) rather than trusting the result. Go build tags and OS-specific files are only analysed for the current `GOOS`/tags: run with each tag set the project builds (`-tags`), or treat tag-guarded code as low confidence.

Check: raw tool output saved per ecosystem, with the exact command used.

### 4. Verify every candidate

For each candidate symbol or file:

1. **Text search for the name everywhere, not just imports**, including non-code files:
   ```bash
   git grep -n -w '<Name>' -- . ':!<the defining file>'
   git grep -n -i -e '<name>' -e '<snake_name>' -e '<kebab-name>' -- '*.yml' '*.yaml' '*.json' '*.toml' '*.xml' '*.html' '*.sql' '*.tf' '*.md'
   ```
   For a file, also search for its path and basename without extension.
2. Check it against the entry-point list from step 2 (convention paths, decorators/annotations, config wiring, dynamic access patterns near the call site).
3. Public API? Exported from a package's entry (`index.ts`, `__init__.py` `__all__`, `exports` map, public Java class in a published artefact): low confidence unless the user confirms there are no external consumers.
4. Recent history: `git log -1 --format='%ar %an' -- <file>`. Code added in the last few weeks is often waiting for a caller in an open branch.

Assign confidence:

| Confidence | Criteria | Default action |
|---|---|---|
| High | Tool flags it, zero text references outside its definition and its own tests, not an entry point, not public API, no dynamic-access pattern in that module | Propose delete |
| Medium | No code references, but the name appears in strings/config/docs, or it lives in a convention directory, or was touched < 30 days ago | Ask per item |
| Low | Public API of a published package, reflection/DI/serialisation-annotated, or matched by a dynamic import pattern | Keep; list for the owner |

Tests that only test the dead code are dead with it; tests that are the only caller are **not** evidence of use.

Check: every candidate has a confidence and an evidence line. Nothing is left "unchecked".

### 5. Find stale feature flags (if in scope)

1. Get flag state: the flag service's export/API, or the repo's flag config. A flag is stale when it is fully on (100%) or fully off (0%) in every environment, has no targeting rules or overrides, and has not changed for ≥ 30 days (or the user's threshold).
2. Find usages: `git grep -n -e '<flag-key>'` plus the constant name that holds it, across all repos you can see. Note any usage outside this repo.
3. The winning branch is the one users get today (on → the "enabled" branch; off → the "disabled" branch). Removal = inline the winning branch, delete the losing branch, then delete code only the losing branch used (re-run step 3 afterwards; it usually exposes new dead code).
4. The flag definition in the flag service is removed **after** the code removal is deployed everywhere, by the user. Never change flag state yourself.

Check: a stale-flag table (key, state, since, usages, winning branch).

### 6. Present the candidate table and get approval

Show the Output table. Ask the user to approve by row number (e.g. "approve 1-14, 17; skip 15-16"). Do not delete anything before this.

Check: an explicit approved list.

### 7. Delete in small batches

- One batch = one module or ~10 files / ~300 deleted lines, one category. Separate commits for dependencies, flags and code.
- After each batch: build, typecheck, lint, tests (the baseline commands). Green → commit `chore(dead-code): remove <what> (<n> items)`. Red → revert that batch (`git restore --source=HEAD --staged --worktree .`; plain `git restore .` leaves `git rm` deletions staged), move the item that broke to "kept" with the failure as evidence, continue.
- Removing a dependency: use the package manager (`npm uninstall`, `pnpm remove`, `uv remove`, `poetry remove`, edit the build file for Maven/Gradle, `go mod tidy`) so the lockfile updates.
- After all batches, re-run the analysers once: deletions expose new dead code. Report the new candidates; delete them only after another approval.

Check: all batches committed, final run matches baseline, second-pass candidate list produced.

## Output

```markdown
# Dead code report: <repo> (<date>)
Baseline: build ✔ typecheck ✔ tests 1,204 ✔ lint ✔ · Branch: chore/remove-dead-code
Tools: knip 5.x, deptry 0.x (commands in appendix)

## Candidates
| # | Kind | Location | Symbol / item | Found by | References found | Confidence | Evidence | Proposed |
|---|---|---|---|---|---|---|---|---|
| 1 | export | src/utils/date.ts:42 | `formatLegacyDate` | knip | none | High | 0 grep hits; not in index.ts | delete |
| 2 | file | src/jobs/reindex.ts | whole file | knip | `reindex` in serverless.yml:31 | Low | wired as Lambda handler | keep |
| 3 | dependency | package.json | `moment` | knip | none in src | High | only used by #1 | remove |
| 4 | flag | `new-checkout` | 100% on all envs since 2026-07-02 | flag export | 6 usages, 2 files | High | inline "on" branch | inline |

## Result (after approval)
| Batch | Items | Lines removed | Build/tests | Commit |
|---|---|---|---|---|
| 1 | #1, #3 | -212 | ✔ | abc1234 |

Kept (false positives / failed batch): #2 (Lambda handler), …
Second-pass candidates: <n> (not deleted; need approval)
Follow-ups for the user: remove flag `new-checkout` from the flag service after deploy; add #2 to knip `entry`.
```

## Guardrails

- Never delete anything before the user approves the specific rows; that includes auto-fixers (`knip --fix`, IDE "safe delete" in bulk).
- Never delete public API of a published library, DB migrations, or code referenced from config/infra without explicit confirmation of that row.
- Never change feature flag state or delete flags in the flag service; only edit code.
- Never weaken or delete tests to make a batch green; a red batch is reverted.
- Never push or open a PR without confirmation.
- Red baseline: stop. No tests: high-confidence deletions only, and say "verified by compiler only".

## Common mistakes

| Mistake | Fix |
|---|---|
| Treating tool output as proof | Every row needs grep evidence and an entry-point check |
| Searching only for imports | Search strings, config, templates, infra files and other repos |
| Deleting a Next.js page / Lambda handler / Spring bean "nobody imports" | Map entry points first (step 2); fix the tool config instead |
| One giant deletion commit | Batches with build+tests between, one commit each, so a revert is one command |
| Removing a flag and the losing branch's helpers in one step without re-scanning | Inline the winner, then re-run the analysers |
| Deleting code added last week | Check `git log`; it may await a caller in an open branch |
| Calling untested code "dead" | Coverage ≠ reachability; use static analysis plus references |

## Example

User: "Clean out dead code in our TypeScript monorepo (pnpm, Next.js app + 2 packages)."

1. Baseline green, branch created.
2. Entry points: Next.js `app/**`, `packages/sdk` is published (`exports` map), `scripts/*.ts` run from CI, `serverless.yml` handlers in `apps/worker`.
3. `npx knip --reporter compact`: 41 unused exports, 9 files, 4 dependencies. 3 of the 9 "unused files" are `apps/worker/src/handlers/*`; add them to `knip.json` `entry` and re-run: 6 files.
4. Grep: `templates/email.ts` export `renderLegacy` appears in `emails.json` → Medium. 12 exports from `packages/sdk/src/index.ts` → Low (published). 26 exports, 5 files, 3 deps → High.
5. Flag `new-onboarding` at 100% in prod and staging for 74 days, 4 usages → inline "on".
6. Table shown; user approves High rows and the flag, skips Medium.
7. Four batches, all green; second pass finds 7 newly unused helpers from the flag's old branch, listed for approval.
