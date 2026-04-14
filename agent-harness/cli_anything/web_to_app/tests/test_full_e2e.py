import json
import subprocess
import sys


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "cli_anything.web_to_app", *args],
        capture_output=True,
        text=True,
        check=False,
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
        ["inspect", "manifest"],
        ["inspect", "gradle"],
        ["inspect", "tree", "--max-depth", "1"],
    ]:
        result = _run("--json", *command)
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert isinstance(payload, dict)


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


def test_invalid_argument_non_zero_exit():
    result = _run("state", "set", "not_a_key", "x")
    assert result.returncode != 0
