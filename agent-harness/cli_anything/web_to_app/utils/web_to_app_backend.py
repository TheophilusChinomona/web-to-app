from __future__ import annotations

import os
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional


class WebToAppBackend:
    def __init__(self, source_root: Path):
        self.source_root = source_root

    def _read_text_if_exists(self, path: Path) -> str:
        if not path.exists() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")

    def summary(self) -> Dict:
        app_src = self.source_root / "app" / "src" / "main"
        test_src = self.source_root / "app" / "src" / "test"
        gradle_files = [
            str(p.relative_to(self.source_root))
            for p in self.source_root.glob("**/*.gradle.kts")
        ]
        kotlin_files = list((self.source_root / "app" / "src").glob("**/*.kt"))
        tests = list(test_src.glob("**/*Test.kt"))

        return {
            "project": self.source_root.name,
            "exists": self.source_root.exists(),
            "gradle_files": sorted(gradle_files),
            "main_assets_exists": app_src.joinpath("assets").exists(),
            "kotlin_file_count": len(kotlin_files),
            "unit_test_count": len(tests),
        }

    def project_tree(self, max_depth: int = 2) -> Dict:
        max_depth = max(1, min(max_depth, 8))
        rows: List[Dict[str, str | int]] = []

        def walk(path: Path, depth: int):
            if depth > max_depth:
                return
            try:
                children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except (PermissionError, FileNotFoundError):
                return
            for child in children:
                rel = child.relative_to(self.source_root)
                rows.append(
                    {
                        "path": str(rel),
                        "type": "dir" if child.is_dir() else "file",
                        "depth": depth,
                    }
                )
                if child.is_dir():
                    walk(child, depth + 1)

        walk(self.source_root, 1)
        return {"root": str(self.source_root), "max_depth": max_depth, "items": rows}

    def list_modules(self) -> Dict:
        settings_path = self.source_root / "settings.gradle.kts"
        content = self._read_text_if_exists(settings_path)
        includes = re.findall(r'include\(([^\)]*)\)', content)

        modules: List[str] = []
        for block in includes:
            parts = re.findall(r'"([^"]+)"', block)
            modules.extend(parts)

        if not modules and content:
            modules = re.findall(r'include\("([^"]+)"\)', content)

        normalized_modules = [m.lstrip(":") for m in modules]
        module_dirs = [m.replace(":", "/") for m in normalized_modules]

        return {
            "settings_file": str(settings_path.relative_to(self.source_root)) if settings_path.exists() else None,
            "root_project_name": self._extract_kts_assignment(content, "rootProject.name"),
            "modules": normalized_modules,
            "module_dirs": module_dirs,
        }

    def feature_module_map(self) -> Dict:
        modules_info = self.list_modules()
        extensions = self.list_extensions()

        module_rows: List[Dict[str, object]] = []
        for module in modules_info.get("modules", []):
            module_path = self.source_root / module.replace(":", "/")
            lower_name = module.lower()
            module_type = "module"
            if module == "app":
                module_type = "app"
            elif "feature" in lower_name:
                module_type = "feature"
            elif "extension" in lower_name:
                module_type = "extension_module"

            module_rows.append(
                {
                    "name": module,
                    "path": str(module_path.relative_to(self.source_root)),
                    "exists": module_path.exists(),
                    "type": module_type,
                }
            )

        extension_assets = [
            {
                "name": ext["name"],
                "path": ext["path"],
                "has_manifest": ext["has_manifest"] == "true",
                "type": "extension_asset",
            }
            for ext in extensions
        ]

        return {
            "root_project_name": modules_info.get("root_project_name"),
            "gradle_modules": module_rows,
            "extension_assets": extension_assets,
            "feature_modules": [m for m in module_rows if m["type"] == "feature"],
            "extension_related": [
                m
                for m in module_rows
                if m["type"] == "extension_module" or "extension" in str(m["name"]).lower()
            ],
        }

    def list_packages(self) -> Dict:
        kotlin_root = self.source_root / "app" / "src"
        package_names = set()

        for kt_file in kotlin_root.glob("**/*.kt"):
            text = self._read_text_if_exists(kt_file)
            match = re.search(r'^\s*package\s+([A-Za-z0-9_\.]+)\s*$', text, flags=re.MULTILINE)
            if match:
                package_names.add(match.group(1))

        return {
            "kotlin_root": str(kotlin_root.relative_to(self.source_root)) if kotlin_root.exists() else None,
            "package_count": len(package_names),
            "packages": sorted(package_names),
        }

    def manifest_info(self) -> Dict:
        manifest_path = self.source_root / "app" / "src" / "main" / "AndroidManifest.xml"
        if not manifest_path.exists():
            return {"manifest_path": None, "exists": False}

        text = self._read_text_if_exists(manifest_path)
        data: Dict[str, object] = {
            "manifest_path": str(manifest_path.relative_to(self.source_root)),
            "exists": True,
        }

        try:
            root = ET.fromstring(text)
            android_ns = "{http://schemas.android.com/apk/res/android}"
            app = root.find("application")

            uses_permissions = [
                p.attrib.get(f"{android_ns}name", "")
                for p in root.findall("uses-permission")
                if p.attrib.get(f"{android_ns}name")
            ]

            activities = []
            services = []
            receivers = []
            if app is not None:
                for act in app.findall("activity"):
                    activities.append(
                        {
                            "name": act.attrib.get(f"{android_ns}name", ""),
                            "exported": act.attrib.get(f"{android_ns}exported"),
                        }
                    )
                for svc in app.findall("service"):
                    services.append(
                        {
                            "name": svc.attrib.get(f"{android_ns}name", ""),
                            "exported": svc.attrib.get(f"{android_ns}exported"),
                        }
                    )
                for recv in app.findall("receiver"):
                    receivers.append(
                        {
                            "name": recv.attrib.get(f"{android_ns}name", ""),
                            "exported": recv.attrib.get(f"{android_ns}exported"),
                        }
                    )

            data.update(
                {
                    "package": root.attrib.get("package"),
                    "application_label": app.attrib.get(f"{android_ns}label") if app is not None else None,
                    "application_name": app.attrib.get(f"{android_ns}name") if app is not None else None,
                    "uses_permissions": uses_permissions,
                    "activity_count": len(activities),
                    "activities": activities,
                    "service_count": len(services),
                    "services": services,
                    "receiver_count": len(receivers),
                    "receivers": receivers,
                }
            )
        except ET.ParseError as exc:
            data["parse_error"] = str(exc)

        return data

    def gradle_info(self) -> Dict:
        root_build = self.source_root / "build.gradle.kts"
        app_build = self.source_root / "app" / "build.gradle.kts"
        settings = self.source_root / "settings.gradle.kts"

        settings_text = self._read_text_if_exists(settings)
        root_build_text = self._read_text_if_exists(root_build)
        app_build_text = self._read_text_if_exists(app_build)

        return {
            "settings_file": str(settings.relative_to(self.source_root)) if settings.exists() else None,
            "root_build_file": str(root_build.relative_to(self.source_root)) if root_build.exists() else None,
            "app_build_file": str(app_build.relative_to(self.source_root)) if app_build.exists() else None,
            "root_project_name": self._extract_kts_assignment(settings_text, "rootProject.name"),
            "android_namespace": self._extract_kts_assignment(app_build_text, "namespace"),
            "application_id": self._extract_kts_assignment(app_build_text, "applicationId"),
            "compile_sdk": self._extract_kts_number(app_build_text, "compileSdk"),
            "min_sdk": self._extract_kts_number(app_build_text, "minSdk"),
            "target_sdk": self._extract_kts_number(app_build_text, "targetSdk"),
            "version_code": self._extract_kts_number(app_build_text, "versionCode"),
            "version_name": self._extract_kts_assignment(app_build_text, "versionName"),
            "plugin_versions": self._extract_plugins(root_build_text),
        }

    def build_variants(self) -> Dict:
        app_build = self.source_root / "app" / "build.gradle.kts"
        app_build_text = self._read_text_if_exists(app_build)

        build_types = self._extract_named_blocks(app_build_text, "buildTypes")
        # Android app modules always have an implicit `debug` build type unless explicitly removed.
        # Keep this in the output so variant planning aligns with default Gradle tasks (e.g. assembleDebug).
        if app_build_text and "debug" not in build_types:
            build_types = sorted(set(build_types + ["debug"]))
        product_flavors = self._extract_named_blocks(app_build_text, "productFlavors")
        flavor_dimensions = self._extract_list_items_assignment(app_build_text, "flavorDimensions")

        variants: List[str] = []
        if product_flavors and build_types:
            variants = [
                f"{self._capitalize(flavor)}{self._capitalize(bt)}"
                for flavor in product_flavors
                for bt in build_types
            ]
        elif build_types:
            variants = [self._capitalize(bt) for bt in build_types]

        return {
            "app_build_file": str(app_build.relative_to(self.source_root)) if app_build.exists() else None,
            "build_types": build_types,
            "product_flavors": product_flavors,
            "flavor_dimensions": flavor_dimensions,
            "variant_names": variants,
        }

    def android_resources_summary(self) -> Dict:
        manifest = self.manifest_info()
        gradle = self.gradle_info()

        return {
            "manifest": {
                "path": manifest.get("manifest_path"),
                "exists": manifest.get("exists", False),
                "package": manifest.get("package"),
                "permissions": manifest.get("uses_permissions", []),
                "activities": manifest.get("activities", []),
                "services": manifest.get("services", []),
                "receivers": manifest.get("receivers", []),
            },
            "android": {
                "application_id": gradle.get("application_id"),
                "namespace": gradle.get("android_namespace"),
                "min_sdk": gradle.get("min_sdk"),
                "target_sdk": gradle.get("target_sdk"),
                "version_code": gradle.get("version_code"),
                "version_name": gradle.get("version_name"),
            },
        }

    def dependency_summary(self) -> Dict:
        gradle_files = sorted(self.source_root.glob("**/*.gradle.kts")) + sorted(self.source_root.glob("**/*.gradle"))
        dependency_entries: List[Dict[str, str]] = []

        for gradle_file in gradle_files:
            rel_path = str(gradle_file.relative_to(self.source_root))
            text = self._read_text_if_exists(gradle_file)
            for configuration, gav in re.findall(
                r"\b(implementation|api|kapt|ksp|compileOnly|runtimeOnly|testImplementation|androidTestImplementation|debugImplementation|releaseImplementation)\s*\(\s*[\"']([^\"']+)[\"']\s*\)",
                text,
            ):
                dependency_entries.append(
                    {
                        "file": rel_path,
                        "configuration": configuration,
                        "notation": gav,
                    }
                )

        configuration_counts: Dict[str, int] = {}
        for dep in dependency_entries:
            configuration_counts[dep["configuration"]] = configuration_counts.get(dep["configuration"], 0) + 1

        return {
            "files_scanned": [str(p.relative_to(self.source_root)) for p in gradle_files],
            "dependency_count": len(dependency_entries),
            "by_configuration": configuration_counts,
            "dependencies": dependency_entries,
        }

    def list_samples(self) -> List[Dict[str, str]]:
        base = self.source_root / "app" / "src" / "main" / "assets" / "sample_projects"
        if not base.exists():
            return []
        rows = []
        for d in sorted([x for x in base.iterdir() if x.is_dir()]):
            markers = []
            for marker in ["package.json", "requirements.txt", "composer.json", "go.mod", "mkdocs.yml", "wp-config.php"]:
                if (d / marker).exists() or any(d.glob(f"**/{marker}")):
                    markers.append(marker)
            rows.append({
                "name": d.name,
                "path": str(d.relative_to(self.source_root)),
                "detected_markers": ",".join(markers) if markers else "static",
            })
        return rows

    def list_extensions(self) -> List[Dict[str, str]]:
        base = self.source_root / "app" / "src" / "main" / "assets" / "extensions"
        if not base.exists():
            return []
        items = []
        for d in sorted([x for x in base.iterdir() if x.is_dir()]):
            manifest = d / "manifest.json"
            items.append(
                {
                    "name": d.name,
                    "path": str(d.relative_to(self.source_root)),
                    "has_manifest": str(manifest.exists()).lower(),
                }
            )
        return items

    def discover_installed_extensions(self) -> Dict:
        base = self.source_root / "app" / "src" / "main" / "assets" / "extensions"
        if not base.exists():
            return {
                "extensions_root": str(base.relative_to(self.source_root)),
                "exists": False,
                "count": 0,
                "extensions": [],
            }

        rows = []
        for ext_dir in sorted([x for x in base.iterdir() if x.is_dir()]):
            meta = self._load_extension_manifest(ext_dir)
            rows.append(
                {
                    "id": ext_dir.name,
                    "path": str(ext_dir.relative_to(self.source_root)),
                    "manifest_exists": meta.get("manifest_exists", False),
                    "name": meta.get("name"),
                    "version": meta.get("version"),
                    "manifest_version": meta.get("manifest_version"),
                    "content_script_count": meta.get("content_script_count", 0),
                }
            )

        return {
            "extensions_root": str(base.relative_to(self.source_root)),
            "exists": True,
            "count": len(rows),
            "extensions": rows,
        }

    def extension_metadata(self, extension_id: str) -> Dict:
        ext_dir = self.source_root / "app" / "src" / "main" / "assets" / "extensions" / extension_id
        if not ext_dir.exists() or not ext_dir.is_dir():
            return {
                "ok": False,
                "extension_id": extension_id,
                "error": "extension not found",
            }

        meta = self._load_extension_manifest(ext_dir)
        files = [
            str(p.relative_to(ext_dir))
            for p in sorted(ext_dir.glob("**/*"))
            if p.is_file()
        ]

        return {
            "ok": True,
            "extension_id": extension_id,
            "path": str(ext_dir.relative_to(self.source_root)),
            "metadata": meta,
            "file_count": len(files),
            "js_file_count": len([p for p in files if p.endswith(".js")]),
            "css_file_count": len([p for p in files if p.endswith(".css")]),
            "sample_files": files[:20],
        }

    def validate_extension_compatibility(self) -> Dict:
        parser_path = self.source_root / "app" / "src" / "main" / "java" / "com" / "webtoapp" / "core" / "extension" / "ChromeExtensionParser.kt"
        parser_text = self._read_text_if_exists(parser_path)

        supported_permissions = sorted(
            set(re.findall(r'"([A-Za-z][A-Za-z0-9]+)"\s+to\s+ModulePermission\.', parser_text))
        )
        unsupported_permissions = sorted(
            set(re.findall(r'"([A-Za-z][A-Za-z0-9]+)"', self._extract_set_block(parser_text, "UNSUPPORTED_PERMISSIONS")))
        )

        extension_results = []
        for ext in self.discover_installed_extensions().get("extensions", []):
            ext_id = ext["id"]
            detail = self.extension_metadata(ext_id)
            meta = detail.get("metadata", {}) if detail.get("ok") else {}

            permissions = meta.get("permissions", []) or []
            host_permissions = meta.get("host_permissions", []) or []
            optional_permissions = meta.get("optional_permissions", []) or []
            api_permissions = [
                p for p in permissions + host_permissions + optional_permissions
                if isinstance(p, str) and "://" not in p and p != "<all_urls>"
            ]
            unsupported_used = sorted([p for p in api_permissions if p in unsupported_permissions])
            unknown_permissions = sorted([p for p in api_permissions if p not in supported_permissions and p not in unsupported_permissions])

            missing_content_files = []
            for cs in meta.get("content_scripts", []) or []:
                for key in ["js", "css"]:
                    for raw_path in cs.get(key, []) or []:
                        norm = self._normalize_manifest_path(raw_path)
                        if not (self.source_root / "app" / "src" / "main" / "assets" / "extensions" / ext_id / norm).exists():
                            missing_content_files.append(norm)

            extension_results.append(
                {
                    "extension_id": ext_id,
                    "name": meta.get("name"),
                    "manifest_version": meta.get("manifest_version"),
                    "supported": len(unsupported_used) == 0,
                    "unsupported_permissions_used": unsupported_used,
                    "unknown_permissions": unknown_permissions,
                    "missing_content_files": sorted(set(missing_content_files)),
                    "warnings": meta.get("warnings", []),
                }
            )

        return {
            "parser_contract": {
                "manifest_versions_supported": [2, 3],
                "supported_permission_keys": supported_permissions,
                "unsupported_permission_keys": unsupported_permissions,
                "source": str(parser_path.relative_to(self.source_root)) if parser_path.exists() else None,
            },
            "extensions_checked": len(extension_results),
            "extensions": extension_results,
        }

    def generate_extension_stub(self, extension_id: str, manifest_version: int = 3, write: bool = False, force: bool = False) -> Dict:
        ext_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", extension_id.strip()).strip("-") or "new-extension"
        base = self.source_root / "app" / "src" / "main" / "assets" / "extensions" / ext_id

        manifest: Dict[str, object] = {
            "manifest_version": int(manifest_version),
            "name": ext_id,
            "version": "0.1.0",
            "description": "TODO: describe extension behavior",
            "permissions": ["storage"],
            "host_permissions": ["<all_urls>"],
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "css": ["style.css"],
                    "run_at": "document_idle",
                }
            ],
            "icons": {"16": "assets/icon-16.png", "48": "assets/icon-48.png", "128": "assets/icon-128.png"},
        }
        if int(manifest_version) >= 3:
            manifest["background"] = {"service_worker": "background/index.js", "type": "module"}
        else:
            manifest["background"] = {"scripts": ["background/index.js"], "persistent": False}

        files = {
            "manifest.json": json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            "content.js": "// TODO: add content script\n",
            "style.css": "/* TODO: add extension styles */\n",
            "background/index.js": "// TODO: add background logic\n",
            "assets/.keep": "",
        }

        writes = []
        errors = []
        if write:
            for rel, content in files.items():
                path = base / rel
                if path.exists() and not force:
                    errors.append(f"exists: {rel} (use --force to overwrite)")
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                writes.append(str(path.relative_to(self.source_root)))

        return {
            "extension_id": ext_id,
            "manifest_version": int(manifest_version),
            "write_requested": write,
            "wrote_files": writes,
            "write_errors": errors,
            "stub": files,
            "target_root": str(base.relative_to(self.source_root)),
        }

    def simulate_extension_plan(
        self,
        action: str,
        extension_id: str,
        source: Optional[str] = None,
        mutate: bool = False,
        execute: bool = False,
    ) -> Dict:
        normalized_action = action.lower().strip()
        ext_id = extension_id.strip()
        target = self.source_root / "app" / "src" / "main" / "assets" / "extensions" / ext_id

        if normalized_action not in {"install", "remove"}:
            return {"ok": False, "error": "action must be 'install' or 'remove'"}

        if normalized_action == "install":
            preconditions = [{
                "check": "target_not_exists",
                "ok": not target.exists(),
                "path": str(target.relative_to(self.source_root)),
            }]
            steps = [
                "Validate extension source archive/folder",
                f"Extract files into {target.relative_to(self.source_root)}",
                "Parse manifest.json and content_scripts",
                "Run extension compatibility validation",
            ]
        else:
            preconditions = [{
                "check": "target_exists",
                "ok": target.exists(),
                "path": str(target.relative_to(self.source_root)),
            }]
            steps = [
                "Resolve extension module references",
                "Archive extension folder for rollback",
                f"Remove {target.relative_to(self.source_root)}",
                "Re-run extension discovery/validation",
            ]

        return {
            "ok": True,
            "mode": "simulation_only",
            "action": normalized_action,
            "extension_id": ext_id,
            "source": source,
            "mutate_flag": mutate,
            "execute_flag": execute,
            "execution_performed": False,
            "execution_blocked_reason": "This harness only simulates extension lifecycle actions. No destructive action is executed.",
            "preconditions": preconditions,
            "plan_steps": steps,
        }

    def build_plan(self, profile: Dict[str, str]) -> Dict:
        return {
            "profile": profile,
            "steps": [
                "Validate app_name/package_name/url",
                "Sync gradle wrapper and dependencies",
                "Run ./gradlew assembleDebug",
                "Collect APK from app/build/outputs/apk/debug/",
            ],
            "expected_artifact": "app/build/outputs/apk/debug/app-debug.apk",
        }

    def build_check(self) -> Dict:
        return self.build_readiness()

    def build_readiness(self) -> Dict:
        gradlew = self.source_root / "gradlew"
        app_build = self.source_root / "app" / "build.gradle.kts"
        manifest = self.source_root / "app" / "src" / "main" / "AndroidManifest.xml"
        gradle_wrapper_jar = self.source_root / "gradle" / "wrapper" / "gradle-wrapper.jar"
        gradle_wrapper_properties = self.source_root / "gradle" / "wrapper" / "gradle-wrapper.properties"

        java_bin = shutil.which("java")
        adb_bin = shutil.which("adb")
        sdk_root = (
            os.environ.get("ANDROID_SDK_ROOT")
            or os.environ.get("ANDROID_HOME")
            or ""
        )

        checks = {
            "gradlew_exists": gradlew.exists(),
            "gradlew_executable": gradlew.exists() and gradlew.stat().st_mode & 0o111 != 0,
            "gradle_wrapper_jar_exists": gradle_wrapper_jar.exists(),
            "gradle_wrapper_properties_exists": gradle_wrapper_properties.exists(),
            "app_build_exists": app_build.exists(),
            "manifest_exists": manifest.exists(),
            "java_available": bool(java_bin),
            "android_sdk_available": bool(sdk_root),
            "adb_available": bool(adb_bin),
        }

        blockers = []
        if not checks["gradlew_exists"]:
            blockers.append("Missing ./gradlew")
        if not checks["app_build_exists"]:
            blockers.append("Missing app/build.gradle.kts")
        if not checks["java_available"]:
            blockers.append("Java is not on PATH")
        if not checks["android_sdk_available"]:
            blockers.append("ANDROID_SDK_ROOT or ANDROID_HOME is not set")

        warnings = []
        if checks["gradlew_exists"] and not checks["gradlew_executable"]:
            warnings.append("./gradlew is not executable")
        if not checks["gradle_wrapper_jar_exists"]:
            warnings.append("gradle/wrapper/gradle-wrapper.jar missing")
        if not checks["gradle_wrapper_properties_exists"]:
            warnings.append("gradle/wrapper/gradle-wrapper.properties missing")
        if not checks["manifest_exists"]:
            warnings.append("AndroidManifest.xml missing")
        if not checks["adb_available"]:
            warnings.append("adb is not on PATH (device/emulator checks unavailable)")

        ready = len(blockers) == 0
        return {
            "source_root": str(self.source_root),
            "gradlew_exists": checks["gradlew_exists"],
            "gradlew_executable": checks["gradlew_executable"],
            "app_build_exists": checks["app_build_exists"],
            "manifest_exists": checks["manifest_exists"],
            "ready_for_gradle_invocation": checks["gradlew_exists"] and checks["app_build_exists"],
            "checks": checks,
            "tools": {
                "java": java_bin,
                "adb": adb_bin,
            },
            "env": {
                "ANDROID_SDK_ROOT": os.environ.get("ANDROID_SDK_ROOT"),
                "ANDROID_HOME": os.environ.get("ANDROID_HOME"),
                "JAVA_HOME": os.environ.get("JAVA_HOME"),
            },
            "ready_for_build": ready,
            "blockers": blockers,
            "warnings": warnings,
        }

    def resolve_variant_target(
        self,
        variant: Optional[str] = None,
        flavor: Optional[str] = None,
        build_type: str = "debug",
    ) -> Dict:
        variants = self.build_variants()
        known_build_types = variants.get("build_types", [])
        known_flavors = variants.get("product_flavors", [])

        if variant:
            normalized_variant = variant[:1].upper() + variant[1:]
        elif flavor:
            normalized_variant = f"{self._capitalize(flavor)}{self._capitalize(build_type)}"
        else:
            normalized_variant = self._capitalize(build_type)

        task = f"assemble{normalized_variant}"
        known_variant_names = variants.get("variant_names", [])
        variant_known = not known_variant_names or normalized_variant in known_variant_names

        warnings = []
        if build_type and known_build_types and build_type not in known_build_types:
            warnings.append(f"Unknown build type '{build_type}'")
        if flavor and known_flavors and flavor not in known_flavors:
            warnings.append(f"Unknown flavor '{flavor}'")
        if not variant_known:
            warnings.append(f"Variant '{normalized_variant}' not in discovered variant list")

        return {
            "requested": {
                "variant": variant,
                "flavor": flavor,
                "build_type": build_type,
            },
            "resolved": {
                "variant": normalized_variant,
                "task": task,
            },
            "known": {
                "build_types": known_build_types,
                "product_flavors": known_flavors,
                "variant_names": known_variant_names,
            },
            "warnings": warnings,
        }

    def assemble_simulation(
        self,
        variant: Optional[str] = None,
        flavor: Optional[str] = None,
        build_type: str = "debug",
    ) -> Dict:
        target = self.resolve_variant_target(variant=variant, flavor=flavor, build_type=build_type)
        task = target["resolved"]["task"]
        dry_run = self.build_dry_run(task=task)
        return {
            "target": target,
            "simulation": dry_run,
        }

    def signing_config_inspect(self) -> Dict:
        app_build = self.source_root / "app" / "build.gradle.kts"
        text = self._read_text_if_exists(app_build)
        if not text:
            return {
                "app_build_file": str(app_build.relative_to(self.source_root)) if app_build.exists() else None,
                "exists": app_build.exists(),
                "signing_configs": [],
                "build_type_signing": {},
                "warnings": ["Cannot inspect signing config without app/build.gradle.kts"],
            }

        signing_block = self._extract_block_content(text, "signingConfigs") or ""
        signing_names = re.findall(r"\bcreate\(\s*[\"']([^\"']+)[\"']\s*\)", signing_block)
        if not signing_names:
            signing_names = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\{", signing_block)
        signing_names = sorted(set(signing_names))

        property_flags = {}
        for name in signing_names:
            created_pattern = re.search(
                rf"create\(\s*[\"']{re.escape(name)}[\"']\s*\)\s*\{{",
                signing_block,
            )
            cfg_block = ""
            if created_pattern:
                cfg_block = self._extract_brace_content_at(signing_block, created_pattern.end() - 1) or ""
            else:
                cfg_block = self._extract_block_content(signing_block, name) or ""
            property_flags[name] = {
                "has_store_file": bool(re.search(r"\bstoreFile\b", cfg_block)),
                "has_store_password": bool(re.search(r"\bstorePassword\b", cfg_block)),
                "has_key_alias": bool(re.search(r"\bkeyAlias\b", cfg_block)),
                "has_key_password": bool(re.search(r"\bkeyPassword\b", cfg_block)),
            }

        build_types_block = self._extract_block_content(text, "buildTypes") or ""
        build_type_signing = {}
        for bt in self._extract_named_blocks(text, "buildTypes"):
            bt_block = self._extract_block_content(build_types_block, bt) or ""
            m = re.search(r"\bsigningConfig\s*=\s*signingConfigs\.([A-Za-z0-9_]+)", bt_block)
            build_type_signing[bt] = m.group(1) if m else None

        warnings = []
        if not signing_names:
            warnings.append("No explicit signingConfigs block discovered")

        return {
            "app_build_file": str(app_build.relative_to(self.source_root)) if app_build.exists() else None,
            "exists": app_build.exists(),
            "signing_configs": signing_names,
            "signing_config_properties": property_flags,
            "build_type_signing": build_type_signing,
            "read_only": True,
            "warnings": warnings,
        }

    def build_dry_run(self, task: str = "assembleDebug") -> Dict:
        gradlew = self.source_root / "gradlew"
        if not gradlew.exists():
            return {
                "ok": False,
                "task": task,
                "command": ["./gradlew", task, "--dry-run", "--console=plain"],
                "error": "gradlew not found",
            }

        cmd = ["./gradlew", task, "--dry-run", "--console=plain"]
        proc = subprocess.run(
            cmd,
            cwd=self.source_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "task": task,
            "command": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-12000:],
            "stderr": proc.stderr[-12000:],
        }

    def _extract_kts_assignment(self, text: str, key: str) -> Optional[str]:
        if not text:
            return None
        m = re.search(rf"{re.escape(key)}\s*=\s*\"([^\"]+)\"", text)
        return m.group(1) if m else None

    def _extract_kts_number(self, text: str, key: str) -> Optional[int]:
        if not text:
            return None
        m = re.search(rf"{re.escape(key)}\s*=\s*(\d+)", text)
        if not m:
            return None
        return int(m.group(1))

    def _extract_plugins(self, text: str) -> List[Dict[str, str]]:
        if not text:
            return []
        rows = []
        for plugin_id, version in re.findall(r'id\("([^"]+)"\)\s+version\s+"([^"]+)"', text):
            rows.append({"id": plugin_id, "version": version})
        return rows

    def _extract_named_blocks(self, text: str, block_name: str) -> List[str]:
        if not text:
            return []
        block = self._extract_block_content(text, block_name)
        if block is None:
            return []
        names = re.findall(r"\bcreate\(\s*[\"']([^\"']+)[\"']\s*\)", block)
        if not names:
            names = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\{", block)
        return sorted(set(names))

    def _extract_list_items_assignment(self, text: str, key: str) -> List[str]:
        if not text:
            return []
        match = re.search(rf"{re.escape(key)}\s*\+?=\s*listOf\(([^\)]*)\)", text)
        if not match:
            match = re.search(rf"{re.escape(key)}\s*=\s*listOf\(([^\)]*)\)", text)
        if not match:
            return []
        return re.findall(r"[\"']([^\"']+)[\"']", match.group(1))

    def _capitalize(self, value: str) -> str:
        return value[:1].upper() + value[1:] if value else value

    def _extract_block_content(self, text: str, block_name: str) -> Optional[str]:
        start_match = re.search(rf"\b{re.escape(block_name)}\s*\{{", text)
        if not start_match:
            return None
        return self._extract_brace_content_at(text, start_match.end() - 1)

    def _extract_brace_content_at(self, text: str, brace_idx: int) -> Optional[str]:
        start = brace_idx
        depth = 0
        i = start
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start + 1 : i]
            i += 1
        return None

    def _extract_set_block(self, text: str, set_name: str) -> str:
        if not text:
            return ""
        match = re.search(rf"\b{re.escape(set_name)}\s*=\s*setOf\((.*?)\)", text, flags=re.DOTALL)
        return match.group(1) if match else ""

    def _load_extension_manifest(self, extension_dir: Path) -> Dict:
        manifest_path = extension_dir / "manifest.json"
        if not manifest_path.exists():
            return {
                "manifest_exists": False,
                "warnings": ["manifest.json missing"],
            }

        try:
            data = json.loads(self._read_text_if_exists(manifest_path))
        except json.JSONDecodeError as exc:
            return {
                "manifest_exists": True,
                "parse_error": str(exc),
                "warnings": ["manifest.json is invalid JSON"],
            }

        content_scripts = data.get("content_scripts") if isinstance(data.get("content_scripts"), list) else []
        warnings = []
        for idx, cs in enumerate(content_scripts):
            if not isinstance(cs, dict):
                warnings.append(f"content_scripts[{idx}] is not an object")

        return {
            "manifest_exists": True,
            "name": data.get("name"),
            "version": data.get("version"),
            "description": data.get("description"),
            "manifest_version": data.get("manifest_version"),
            "permissions": data.get("permissions", []),
            "host_permissions": data.get("host_permissions", []),
            "optional_permissions": data.get("optional_permissions", []),
            "background": data.get("background", {}),
            "content_scripts": content_scripts,
            "content_script_count": len(content_scripts),
            "warnings": warnings,
        }

    def _normalize_manifest_path(self, value: str) -> str:
        return value.strip().lstrip("./")
