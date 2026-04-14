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
    assert "gradlew not found" in dry_run["error"]


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
    assert "gradlew not found" in sim["simulation"]["error"]


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
