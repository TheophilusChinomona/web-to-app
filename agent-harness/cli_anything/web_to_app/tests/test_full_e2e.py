import json
import subprocess
import sys
from pathlib import Path

from cli_anything.web_to_app.tests.snapshot import assert_json_snapshot
from cli_anything.web_to_app.tests.test_core import _make_fixture_repo


def _run(*args, cwd: Path | None = None):
    return subprocess.run(
        [sys.executable, "-m", "cli_anything.web_to_app", *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )


def test_cli_entrypoint_help():
    result = _run("--help")
    assert result.returncode == 0
    assert "CLI-Anything harness for web-to-app" in result.stdout


def test_cli_json_inspect_summary():
    result = _run("--json", "inspect", "summary")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "project" in payload
    assert "gradle_files" in payload


def test_cli_json_inspect_commands():
    for command in [
        ["inspect", "modules"],
        ["inspect", "feature-map"],
        ["inspect", "manifest"],
        ["inspect", "variants"],
        ["inspect", "android-summary"],
        ["inspect", "gradle"],
        ["inspect", "dependencies"],
        ["inspect", "tree", "--max-depth", "1"],
    ]:
        result = _run("--json", *command)
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert isinstance(payload, dict)


def test_cli_json_extension_commands():
    discover = _run("--json", "extension", "discover")
    assert discover.returncode == 0
    discover_payload = json.loads(discover.stdout)
    assert "extensions" in discover_payload

    validate = _run("--json", "extension", "validate")
    assert validate.returncode == 0
    validate_payload = json.loads(validate.stdout)
    assert "parser_contract" in validate_payload

    stub = _run("--json", "extension", "stub", "e2e-ext")
    assert stub.returncode == 0
    stub_payload = json.loads(stub.stdout)
    assert stub_payload["extension_id"] == "e2e-ext"

    plan = _run(
        "--json",
        "extension",
        "plan",
        "--action",
        "install",
        "--extension-id",
        "e2e-ext",
        "--source",
        "./demo.zip",
    )
    assert plan.returncode == 0
    plan_payload = json.loads(plan.stdout)
    assert plan_payload["mode"] == "simulation_only"

    apply = _run(
        "--json",
        "extension",
        "apply",
        "--action",
        "remove",
        "--extension-id",
        "e2e-ext",
    )
    assert apply.returncode == 0
    apply_payload = json.loads(apply.stdout)
    assert apply_payload["mode"] == "dry_run"


def test_cli_state_set_and_show_json():
    result = _run("--json", "state", "set", "app_name", "Demo")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["app_name"] == "Demo"


def test_cli_build_check_and_dry_run_json():
    check = _run("--json", "build", "check")
    assert check.returncode == 0
    check_payload = json.loads(check.stdout)
    assert "ready_for_gradle_invocation" in check_payload

    dry_run = _run("--json", "build", "dry-run")
    assert dry_run.returncode == 0
    dry_run_payload = json.loads(dry_run.stdout)
    assert "ok" in dry_run_payload
    assert dry_run_payload.get("task") == "assembleDebug"


def test_cli_build_new_json_commands():
    for command in [
        ["build", "readiness"],
        ["build", "target", "--flavor", "dev", "--build-type", "release"],
        ["build", "assemble-simulate", "--build-type", "debug"],
        ["build", "signing-inspect"],
        ["build", "assemble", "--build-type", "debug"],
        ["build", "bundle", "--build-type", "release"],
        ["config", "apply-profile"],
    ]:
        result = _run("--json", *command)
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert isinstance(payload, dict)


def test_cli_golden_build_target_resolution(update_goldens):
    result = _run("--json", "build", "target", "--flavor", "dev", "--build-type", "release")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["resolved"]["variant"] == "DevRelease"
    assert payload["resolved"]["task"] == "assembleDevRelease"
    assert_json_snapshot("cli_build_target_dev_release", payload, update=update_goldens)


def test_cli_source_root_override_json(tmp_path):
    source_root = _make_fixture_repo(tmp_path)
    result = _run("--json", "--source-root", str(source_root), "inspect", "summary", cwd=source_root)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["project"] == source_root.name
    assert payload["exists"] is True


def test_cli_failure_path_for_missing_gradle_wrapper():
    result = _run("--json", "build", "dry-run", "--task", "assembleDebug")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    if "error" in payload:
        assert payload["error"]["code"] in {"GRADLEW_MISSING", "GRADLEW_NOT_EXECUTABLE"}
    else:
        # Repository may have gradlew present and fail later due to env/dependencies.
        assert isinstance(payload.get("returncode"), int)


def test_cli_build_target_human_mode():
    result = _run("build", "target", "--build-type", "debug")
    assert result.returncode == 0
    assert "assemble" in result.stdout


def test_invalid_argument_non_zero_exit():
    result = _run("state", "set", "not_a_key", "x")
    assert result.returncode != 0
