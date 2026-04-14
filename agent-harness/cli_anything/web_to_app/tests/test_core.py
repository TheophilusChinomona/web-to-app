from pathlib import Path

from cli_anything.web_to_app.core.state import SessionState
from cli_anything.web_to_app.utils.web_to_app_backend import WebToAppBackend


MANIFEST = """<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\" package=\"com.example.demo\">
    <uses-permission android:name=\"android.permission.INTERNET\" />
    <application android:name=\".DemoApp\" android:label=\"@string/app_name\">
        <activity android:name=\".MainActivity\" android:exported=\"true\" />
        <service android:name=\".SyncService\" android:exported=\"false\" />
        <receiver android:name=\".BootReceiver\" android:exported=\"false\" />
    </application>
</manifest>
"""


APP_BUILD = """
android {
    namespace = "com.example.demo"
    compileSdk = 34
    flavorDimensions += listOf("env")

    buildTypes {
        debug {
            isMinifyEnabled = false
        }
        release {
            isMinifyEnabled = true
        }
    }

    productFlavors {
        create("dev") {
            dimension = "env"
        }
        create("prod") {
            dimension = "env"
        }
    }

    defaultConfig {
        applicationId = "com.example.demo"
        minSdk = 24
        targetSdk = 34
        versionCode = 7
        versionName = "0.7.0"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    testImplementation("junit:junit:4.13.2")
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
    assert manifest["service_count"] == 1
    assert manifest["receiver_count"] == 1
    assert "android.permission.INTERNET" in manifest["uses_permissions"]

    gradle = backend.gradle_info()
    assert gradle["android_namespace"] == "com.example.demo"
    assert gradle["application_id"] == "com.example.demo"
    assert gradle["compile_sdk"] == 34


def test_backend_feature_map_variants_android_summary_and_dependencies(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))

    feature_map = backend.feature_module_map()
    assert feature_map["root_project_name"] == "DemoProject"
    assert any(m["name"] == "feature:demo" for m in feature_map["feature_modules"])

    variants = backend.build_variants()
    assert variants["build_types"] == ["debug", "release"]
    assert variants["product_flavors"] == ["dev", "prod"]
    assert "DevDebug" in variants["variant_names"]
    assert "ProdRelease" in variants["variant_names"]

    android_summary = backend.android_resources_summary()
    assert android_summary["manifest"]["package"] == "com.example.demo"
    assert android_summary["android"]["application_id"] == "com.example.demo"
    assert android_summary["android"]["min_sdk"] == 24

    deps = backend.dependency_summary()
    assert deps["dependency_count"] >= 2
    assert deps["by_configuration"]["implementation"] >= 1


def test_build_check_and_dry_run_missing_gradlew(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))

    check = backend.build_check()
    assert check["gradlew_exists"] is False
    assert check["ready_for_gradle_invocation"] is False

    dry_run = backend.build_dry_run()
    assert dry_run["ok"] is False
    assert "gradlew not found" in dry_run["error"]


def test_build_variants_includes_implicit_debug_type(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    variants = backend.build_variants()
    assert "debug" in variants["build_types"]
    assert any(name.endswith("Debug") for name in variants["variant_names"])
