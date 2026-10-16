# Testing — baseline commands, revert proof, self-review

Read this in Phase 2c (baseline) and Phase 4 (testing your own work). It is
also the revert proof that [review.md](review.md) points to.

## 1. Discover the commands (never invent one)

| Ecosystem | Look in | Typical commands |
|---|---|---|
| JS/TS | `package.json` scripts, lockfile (npm/pnpm/yarn/bun) | `pnpm test`, `pnpm lint`, `pnpm exec tsc --noEmit` |
| JS/TS monorepo | `pnpm-workspace.yaml` / `workspaces`, `turbo.json`, `nx.json`; the touched package's own `package.json` | `pnpm --filter <pkg> test`, `pnpm --filter <pkg> exec vitest run <file>`, `pnpm turbo run test --filter=<pkg>`, `npx nx test <project>`; typecheck with the package's script or `tsc -b` when it uses project references |
| Python | `pyproject.toml` (`[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.mypy]`), `tox.ini`, `noxfile.py`, `Makefile`; `uv.lock`/`poetry.lock` | `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `poetry run pytest` |
| Java/Kotlin | `settings.gradle(.kts)` `include(...)`, `build.gradle(.kts)` plugins (checkstyle, spotless, detekt), `pom.xml` | `./gradlew :<module>:test --tests '<Class>'`, `./gradlew :<module>:check`, `./mvnw -pl <module> -am verify` |
| Go | `go.mod`, `Makefile`, `.golangci.yml` | `go build ./...`, `go vet ./...`, `go test ./<pkg>/... -run '<TestName>'`, `golangci-lint run` (only if configured) |
| Any | CI config (`.github/workflows/*`, `.gitlab-ci.yml`, `Jenkinsfile`) test/lint jobs | whatever CI runs |

- **Watch modes hang an agent.** Vitest watches by default in a terminal: use
  `vitest run`. Never pass `--watch`/`-w` to any runner.
- **Monorepo scope:** run the touched package and every workspace package that
  depends on it (`pnpm --filter '...<pkg>' test` includes dependents).
- **A package with no tests** (e.g. Go `? <pkg> [no test files]`) still gets
  tests for each AC: copy the test style of the nearest tested sibling package.
  Test through a seam that already exists (exported function, HTTP handler via
  `httptest`/`TestClient`/`supertest`). If none exists, a minimal seam is
  "required by the AC"; put it in the Change plan, and if it changes an
  exported signature it is a Design `ask`.

Save pass/fail and each failing test's first error line to
`.devloop/<ID>/baseline.txt`.

## 2. Revert proof ("fails without, passes with")

Never use `git stash` (the stash is shared by every worktree).

1. **Back up** every changed/new non-test file into `.devloop/<ID>/revert/`
   keeping paths; save `git diff --stat` **and** `git status --porcelain`
   (new files are untracked, so `diff --stat` alone misses them) to
   `.devloop/<ID>/revert/state.txt`.
2. **Revert:** `git restore --source=<base> --worktree -- <changed files>`
   (or `git checkout <base> -- <files>` on git < 2.23); move new non-test files
   into the backup.
3. **Run the new tests.** They must fail **on the AC's assertion**. An import or
   compile error is not that: add an empty stub so the assertion itself fails,
   or mark the AC `reasoned, not run`.
4. **Restore** from the backup; `git diff --stat` and `git status --porcelain`
   must match `state.txt` and the tests pass. Mismatch → stop, run nothing
   else, give the user the backup path.

A test that passes with the change reverted proves nothing: rewrite it. This
covers every test in the final diff, including ones a reviewer added.
`reasoned, not run` is allowed only when reverting is impractical (build > ~5
min, or tests live in the same file as the code: Rust `#[cfg(test)]`,
doctests). For UI/config ACs a unit test can't reach, the evidence is a manual
check you actually ran (request, rendered page, CLI call) with its output.

## 3. Self-review checklist (`git diff <base>` plus new files, line by line)

- **Scope:** delete anything not serving an AC: debug prints, commented code,
  unused imports, speculative params, drive-by formatting.
- **Security at trust boundaries:** input validated, queries parameterised, no secrets logged.
- **Copies:** any literal, block or fixture appearing twice → defined once.
- **Meaning changes:** an existing field whose meaning changes but type doesn't → new field, or a Design `ask`.
- **Repo rules:** each brief row met, or why not.
- **Doc placement:** doc comments still sit directly above their declaration.
- **Type escapes:** no new `as any` / `# type: ignore` / `@SuppressWarnings` / `//nolint` without a reason comment.
