from pathlib import Path

from cli_anything.web_to_app.core.state import SessionState
from cli_anything.web_to_app.utils.web_to_app_backend import WebToAppBackend


MANIFEST = """<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\" package=\"com.example.demo\">
    <uses-permission android:name=\"android.permission.INTERNET\" />
    <application android:name=\".DemoApp\" android:label=\"@string/app_name\">
        <activity android:name=\".MainActivity\" android:exported=\"true\" />
    </application>
</manifest>
"""


APP_BUILD = """
android {
    namespace = "com.example.demo"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.example.demo"
        minSdk = 24
        targetSdk = 34
        versionCode = 7
        versionName = "0.7.0"
    }
}
"""


def _make_fixture_repo(tmp_path: Path) -> Path:
    (tmp_path / "settings.gradle.kts").write_text(
        'rootProject.name = "DemoProject"\ninclude(":app", ":feature:demo")\n',
        encoding="utf-8",
    )
    (tmp_path / "build.gradle.kts").write_text(
        'plugins {\n id("com.android.application") version "8.1.0" apply false\n}\n',
        encoding="utf-8",
    )
    app_dir = tmp_path / "app"
    (app_dir / "build.gradle.kts").parent.mkdir(parents=True, exist_ok=True)
    (app_dir / "build.gradle.kts").write_text(APP_BUILD, encoding="utf-8")
    (app_dir / "src" / "main").mkdir(parents=True, exist_ok=True)
    (app_dir / "src" / "main" / "AndroidManifest.xml").write_text(MANIFEST, encoding="utf-8")
    (app_dir / "src" / "main" / "kotlin" / "com" / "example").mkdir(parents=True, exist_ok=True)
    (app_dir / "src" / "main" / "kotlin" / "com" / "example" / "Main.kt").write_text(
        "package com.example.demo\nclass Main\n", encoding="utf-8"
    )
    return tmp_path


def test_state_undo_redo_cycle(tmp_path):
    state = SessionState()
    state.set_value("app_name", "Demo")
    assert state.snapshot()["app_name"] == "Demo"
    state.undo()
    assert state.snapshot()["app_name"] == ""
    state.redo()
    assert state.snapshot()["app_name"] == "Demo"


def test_backend_summary_keys(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    summary = backend.summary()
    for key in ["project", "exists", "gradle_files", "kotlin_file_count", "unit_test_count"]:
        assert key in summary


def test_backend_modules_packages_manifest_and_gradle(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))

    modules = backend.list_modules()
    assert modules["root_project_name"] == "DemoProject"
    assert "app" in modules["modules"]

    packages = backend.list_packages()
    assert "com.example.demo" in packages["packages"]

    manifest = backend.manifest_info()
    assert manifest["package"] == "com.example.demo"
    assert manifest["activity_count"] == 1
    assert "android.permission.INTERNET" in manifest["uses_permissions"]

    gradle = backend.gradle_info()
    assert gradle["android_namespace"] == "com.example.demo"
    assert gradle["application_id"] == "com.example.demo"
    assert gradle["compile_sdk"] == 34


def test_build_check_and_dry_run_missing_gradlew(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))

    check = backend.build_check()
    assert check["gradlew_exists"] is False
    assert check["ready_for_gradle_invocation"] is False

    dry_run = backend.build_dry_run()
    assert dry_run["ok"] is False
    assert "gradlew not found" in dry_run["error"]
