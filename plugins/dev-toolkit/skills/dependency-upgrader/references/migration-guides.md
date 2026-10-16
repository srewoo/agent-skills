# Migration guides and codemods for common major upgrades

Starting points only. Versions move: always open the vendor's guide for the exact major you are crossing, and check the codemod's own README for current flags. Run every codemod on a clean tree and commit its diff on its own.

## JavaScript / TypeScript

| Upgrade | Official guide | Codemod / automation | Watch for |
|---|---|---|---|
| React 18 → 19 | react.dev/blog/2024/04/25/react-19-upgrade-guide | `npx codemod@latest react/19/migration-recipe`; types: `npx types-react-codemod@latest preset-19 <paths>` | Go to 18.3 first (warns on removed APIs). Removed: `ReactDOM.render`/`hydrate`, string refs, `propTypes`/`defaultProps` on function components, legacy context. `useRef()` needs an argument in types. Bump `@types/react*`, `@testing-library/react` ≥ 16 |
| Next.js N → N+1 | nextjs.org/docs/app/guides/upgrading | Before 16.1: `npx @next/codemod@canary upgrade major` (or `upgrade <version>`); 16.1+: built-in `next upgrade`. Named transforms: `npx @next/codemod <transform> <path>` | Runs non-interactively in agents/CI and accepts every default (incl. React upgrade); use `--skip-react-upgrade` if React is a separate hop. Async request APIs (`cookies()`, `headers()`, `params`) since 15 |
| Node.js LTS → next LTS | nodejs.org/en/blog (release post "Notable changes" + "Semver-major commits") | none | Update `.nvmrc`, `engines`, Dockerfile `FROM node:<n>`, CI matrix, serverless runtime. Rebuild native addons (`npm rebuild`). Check `node --trace-deprecation` output |
| TypeScript 5.x → next | devblogs.microsoft.com/typescript (release post "Breaking changes") | none | Pin exact version; new errors are usually stricter inference |
| Angular N → N+1 | angular.dev/update-guide | `ng update @angular/core@<N> @angular/cli@<N>` (runs migrations) | One major at a time is mandatory; TypeScript and RxJS ranges move with it |
| Vue 2 → 3 | v3-migration.vuejs.org | `@vue/compat` migration build | Large; split by component area |
| ESLint 8 → 9 | eslint.org/docs/latest/use/migrate-to-9.0.0 | `npx @eslint/migrate-config .eslintrc.json` | Flat config (`eslint.config.js`); plugins must support flat config |
| Jest → newer major | jestjs.io/docs/upgrading-to-jest<N> | none | `jest-environment-jsdom` is a separate package since 28 |

## Python

| Upgrade | Official guide | Codemod / automation | Watch for |
|---|---|---|---|
| Python 3.x → 3.y | docs.python.org/3/whatsnew/3.y.html ("Removed", "Porting to Python 3.y") | `ruff check --select UP --target-version py3y --fix`, or `pyupgrade --py3y-plus` | Update `requires-python`, `.python-version`, Dockerfile, CI. Removed stdlib modules (3.12: `distutils`, `asynchat`, `imp`; 3.13: `cgi`, `crypt`, `telnetlib` and other "dead batteries"). C-extension wheels may lag a new release |
| Django N → N+1 | docs.djangoproject.com/en/stable/howto/upgrade-version/ + release notes "Backwards incompatible changes" | `django-upgrade --target-version <x.y> $(git ls-files '*.py')` | Go to the last LTS / last minor of the old series first and run `python -Wa manage.py test` until clean. Check every third-party app's supported versions |
| Pydantic 1 → 2 | docs.pydantic.dev/latest/migration/ | `bump-pydantic <package>` | `pydantic.v1` shim exists for gradual migration |
| SQLAlchemy 1.4 → 2.0 | docs.sqlalchemy.org/en/20/changelog/migration_20.html | none; run 1.4 with `SQLALCHEMY_WARN_20=1` first | 2.0-style `select()`, no autocommit |
| pandas 1 → 2 | pandas.pydata.org release notes "Backwards incompatible API changes" | none | Run with `-W error::FutureWarning` on the last 1.x first |

## JVM

| Upgrade | Official guide | Codemod / automation | Watch for |
|---|---|---|---|
| Spring Boot 2.7 → 3.x | github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide | OpenRewrite `org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_5` (or `_3_0` … `_3_4` for an earlier 3.x) from `rewrite-spring` | Requires Java 17+; `javax.*` → `jakarta.*`; Spring Security 6 config; add `spring-boot-properties-migrator` temporarily to log renamed properties. Go to 2.7.x first |
| Spring Boot 3.x → 4.0 | Spring Boot 4.0 Migration Guide on the spring-boot wiki | OpenRewrite `org.openrewrite.java.spring.boot4.UpgradeSpringBoot_4_0` | Go to 3.5.x first; Spring Framework 7, Security 7, Jakarta EE 11 |
| Java 11/17 → 21 | Oracle JDK migration guide + JDK release notes | OpenRewrite `org.openrewrite.java.migrate.UpgradeToJava21` from `rewrite-migrate-java` (also `UpgradeToJava17`, `UpgradeToJava25`) | Bump build plugins (compiler, surefire, Lombok, Mockito, ByteBuddy, Jacoco) to Java-21-aware versions; toolchain in `build.gradle` / `maven.compiler.release` |
| Gradle N → N+1 | docs.gradle.org/current/userguide/upgrading_version_<N>.html | `./gradlew wrapper --gradle-version <x>` | Run `./gradlew build --warning-mode all` on the old version first |

Running an OpenRewrite recipe without editing the build:

```bash
# Maven
./mvnw -U org.openrewrite.maven:rewrite-maven-plugin:run \
  -Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-spring:RELEASE \
  -Drewrite.activeRecipes=org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_5
# use rewrite-migrate-java:RELEASE and org.openrewrite.java.migrate.UpgradeToJava21 for the JDK
```

Gradle: copy the init script from the recipe's page on docs.openrewrite.org, save it as `init.gradle`, and run `./gradlew --init-script init.gradle rewriteRun` (`rewriteDryRun` to preview). If artifact resolution fails on the newest recipe versions, pin the plugin/recipe versions shown on that page.

## Go / others

| Upgrade | Guide | Automation | Watch for |
|---|---|---|---|
| Go toolchain 1.x → 1.y | go.dev/doc/go1.y | `go mod edit -go=1.y` (and `toolchain` line), `go fix ./...` | Update Dockerfile and CI `setup-go`; `go vet` gets stricter |
| Go module v1 → v2+ | module's release notes | `go get example.com/mod/v2@latest`, then rewrite imports (`gofmt -r` or search-and-replace on the import path) | Major versions are different import paths; both can coexist during migration |
| Rails N → N+1 | guides.rubyonrails.org/upgrading_ruby_on_rails.html | `bin/rails app:update` | Go to the latest patch of the current minor first; `new_framework_defaults_*.rb` flags one at a time |
