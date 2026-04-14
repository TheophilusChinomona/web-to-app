# Test Plan (Refine Pass)

## Unit coverage (`test_core.py`)

- Session state undo/redo cycle
- Backend summary key presence
- Fixture-based verification for:
  - module parsing from `settings.gradle.kts`
  - package extraction from Kotlin source
  - AndroidManifest parsing (package, permissions, activities)
  - Gradle metadata extraction (namespace, app id, SDK versions)
- Build wrappers:
  - `build_check` readiness flags
  - `build_dry_run` graceful behavior when wrapper is missing

## E2E coverage (`test_full_e2e.py`)

- CLI help entrypoint
- JSON output for:
  - `inspect summary`
  - `inspect modules`
  - `inspect manifest`
  - `inspect gradle`
  - `inspect tree --max-depth 1`
- State mutation path:
  - `state set app_name Demo`
- Safe build wrappers:
  - `build check`
  - `build dry-run`
- Invalid argument failure path (`state set` bad key)

## How to run

```bash
cd agent-harness
pytest -q
```

Optional quick checks:

```bash
python -m cli_anything.web_to_app --json inspect gradle
python -m cli_anything.web_to_app --json build dry-run
```
