# Flaky-test root-cause taxonomy

Each class gives the symptoms, a way to **confirm** it by controlling one input, and the **deterministic fix**. Sleeps and retries are never the fix.

## 1. Async / timing waits

- **Symptoms:** "element not found", "expected 3 got 2", "undefined is not a function" on a value that arrives late. Duration sits near a timeout. It fails more under load.
- **Confirm:** run under CPU throttling or with `rerun.py --parallel 8`, and the rate goes up. Adding an artificial delay inside the producer (not the test) makes it fail every time.
- **Fix:** wait on the condition, not a duration.
  - JS: `await` every promise, so a floating promise fails the lint (`@typescript-eslint/no-floating-promises`). Testing Library: `await screen.findByRole(...)` / `waitFor(() => expect(...))`.
  - Fake timers: `jest.useFakeTimers()` + `jest.advanceTimersByTime(ms)`, or `vi.useFakeTimers()` + `vi.advanceTimersByTimeAsync(ms)`.
  - Python: `await` the task. Use `asyncio.wait_for(event.wait(), timeout)`, not `sleep`.
  - Go: channels or `sync.WaitGroup`. Polling `assert.Eventually`/`require.Eventually` is acceptable only for truly external processes. Go 1.25+: `testing/synctest` (`synctest.Test`) gives goroutines a fake clock.
  - Java: Awaitility `await().atMost(5, SECONDS).until(...)`, or a `CountDownLatch` the code under test counts down.

## 2. Test order and shared state

- **Symptoms:** it passes alone and fails in the suite, or only on one shard, or only after a specific test.
- **Confirm:** run `<polluter> <victim>` in that order and it fails. Run `<victim>` alone and it passes. Find the polluter by halving the list of tests that ran before the victim.
- **Fix:** give every test its own state.
  - Reset module singletons, caches and global config in `beforeEach`/fixtures (`jest.resetModules()`, `vi.resetModules()`, `restoreMocks: true`).
  - Use per-test DB transactions that roll back, or unique schema/tenant ids. Spring: `@Transactional` on a test rolls back by default, but not for code that runs on another thread (`webEnvironment = RANDOM_PORT` requests, `@Async`, message listeners) or under `@Commit`; clean those with `@Sql(executionPhase = AFTER_TEST_METHOD)` or truncate tables in `@AfterEach`. The cached `ApplicationContext` (and its embedded DB) is shared across test classes; prefer cleanup over `@DirtiesContext`, which is slow. Use `tmp_path` / `t.TempDir()` / `@TempDir` instead of shared paths.
  - Remove the dependency: the victim must create its own data. Never make the fix "run the polluter first".
  - Restore anything the test patched: env vars (`monkeypatch.setenv`, `t.Setenv`), the working directory, locale.

## 3. Time, timezone and dates

- **Symptoms:** it fails at particular hours (around midnight UTC), at month-end, on Feb 29, at DST changes, or only on CI (CI runs in UTC while developers run in local time). A snapshot contains a date.
- **Confirm:** set `TZ=Pacific/Kiritimati` (UTC+14) and `TZ=Pacific/Pago_Pago` (UTC-11). Freeze the clock at `23:59:59` before a date boundary.
- **Fix:** inject the clock and freeze it.
  - Jest: `jest.useFakeTimers({ now: new Date('2026-02-28T23:30:00Z') })` or `jest.setSystemTime(...)`. Vitest: `vi.setSystemTime(...)`.
  - Python: `freezegun` (`@freeze_time("2026-02-28 23:30:00")`) or `time-machine`. Always compare timezone-aware datetimes.
  - Java: pass a `java.time.Clock` and use `Clock.fixed(Instant.parse(...), ZoneOffset.UTC)` in tests.
  - Go: inject a `func() time.Time` or a clock interface.
  - Playwright: `await page.clock.setFixedTime(new Date('2026-02-28T23:30:00Z'))`. Cypress: `cy.clock(Date.UTC(2026, 1, 28, 23, 30))`.
  - Set `TZ=UTC` explicitly in CI and in test setup, and still test the boundary cases on purpose.

## 4. Randomness and unseeded generators

- **Symptoms:** a different value appears in each failure message. Data comes from faker/factories or UUIDs. A unique constraint collides now and then.
- **Confirm:** pin the seed (`--randomly-seed`, `faker.seed(1)`, `Faker.seed_instance(1)`, `rand.New(rand.NewSource(1))`) and find a seed that fails every time.
- **Fix:** seed the RNG or inject it. Assert on properties, not on generated values. Generate unique keys from a counter, not from random strings. Property-based tests (Hypothesis, fast-check) are fine because they print a replayable seed or example. Keep that seed as a regression case.

## 5. Network and external services

- **Symptoms:** `ECONNRESET`, `ETIMEDOUT`, 429, 503, DNS errors. It fails only on CI (egress rules) or at certain times (rate limits).
- **Confirm:** block the network and the test fails every time. Use `pytest --disable-socket` (pytest-socket), or run in a container with `--network none`.
- **Fix:** keep tests hermetic.
  - HTTP fakes: `msw`/`nock` (JS), `responses`/`respx`/`pytest-httpserver` (Python), `httptest.NewServer` (Go), WireMock/MockWebServer (JVM). Playwright `page.route`, Cypress `cy.intercept` + `cy.wait('@alias')`.
  - For real dependencies (database, broker), use Testcontainers with a readiness wait strategy, not a fixed delay.
  - Keep true third-party contract checks in a separate, non-blocking suite.

## 6. Resource leaks and ports

- **Symptoms:** `EADDRINUSE` / "address already in use", "too many open files", the runner hangs after the tests ("Jest did not exit"), memory climbs, and it fails late in the suite.
- **Confirm:** `jest --detectOpenHandles`, `python -X dev -W error::ResourceWarning -m pytest`, `go.uber.org/goleak` (`goleak.VerifyNone(t)`), `lsof -i :<port>` during the run.
- **Fix:** bind port 0 and read back the assigned port. Close servers, clients, files and DB pools in teardown (`afterAll`, fixture `yield`, `t.Cleanup`, `@AfterEach`, try-with-resources). Use unique temp dirs. Use `RERUN_INDEX` (set by rerun.py) or the worker id (`JEST_WORKER_ID`, `PYTEST_XDIST_WORKER`, `testInfo.workerIndex`) to separate parallel resources.

## 7. Concurrency and races

- **Symptoms:** it fails only with parallelism. The race detector reports a data race. The order of results from goroutines/threads/promises varies. Counts are off by one.
- **Confirm:** `go test -race -count=200 -cpu=1,4,16`. On the JVM, run with more threads, or use jcstress for low-level code. In Vitest, `--sequence.concurrent` runs the tests in a file concurrently. ThreadSanitizer for C/C++/Rust.
- **Fix:** if production code races, fix the product (mutex, atomic, channel, transaction isolation, idempotency key). Then tell the user it is a real bug. If only the test assumes an order, sort the results before asserting or assert on a set.

## 8. Environment and locale

- **Symptoms:** it fails on one OS, runtime version, CPU architecture or locale. It differs between CI image and laptop. Number or date formatting changes (`1.234,5`, the Turkish dotless i). It depends on filesystem case sensitivity, path separators or line endings.
- **Confirm:** run with `LANG=tr_TR.UTF-8 LC_ALL=tr_TR.UTF-8`, `LANG=de_DE.UTF-8`, the CI container image, and a clean clone with no `.env`.
- **Fix:** pin the locale and timezone in test setup. Use locale-explicit APIs (`toLocaleString('en-US')`, `Locale.ROOT`, `str.casefold()`). Pin tool versions (`.nvmrc`, `.python-version`, `go.mod` toolchain, Gradle toolchains). Use `path.join`/`pathlib`. Add `.gitattributes` for line endings.

## 9. UI animation, rendering and selectors

- **Symptoms:** "element is not visible", "element is detached from the DOM", "click intercepted", or a screenshot diff of a few pixels. The selector matched two elements. It fails more on slow CI browsers.
- **Confirm:** CPU throttling (CDP `Emulation.setCPUThrottlingRate`, rate 4) makes it worse. Disabling animations makes it pass every time.
- **Fix:**
  - Use web-first assertions that auto-wait (`await expect(locator).toBeVisible()`, Cypress chained assertions) instead of reading state once.
  - Use role/label locators (`getByRole('button', { name: 'Pay' })`, `data-testid`) instead of CSS position or text that changes.
  - Wait on the network response that drives the UI (`page.waitForResponse`, `cy.wait('@alias')`), not a fixed time.
  - Disable animations: Playwright `use: { reducedMotion: 'reduce' }` and `toHaveScreenshot({ animations: 'disabled' })`, or a test-only CSS rule `*{transition:none!important;animation:none!important}`.
  - Use the same browser version and fonts in CI and locally for visual tests.
