---
name: dependency-upgrader
description: Use when the user wants to move one dependency, framework or runtime across a major version, e.g. "upgrade to React 19", "bump Next.js to 15", "move us to Node 22", "migrate Spring Boot 2 to 3", "Java 17 to 21", "upgrade Django to 5", "Python 3.9 is EOL", or when a build breaks with peer-dependency conflicts or deprecation warnings after a major bump. Not for routine minor/patch bumps or bulk Dependabot/Renovate PRs.
---

# Dependency Upgrader

## Overview

Upgrade exactly one thing across a major version, one major at a time, starting from a green baseline, using the vendor's own migration guide and codemods before hand edits. The upgrade is done when build, typecheck, tests and lint are as green as the baseline and every breaking change in the guide is accounted for in a report.

## When to use

- One package, framework or runtime is moving across a major version (React 18→19, Next 14→15, Node 18→22, Python 3.9→3.12, Spring Boot 2.7→3.x, Java 17→21, Django 4.2→5.2, Angular N→N+1).
- A major bump left peer-dependency conflicts, type errors or deprecation warnings to clean up.

## When not to use

- Patch/minor bumps or batching many unrelated bumps: use the ecosystem's update tooling (`npm update`, Renovate, Dependabot) and normal CI.
- Responding to a CVE with a patch release: bump the patch, no migration needed.
- Tests are flaky before you start: fix that first (the `flaky-test-hunter` skill), or the green baseline is meaningless.

## Inputs

| Input | Default if not given |
|---|---|
| Target (package/runtime + version) | Ask; this has no safe default |
| Target version | Latest stable major, or for runtimes the latest **LTS** (Node even-numbered Active LTS, Java LTS 17/21/25) |
| Scope in a monorepo | Every workspace that depends on it, upgraded together |
| Branch name | `chore/upgrade-<name>-<major>` |

Ask for anything without a default in one message, then proceed.

## Workflow

### 1. Detect the toolchain

Read the root and look for these files:

| File | Ecosystem / tool | Monorepo signal |
|---|---|---|
| `pnpm-lock.yaml` / `yarn.lock` / `package-lock.json` / `bun.lock(b)` | pnpm / yarn / npm / bun | `pnpm-workspace.yaml`, `"workspaces"` in package.json, `nx.json`, `turbo.json`, `lerna.json` |
| `uv.lock` / `poetry.lock` / `Pipfile.lock` / `requirements*.txt` | uv / Poetry / Pipenv / pip | multiple `pyproject.toml` |
| `pom.xml` / `build.gradle(.kts)` + `gradle/libs.versions.toml` | Maven / Gradle | `<modules>` / `settings.gradle` `include(...)` |
| `go.mod` / `go.work` | Go modules | `go.work` |

Also find every place the version is pinned: `engines`, `.nvmrc`, `.node-version`, `.tool-versions`, `.python-version`, `requires-python`, `<java.version>`/`toolchain`, `Dockerfile` `FROM`, CI workflow files (`setup-node`, `setup-python`, `setup-java` versions), `runtime.txt`, serverless/runtime configs.

Check: you can name the package manager, list the workspaces/modules that depend on the target, and list every file that pins a runtime version.

### 2. Establish a green baseline

On the current default branch, with a clean working tree (`git status --porcelain` empty), run the project's own commands. Prefer scripts already defined in `package.json`, `Makefile`, CI config. Typical:

- JS/TS: `pnpm install --frozen-lockfile && pnpm -r build && pnpm -r --if-present run typecheck && pnpm -r test && pnpm -r lint` (npm: `npm ci`, `--workspaces`; yarn: `yarn install --immutable`, `yarn workspaces foreach -A run test`)
- Python: `uv sync --frozen && uv run pytest && uv run ruff check . && uv run mypy .` (Poetry 2: `poetry sync`, `poetry run pytest`; pip: `pip install -r requirements.txt` in a fresh venv)
- Maven: `./mvnw -B verify` — Gradle: `./gradlew build` — Go: `go build ./... && go vet ./... && go test ./...`

Record pass/fail counts and the number of existing warnings. If something is already red, write it down as "pre-existing" and do not count it against the upgrade. If there are no tests, say so in the report and add a smoke check (app boots, one request/page renders) before continuing.

Check: a baseline table exists (command, result, failures, warnings).

### 3. Branch

`git switch -c chore/upgrade-<name>-<major>`. Commit each step below separately so any one can be reverted.

Check: on the new branch, working tree clean.

### 4. Read the official migration material

Find, in this order: the vendor's upgrade/migration guide for each major you cross, the CHANGELOG/release notes "Breaking changes" sections, and the official codemod or recipe. [references/migration-guides.md](references/migration-guides.md) lists guides and codemods for common upgrades; otherwise search "<name> <major> migration guide" on the vendor's site.

Turn the guide into a checklist of breaking changes, then search the codebase for each one (removed API names, renamed config keys, changed defaults) and mark it *applies* / *does not apply*.

Check: a breaking-change checklist exists with every item marked, with file counts for those that apply.

### 5. Plan the hop path and the peer cascade

- **One major at a time.** 2→4 means 2→3, green, commit, then 3→4. Exception: the vendor's guide explicitly supports skipping (it says so, or its codemod targets the final version directly).
- Prerequisite runtimes are their own hop: if the target needs a newer runtime (Spring Boot 3 needs Java 17, Django 5 needs Python 3.10, Next 15 needs Node 18.18), upgrade the runtime first as a separate, green, committed hop and list it in the report.
- Bridge releases first: if the guide says "upgrade to the last minor of the old major and fix deprecations" (Spring Boot 2.7, Django 4.2 LTS, React 18.3, Angular), do that as hop zero.
- Peer cascade: list packages whose `peerDependencies` exclude the new major. npm 7+ fails install on these (`ERESOLVE`); pnpm (`strict-peer-dependencies` is off by default) and Yarn Berry only warn (`Issues with peer dependencies found` / `YN0060`), so read the install output and treat every unmet-peer warning for the target as a blocker.
  - npm: `npm ls <pkg>`, `npm explain <pkg>`; pnpm: `pnpm why <pkg> -r`; yarn: `yarn why <pkg>`. For each blocker, check its latest version's `peerDependencies` with `npm view <dep> peerDependencies`.
  - Python: `uv tree --invert --package <pkg>`, `poetry show --tree`, or `pipdeptree -r -p <pkg>`.
  - Maven: `./mvnw dependency:tree -Dincludes=<groupId>`; Gradle: `./gradlew dependencyInsight --dependency <name>`.
  - Go: a new major is a new import path (`example.com/mod/v2`); `go mod graph | grep <mod>`.
- Companion packages move together: `react` + `react-dom` + `@types/react` + `@types/react-dom`; Spring Boot BOM + Spring Cloud release train; Angular `@angular/*` + CLI + TypeScript range; Django + third-party apps' supported versions.
- A blocker with no compatible release: check its issue tracker/changelog for a canary or a "works, peer range not bumped yet" note, then stop and report it with the options (wait, fork/patch, replace, or a documented temporary hack: npm `overrides`, Yarn `resolutions`, pnpm `pnpm.peerDependencyRules.allowedVersions`, which in pnpm 10 can also live in `pnpm-workspace.yaml`). Choosing the hack is the user's call; do not force-install.

Check: an ordered hop list and a cascade table (package, current, needed, compatible release exists?).

### 6. Apply the bump and update the lockfile

Change the version through the package manager so the lockfile is regenerated consistently, not by hand-editing the lockfile:

- npm `npm install react@19 react-dom@19` · pnpm `pnpm up -r react@19 react-dom@19` · yarn `yarn up react@19 react-dom@19`
- uv `uv add 'django>=5.2,<5.3'` then `uv lock` · Poetry `poetry add django@^5.2` · pip-tools: edit `requirements.in`, `pip-compile`
- Maven/Gradle: edit the version property, BOM or `libs.versions.toml` entry
- Go module `go get example.com/mod/v2@latest && go mod tidy`; Go toolchain `go mod edit -go=1.23`
- Runtime upgrades: install the runtime locally (`nvm install 22`, `uv python install 3.12 && uv venv --python 3.12`, `poetry env use 3.12`, `sdk install java 21-tem` or your JDK manager), recreate the virtualenv/`node_modules`, then update every pin found in step 1 (`.nvmrc`, `engines`, Dockerfile, CI, `requires-python`, `<java.version>`/toolchain), plus base images.

Never use `--force` or `--legacy-peer-deps` to make install pass; that hides the cascade from step 5. Review the lockfile diff for unexpected churn: if unrelated packages moved majors, regenerate with only the target unlocked.

Check: clean install succeeds with the frozen/immutable flag on a fresh checkout of the branch.

### 7. Run official codemods, then fix by hand

Tools that bump the version themselves (`@next/codemod upgrade`, `ng update`) replace the manual bump in step 6. Run the vendor codemod first, review its diff and commit it on its own ("codemod: …"), then fix the rest by hand. Codemods are not complete: re-run the step 4 searches afterwards.

Examples (exact commands for more in the reference file):
- React 19: `npx codemod@latest react/19/migration-recipe` and `npx types-react-codemod@latest preset-19 ./src`
- Next.js: `npx @next/codemod@canary upgrade major` (Next 16.1+ also has a built-in `next upgrade`); it also bumps React unless you pass `--skip-react-upgrade`
- Spring Boot 3 / Java 21: OpenRewrite `org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_5` / `org.openrewrite.java.migrate.UpgradeToJava21` (run commands in the reference file)
- Python syntax: `ruff check --select UP --target-version py312 --fix` or `pyupgrade --py312-plus $(git ls-files '*.py')`
- Django: `django-upgrade --target-version 5.2 $(git ls-files '*.py')`
- Angular: `ng update @angular/core@<N> @angular/cli@<N>` (runs migrations)

Check: every *applies* item in the checklist is marked fixed, or remaining with a reason.

### 8. Verify against the baseline

Run exactly the baseline commands from step 2. The upgrade is green when every check that passed at baseline still passes. New failures must be fixed or explained; never skip, delete or loosen tests to get green.

Check: a before/after table with no new failures.

### 9. Sweep deprecation warnings

Deprecations in the new major are next major's breaking changes. Surface them:

- Node: `NODE_OPTIONS=--trace-deprecation` while running tests; React: console warnings in test output
- Python: pytest's warnings summary (`-W error::DeprecationWarning` to make each one fail loudly) (or `python -Wa manage.py test` for Django)
- Java: `-Xlint:deprecation` (Maven `maven-compiler-plugin` `<compilerArgs>`); Gradle `--warning-mode all`
- Go: `staticcheck ./...` (SA1019 flags deprecated API use)

Fix the warnings that come from the upgraded dependency when the fix is mechanical; list the rest in the report.

Check: warning count recorded, attributable ones fixed or listed.

### 10. Repeat for the next hop, then report

Repeat steps 6-9 for each hop. Then write the report below. Ask before pushing or opening a PR.

## Output

```markdown
# Upgrade report: <name> <from> → <to>
Branch: chore/upgrade-<name>-<major> · Hops: <from> → <x> → <to> · Commits: <n>

## Baseline vs after
| Check | Command | Baseline | After |
|---|---|---|---|
| Build | `pnpm -r build` | pass | pass |
| Tests | `pnpm -r test` | 812 pass / 2 fail (pre-existing) | 812 pass / 2 fail |
| Deprecation warnings | … | 41 | 9 |

## Breaking changes
| Change (from guide) | Applies? | Files | Status | How |
|---|---|---|---|---|
| `ReactDOM.render` removed | yes | 3 | fixed | codemod |
| `forwardRef` no longer needed (ref is a prop) | yes | 22 | remaining | still works in 19; follow-up |

## Dependency cascade
| Package | Before | After | Why |
|---|---|---|---|

## Remaining work / risks
- <item, owner suggestion, whether it blocks merge>

## Rollback
Revert the merge commit (or `git revert <first>^..<last>`); restore lockfile from `main`.
Runtime pins changed in: <files>; deploy the previous image tag if already released.
Data/schema changes: <none | migrations that are not reversible>.
```

## Guardrails

- Never push, open a PR, or merge without explicit confirmation.
- Never upgrade more than the one requested target, except companions and peers the cascade forces; list those.
- Never `--force`, `--legacy-peer-deps`, `overrides`/`resolutions`, or `--no-verify` without stating it in the report as a known hack.
- Never delete, skip or weaken tests to reach green.
- Stop and ask if the upgrade needs a data migration, an irreversible DB migration, a config change in deployed environments, or a runtime change the hosting platform may not support yet (e.g. a serverless runtime version).
- No baseline (red build, no tests): say so in the report's first line; the result is "compiles", not "verified".

## Common mistakes

| Mistake | Fix |
|---|---|
| Jumping several majors in one go | One major per hop, green between, unless the vendor guide says skipping is supported |
| Bumping `react` but not `react-dom`/`@types/react` | Move companion packages together (step 5) |
| Reading a passing `pnpm install` as "no peer conflicts" | pnpm and Yarn only warn; grep the install output for unmet peers |
| Hand-editing the lockfile | Change versions through the package manager, then review the lockfile diff |
| Upgrading Node in `package.json` only | Update `.nvmrc`, Dockerfile, CI matrix, `engines` and platform runtime config too |
| Trusting the codemod as complete | Re-run the breaking-change searches after it |
| Spring Boot 3 before Java 17 / javax→jakarta | Boot 3 requires Java 17+ and Jakarta EE 9+ namespaces; OpenRewrite's Boot 3 recipe handles both |
| Treating pre-existing failures as caused by the upgrade | Compare against the recorded baseline |

## Example

User: "Upgrade our pnpm monorepo to React 19."

1. pnpm, 3 workspaces depend on `react` (`apps/web`, `packages/ui`, `packages/forms`). Node 20 pinned in `.nvmrc` and CI.
2. Baseline: build pass, `tsc` pass, 640 tests pass, lint pass, 12 React warnings.
3. `git switch -c chore/upgrade-react-19`.
4. React 19 guide → checklist: `ReactDOM.render` (2 files), string refs (0), `propTypes` on function components (14 files), `defaultProps` on function components (6), `useRef()` needs an argument (types, 9).
5. Hop zero: `react@18.3` (adds warnings for 19 removals) → green. Cascade: `react-select@5.7` peer `^16.8 || ^17 || ^18` → latest supports 19, bump; `@testing-library/react` 14 → 16.
6. `pnpm up -r react@19 react-dom@19 @types/react@19 @types/react-dom@19`.
7. `npx codemod@latest react/19/migration-recipe`, `npx types-react-codemod@latest preset-19 ./packages ./apps`; hand-fix `defaultProps` → default parameters.
8. After: all green; 640 tests pass.
9. Remaining: 22 `forwardRef` uses (still supported, listed as follow-up).
10. Report written; asks "Push `chore/upgrade-react-19` and open a PR?"
