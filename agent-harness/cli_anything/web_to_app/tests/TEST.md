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
  - `build_dry_run` taxonomy behavior when wrapper is missing/non-executable
- Reliability/failure-path hardening:
  - malformed AndroidManifest handling (`MANIFEST_MALFORMED`)
  - Groovy DSL parser resilience for settings/build files
- Golden-output style checks:
  - stable `android_summary` shape and critical values
  - file snapshots under `tests/golden/`

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
- Golden-output checks for critical command contracts:
  - `build target --flavor dev --build-type release` resolves to `assembleDevRelease`
  - file snapshot for `build target` JSON contract
- Source-root override path:
  - `--source-root <repo>` applied across command groups
- Failure-path checks:
  - build dry-run returns structured error taxonomy when wrapper is unavailable
- Invalid argument failure path (`state set` bad key)

## CI

- GitHub Actions workflow: `.github/workflows/agent-harness-tests.yml`
- Matrix: Python 3.11 + 3.12, with optional Java 17 setup on one leg
- Trigger scope: push/PR changes under `projects/web-to-app/agent-harness/**`

## How to run

```bash
cd agent-harness
pytest -q
# update snapshots when intentional output contracts change
pytest -q --update-goldens
```

Optional quick checks:

```bash
python -m cli_anything.web_to_app --json inspect gradle
python -m cli_anything.web_to_app --json build dry-run
```

If a consumer still expects the old `error: "..."` shape, update it to read `error.code/message/hints`.

If tests fail on golden snapshots, inspect diff first, then update with `--update-goldens` only for intentional contract changes.
