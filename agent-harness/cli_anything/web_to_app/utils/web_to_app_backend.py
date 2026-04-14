from __future__ import annotations

import re
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
            if app is not None:
                for act in app.findall("activity"):
                    activities.append(
                        {
                            "name": act.attrib.get(f"{android_ns}name", ""),
                            "exported": act.attrib.get(f"{android_ns}exported"),
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
        gradlew = self.source_root / "gradlew"
        app_build = self.source_root / "app" / "build.gradle.kts"
        manifest = self.source_root / "app" / "src" / "main" / "AndroidManifest.xml"

        return {
            "source_root": str(self.source_root),
            "gradlew_exists": gradlew.exists(),
            "gradlew_executable": gradlew.exists() and gradlew.stat().st_mode & 0o111 != 0,
            "app_build_exists": app_build.exists(),
            "manifest_exists": manifest.exists(),
            "ready_for_gradle_invocation": gradlew.exists() and app_build.exists(),
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
