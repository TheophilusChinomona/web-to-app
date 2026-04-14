# cli-anything-web-to-app

CLI-Anything harness for practical inspection and safe build checks against the `web-to-app` Android repository.

## Install

```bash
cd agent-harness
pip install -e .
```

## Use

```bash
cli-anything-web-to-app inspect summary
cli-anything-web-to-app inspect tree --max-depth 2
cli-anything-web-to-app inspect modules
cli-anything-web-to-app inspect feature-map
cli-anything-web-to-app inspect packages
cli-anything-web-to-app inspect manifest
cli-anything-web-to-app inspect variants
cli-anything-web-to-app inspect android-summary
cli-anything-web-to-app inspect gradle
cli-anything-web-to-app inspect dependencies
cli-anything-web-to-app build check
cli-anything-web-to-app build readiness
cli-anything-web-to-app build target --flavor dev --build-type release
cli-anything-web-to-app build assemble-simulate --variant DevDebug
cli-anything-web-to-app build signing-inspect
cli-anything-web-to-app build dry-run --task assembleDebug
cli-anything-web-to-app build assemble --flavor dev --build-type debug
cli-anything-web-to-app build assemble --flavor dev --build-type release --execute
cli-anything-web-to-app build bundle --flavor prod --build-type release
cli-anything-web-to-app build bundle --flavor prod --build-type release --execute
cli-anything-web-to-app extension discover
cli-anything-web-to-app extension show bewlycat
cli-anything-web-to-app extension validate
cli-anything-web-to-app extension stub my-extension
cli-anything-web-to-app extension stub my-extension --write
cli-anything-web-to-app extension plan --action install --extension-id my-extension --source ./my-extension.zip
cli-anything-web-to-app extension plan --action remove --extension-id bewlycat --mutate --execute
cli-anything-web-to-app extension apply --action install --extension-id my-extension --source ./my-extension.zip
cli-anything-web-to-app extension apply --action remove --extension-id bewlycat --execute --confirm remove:bewlycat --allow-destructive
cli-anything-web-to-app config apply-profile
cli-anything-web-to-app config apply-profile --execute
```

JSON output:

```bash
cli-anything-web-to-app --json inspect gradle
```

REPL mode (default when no subcommand):

```bash
cli-anything-web-to-app
# examples:
# inspect summary
# inspect feature-map
# inspect variants
# inspect android-summary
# build dry-run
# extension discover
# extension validate
```

## Implemented command groups

- `inspect`
  - `summary`: quick project health summary
  - `tree`: repository tree (depth-controlled)
  - `modules`: Gradle modules from `settings.gradle.kts`
  - `feature-map`: feature/module map including extension assets
  - `packages`: Kotlin package discovery from source files
  - `manifest`: parsed AndroidManifest metadata (package, app, permissions, activities, services, receivers)
  - `variants`: build types, product flavors, flavor dimensions, derived variant names
  - `android-summary`: combined manifest + Gradle Android app metadata
  - `gradle`: parsed Gradle basics (namespace, SDK versions, app id, version, plugin versions)
  - `dependencies`: dependency summary from Gradle files
  - `samples`, `extensions`: assets discovery
- `state`: in-memory profile state with undo/redo
- `build`
  - `plan`: scaffold build plan
  - `check`: compatibility alias for readiness check
  - `readiness`: tooling/env/wrapper readiness with blockers and warnings
  - `target`: resolve build variant and Gradle task safely
  - `assemble-simulate`: dry-run simulation for resolved assemble task
  - `signing-inspect`: read-only signing config inspection from `app/build.gradle.kts`
  - `dry-run`: Gradle dry-run wrapper (`./gradlew <task> --dry-run`)
  - `assemble`: controlled assemble wrapper (dry-run default, `--execute` to run)
  - `bundle`: controlled bundle wrapper (dry-run default, `--execute` to run)
- `extension`
  - `discover`: discover installed extension folders under assets
  - `show <extension_id>`: show extension manifest metadata and file inventory
  - `validate`: check extension compatibility assumptions from parser/project files
  - `stub <extension_id>`: generate a manifest/content/background scaffold (add `--write` to create files)
  - `plan --action install|remove --extension-id <id>`: simulate install/remove lifecycle plan only
  - `apply --action install|remove --extension-id <id>`: gated execution mode (`--execute` + `--confirm action:id`, and `--allow-destructive` for remove)
- `config`
  - `apply-profile`: transactional write of current state profile (`--execute` to persist; rollback on failure)

## Notes and safety

- `build dry-run` is intentionally non-packaging and does not produce APKs.
- `build assemble` and `build bundle` default to dry-run behavior. Real execution requires `--execute` and passes readiness checks first.
- Release builds include extra readiness checks for signing and keystore path before running.
- `build check`, `build readiness`, `build target`, `build assemble-simulate`, `build signing-inspect`, and all `inspect` commands are read-only.
- `extension plan` never performs destructive actions, even if `--mutate --execute` flags are provided.
- `extension apply remove` is blocked unless both `--execute` and `--allow-destructive` are provided with the correct `--confirm` token.
- Config writes use transactional backup+rollback to avoid partial corruption.
- State is session-scoped by default; use `config apply-profile --execute` to persist a snapshot transactionally.

## Reliability hardening (Wave B)

- Structured error taxonomy is now used for failure paths.
  - `GRADLEW_MISSING`: wrapper absent.
  - `GRADLEW_NOT_EXECUTABLE`: wrapper lacks execute permission.
  - `GRADLE_DRY_RUN_TIMEOUT`: dry-run exceeded timeout.
  - `GRADLE_INVOKE_FAILED`: wrapper could not be started.
  - `MANIFEST_MALFORMED`: manifest XML parse failure.
- Build failure responses include actionable remediation hints.
- Gradle/settings parsing now supports both Kotlin DSL (`*.kts`) and Groovy DSL (`*.gradle`).

## Migration notes

- If you consumed `build dry-run` failures as a plain `error` string, migrate to:
  - `error.code`
  - `error.message`
  - `error.hints[]`
- Existing success payload fields remain unchanged.

## Operational notes

- `build readiness` remains the preflight command before any build command in automation.
- If CI runners fail on Android checks, export `ANDROID_SDK_ROOT` in the runner environment.
- For local failures on wrapper permissions, run `chmod +x ./gradlew` once in repo root.
