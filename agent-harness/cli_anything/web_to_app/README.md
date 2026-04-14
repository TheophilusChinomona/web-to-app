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
cli-anything-web-to-app extension discover
cli-anything-web-to-app extension show bewlycat
cli-anything-web-to-app extension validate
cli-anything-web-to-app extension stub my-extension
cli-anything-web-to-app extension stub my-extension --write
cli-anything-web-to-app extension plan --action install --extension-id my-extension --source ./my-extension.zip
cli-anything-web-to-app extension plan --action remove --extension-id bewlycat --mutate --execute
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
- `extension`
  - `discover`: discover installed extension folders under assets
  - `show <extension_id>`: show extension manifest metadata and file inventory
  - `validate`: check extension compatibility assumptions from parser/project files
  - `stub <extension_id>`: generate a manifest/content/background scaffold (add `--write` to create files)
  - `plan --action install|remove --extension-id <id>`: simulate install/remove lifecycle plan only

## Notes and safety

- `build dry-run` is intentionally non-packaging and does not produce APKs.
- `build check`, `build readiness`, `build target`, `build assemble-simulate`, `build signing-inspect`, and all `inspect` commands are read-only.
- `extension plan` never performs destructive actions, even if `--mutate --execute` flags are provided.
- State is session-scoped and not persisted to disk yet.
