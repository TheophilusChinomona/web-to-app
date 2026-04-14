# CLI-Anything Harness Plan: web-to-app

Target source: `projects/web-to-app`
Harness root: `projects/web-to-app/agent-harness`

## First-pass scope

This first pass provides a practical CLI wrapper around repository-level operations that are useful without launching the Android GUI:

- Repository inspection and summary
- Listing sample web project templates
- Inspecting extension modules and assets
- Managing an in-session build profile state with undo/redo

## Command groups

- `inspect`:
  - `summary`: project metadata (Gradle files, source roots, test counts)
  - `samples`: sample web project templates under assets
  - `extensions`: extension module inventory
- `state`:
  - `show`: current session profile
  - `set`: set profile keys (`app_name`, `package_name`, `url`, `engine`)
  - `undo`, `redo`: state history navigation
- `build`:
  - `plan`: output a lightweight build checklist and expected artifact path

## Notes

- Backend wrappers target real repo structure (Gradle + assets), not synthetic emulation.
- A full APK build runner can be added in refine mode by wiring `./gradlew` execution and log parsing.
