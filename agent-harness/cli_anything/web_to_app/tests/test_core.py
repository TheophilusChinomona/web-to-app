from pathlib import Path

from cli_anything.web_to_app.core.state import SessionState
from cli_anything.web_to_app.utils.web_to_app_backend import WebToAppBackend
from cli_anything.web_to_app.tests.snapshot import assert_json_snapshot


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
            signingConfig = signingConfigs.release
        }
    }

    signingConfigs {
        create("release") {
            storeFile = file("keystore/release.jks")
            storePassword = "env"
            keyAlias = "release"
            keyPassword = "env"
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

    ext_dir = app_dir / "src" / "main" / "assets" / "extensions" / "demoext"
    ext_dir.mkdir(parents=True, exist_ok=True)
    (ext_dir / "manifest.json").write_text(
        """
{
  "manifest_version": 3,
  "name": "Demo Extension",
  "version": "0.1.0",
  "permissions": ["storage", "tabs"],
  "host_permissions": ["*://example.com/*"],
  "content_scripts": [
    {
      "matches": ["*://example.com/*"],
      "js": ["content.js"],
      "css": ["style.css"],
      "run_at": "document_start"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    (ext_dir / "content.js").write_text("console.log('demo');\n", encoding="utf-8")
    (ext_dir / "style.css").write_text("body{color:red;}\n", encoding="utf-8")

    parser_file = app_dir / "src" / "main" / "java" / "com" / "webtoapp" / "core" / "extension" / "ChromeExtensionParser.kt"
    parser_file.parent.mkdir(parents=True, exist_ok=True)
    parser_file.write_text(
        """
private val PERMISSION_MAP = mapOf(
    "tabs" to ModulePermission.DOM_ACCESS,
    "storage" to ModulePermission.STORAGE
)

private val UNSUPPORTED_PERMISSIONS = setOf(
    "debugger", "nativeMessaging"
)
""".strip(),
        encoding="utf-8",
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
    assert dry_run["error"]["code"] == "GRADLEW_MISSING"
    assert "gradlew not found" in dry_run["error"]["message"]


def test_build_readiness_reports_missing_env_and_tools(tmp_path, monkeypatch):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    monkeypatch.delenv("ANDROID_HOME", raising=False)

    readiness = backend.build_readiness()
    assert "checks" in readiness
    assert readiness["checks"]["app_build_exists"] is True
    assert readiness["checks"]["gradlew_exists"] is False
    assert any("Missing ./gradlew" in b for b in readiness["blockers"])
    assert any("ANDROID_SDK_ROOT" in b or "ANDROID_HOME" in b for b in readiness["blockers"])


def test_resolve_variant_target_and_simulate(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    target = backend.resolve_variant_target(flavor="dev", build_type="release")
    assert target["resolved"]["variant"] == "DevRelease"
    assert target["resolved"]["task"] == "assembleDevRelease"

    sim = backend.assemble_simulation(flavor="prod", build_type="debug")
    assert sim["target"]["resolved"]["task"] == "assembleProdDebug"
    assert sim["simulation"]["ok"] is False
    assert sim["simulation"]["error"]["code"] == "GRADLEW_MISSING"


def test_signing_config_inspection(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    signing = backend.signing_config_inspect()
    assert "release" in signing["signing_configs"]
    assert signing["build_type_signing"]["release"] == "release"
    assert signing["signing_config_properties"]["release"]["has_store_file"] is True


def test_build_variants_includes_implicit_debug_type(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    variants = backend.build_variants()
    assert "debug" in variants["build_types"]
    assert any(name.endswith("Debug") for name in variants["variant_names"])


def test_extension_discovery_metadata_validation_and_stub(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))

    discovered = backend.discover_installed_extensions()
    assert discovered["count"] == 1
    assert discovered["extensions"][0]["id"] == "demoext"

    metadata = backend.extension_metadata("demoext")
    assert metadata["ok"] is True
    assert metadata["metadata"]["name"] == "Demo Extension"
    assert metadata["metadata"]["manifest_version"] == 3

    compat = backend.validate_extension_compatibility()
    assert compat["extensions_checked"] == 1
    assert compat["extensions"][0]["supported"] is True

    stub = backend.generate_extension_stub("new-ext", manifest_version=3, write=False)
    assert stub["extension_id"] == "new-ext"
    assert "manifest.json" in stub["stub"]

    plan = backend.simulate_extension_plan(action="remove", extension_id="demoext", mutate=True, execute=True)
    assert plan["ok"] is True
    assert plan["execution_performed"] is False


def test_extension_apply_requires_execute_and_confirm(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    result = backend.apply_extension_plan(action="remove", extension_id="demoext", execute=False)
    assert result["mode"] == "dry_run"

    blocked = backend.apply_extension_plan(action="remove", extension_id="demoext", execute=True, confirm="bad")
    assert blocked["ok"] is False
    assert blocked["mode"] == "blocked"


def test_transactional_profile_config_rolls_back_on_failure(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    dry = backend.apply_profile_config_transactional(profile={"app_name": "Demo"}, execute=False)
    assert dry["mode"] == "dry_run"

    ok = backend.apply_profile_config_transactional(profile={"app_name": "Demo"}, execute=True)
    assert ok["ok"] is True

    fail = backend.apply_profile_config_transactional(
        profile={"app_name": "Broken"},
        execute=True,
        fail_after_write=True,
    )
    assert fail["ok"] is False
    profile_file = tmp_path / ".cli-anything-web-to-app" / "session-profile.json"
    content = profile_file.read_text(encoding="utf-8")
    assert "Broken" not in content


def test_build_execute_wrapper_blocks_release_without_keystore(tmp_path, monkeypatch):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    monkeypatch.setenv("ANDROID_SDK_ROOT", "/tmp/android-sdk")
    blocked = backend.build_execute_wrapper(task="bundleRelease", execute=True)
    assert blocked["ok"] is False
    assert blocked["mode"] == "blocked"


def test_manifest_malformed_returns_error_taxonomy(tmp_path):
    repo = _make_fixture_repo(tmp_path)
    manifest_path = repo / "app" / "src" / "main" / "AndroidManifest.xml"
    manifest_path.write_text("<manifest><application></manifest>", encoding="utf-8")

    backend = WebToAppBackend(repo)
    manifest = backend.manifest_info()
    assert manifest["exists"] is True
    assert manifest["error"]["code"] == "MANIFEST_MALFORMED"
    assert len(manifest["error"]["hints"]) >= 1


def test_groovy_gradle_and_settings_are_parsed(tmp_path):
    (tmp_path / "settings.gradle").write_text("rootProject.name = 'GroovyDemo'\ninclude ':app', ':feature:chat'\n", encoding="utf-8")
    (tmp_path / "build.gradle").write_text("plugins { id 'com.android.application' version '8.4.0' apply false }\n", encoding="utf-8")
    app_dir = tmp_path / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "build.gradle").write_text(
        """
android {
  compileSdkVersion 34
  defaultConfig {
    applicationId "com.example.groovy"
    minSdkVersion 24
    targetSdkVersion 34
    versionCode 2
    versionName "1.2.0"
  }
}
        """.strip(),
        encoding="utf-8",
    )

    backend = WebToAppBackend(tmp_path)
    modules = backend.list_modules()
    gradle = backend.gradle_info()
    assert modules["root_project_name"] == "GroovyDemo"
    assert "app" in modules["modules"]
    assert "feature:chat" in modules["modules"]
    assert gradle["application_id"] == "com.example.groovy"
    assert gradle["compile_sdk"] == 34
    assert gradle["min_sdk"] == 24


def test_build_dry_run_non_executable_wrapper(tmp_path):
    repo = _make_fixture_repo(tmp_path)
    gradlew = repo / "gradlew"
    gradlew.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    gradlew.chmod(0o644)

    backend = WebToAppBackend(repo)
    dry_run = backend.build_dry_run()
    assert dry_run["ok"] is False
    assert dry_run["error"]["code"] == "GRADLEW_NOT_EXECUTABLE"


def test_golden_android_summary_shape(tmp_path, update_goldens):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    payload = backend.android_resources_summary()
    assert sorted(payload.keys()) == ["android", "manifest"]
    assert payload["manifest"]["package"] == "com.example.demo"
    assert payload["android"]["application_id"] == "com.example.demo"
    assert_json_snapshot("backend_android_summary", payload, update=update_goldens)


def test_golden_variant_target_resolution_snapshot(tmp_path, update_goldens):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    payload = backend.resolve_variant_target(flavor="dev", build_type="release")
    assert payload["resolved"]["variant"] == "DevRelease"
    assert_json_snapshot("backend_variant_target_dev_release", payload, update=update_goldens)


def test_extension_metadata_missing_uses_error_taxonomy(tmp_path):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    payload = backend.extension_metadata("does-not-exist")
    assert payload["ok"] is False
    assert payload["error"]["code"] == "EXTENSION_NOT_FOUND"


def test_build_execute_blocked_uses_error_taxonomy(tmp_path, monkeypatch):
    backend = WebToAppBackend(_make_fixture_repo(tmp_path))
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    payload = backend.build_execute_wrapper(task="assembleDebug", execute=True)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "BUILD_READINESS_BLOCKED"
