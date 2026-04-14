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
cli-anything-web-to-app build dry-run --task assembleDebug
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
  - `check`: non-destructive build readiness check
  - `dry-run`: Gradle dry-run wrapper (`./gradlew <task> --dry-run`)

## Notes and safety

- `build dry-run` is intentionally non-packaging and does not produce APKs.
- `build check` and all `inspect` commands are read-only.
- State is session-scoped and not persisted to disk yet.
