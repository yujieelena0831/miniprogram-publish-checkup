#!/usr/bin/env python3
"""Static preflight for a WeChat Mini Program project."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SKIP_DIRS = {".git", "node_modules", "miniprogram_npm"}
SCRIPT_EXTENSIONS = (".js", ".ts")
REQUIRED_VIEW_EXTENSIONS = (".json", ".wxml", ".wxss")
SECRET_NAME_RE = re.compile(
    r"(^\.env(?:\.|$)|private.?key|upload.?key|secret|\.pem$|\.p12$|\.pfx$)",
    re.IGNORECASE,
)
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
PRIVACY_TOKENS = {
    "wx.chooseAddress": "address",
    "wx.chooseContact": "contacts",
    "wx.chooseImage": "selected images",
    "wx.saveImageToPhotosAlbum": "photo album writes",
    "wx.chooseMedia": "selected media",
    "wx.chooseMessageFile": "selected files",
    "wx.getClipboardData": "clipboard",
    "wx.getFuzzyLocation": "approximate location",
    "wx.getLocation": "location",
    "wx.chooseLocation": "selected location",
    "wx.openLocation": "location display",
    "wx.getUserProfile": "user profile",
    "wx.getWeRunData": "fitness data",
    "wx.getInvoiceTitle": "invoice title",
    "wx.startRecord": "microphone",
    "RecorderManager": "microphone",
    "camera": "camera",
    "getPhoneNumber": "phone number",
}

CAPABILITY_TOKENS = {
    "payments": ("wx.requestPayment", "requestPayment"),
    "user-content-or-upload": ("wx.uploadFile", "chooseImage", "chooseMedia", "chooseMessageFile"),
    "location": ("getLocation", "chooseLocation", "openLocation", "map"),
    "camera-or-scan": ("camera", "wx.scanCode"),
    "microphone-or-audio": ("startRecord", "RecorderManager", "live-pusher"),
    "subscriptions": ("requestSubscribeMessage",),
    "customer-service": ("open-type=\"contact\"", "open-type='contact'"),
    "sharing": ("onShareAppMessage", "open-type=\"share\"", "open-type='share'"),
    "live-or-video": ("live-player", "live-pusher", "video"),
}
INSECURE_ENDPOINT_RE = re.compile(r"(?:http://|https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)|\b(?:localhost|127\.0\.0\.1):\d+)", re.IGNORECASE)
EMBEDDED_SECRET_RE = re.compile(
    r"(?:secret(?:id|key)?|api[_-]?key|private[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    re.IGNORECASE,
)


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str = ""


def read_json(path: Path, findings: list[Finding], required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            findings.append(Finding("BLOCKER", "missing-json", "Required JSON file is missing.", str(path)))
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        findings.append(Finding("BLOCKER", "invalid-json", f"Cannot parse JSON: {exc}", str(path)))
        return {}
    if not isinstance(value, dict):
        findings.append(Finding("BLOCKER", "invalid-json-shape", "Expected a JSON object.", str(path)))
        return {}
    return value


def within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def normalize_route(value: str) -> str:
    return str(value or "").strip().strip("/")


def require_companion_files(base: Path, label: str, findings: list[Finding]) -> None:
    for extension in REQUIRED_VIEW_EXTENSIONS:
        path = base.with_suffix(extension)
        if not path.exists():
            findings.append(Finding("BLOCKER", f"missing-{label}-file", f"Missing {label} companion file {extension}.", str(path)))
    if not any(base.with_suffix(extension).exists() for extension in SCRIPT_EXTENSIONS):
        findings.append(Finding("BLOCKER", f"missing-{label}-script", f"Missing {label} script (.js or .ts).", str(base)))


def resolve_component(value: str, owner_json: Path, source_root: Path) -> Path | None:
    if not value or value.startswith(("plugin://", "ext://", "dynamicLib://")):
        return None
    if value.startswith("/"):
        return source_root / value.lstrip("/")
    if value.startswith("."):
        return (owner_json.parent / value).resolve()
    return None


def inspect_components(config: dict[str, Any], owner_json: Path, source_root: Path, findings: list[Finding]) -> None:
    components = config.get("usingComponents", {})
    if not isinstance(components, dict):
        findings.append(Finding("WARNING", "invalid-components", "usingComponents should be an object.", str(owner_json)))
        return
    for name, value in components.items():
        if not isinstance(value, str):
            findings.append(Finding("WARNING", "invalid-component-path", f"Component {name} has a non-string path.", str(owner_json)))
            continue
        base = resolve_component(value, owner_json, source_root)
        if base is None:
            continue
        require_companion_files(base, "component", findings)


def load_ignores(config: dict[str, Any], root_value: str) -> list[tuple[str, str]]:
    ignores = config.get("packOptions", {}).get("ignore", [])
    result: list[tuple[str, str]] = []
    if not isinstance(ignores, list):
        return result
    for item in ignores:
        if not isinstance(item, dict) or not item.get("value"):
            continue
        value = str(item["value"]).strip().strip("/")
        normalized_root = root_value.strip("/")
        if normalized_root and normalized_root != "." and value.startswith(normalized_root + "/"):
            value = value[len(normalized_root) + 1 :]
        result.append((value, str(item.get("type") or "file")))
    return result


def is_ignored(rel: Path, ignores: list[tuple[str, str]]) -> bool:
    value = rel.as_posix()
    for ignored, kind in ignores:
        if kind == "folder" and (value == ignored or value.startswith(ignored + "/")):
            return True
        if kind != "folder" and value == ignored:
            return True
    return False


def iter_source_files(root: Path, ignores: list[tuple[str, str]] | None = None):
    ignores = ignores or []
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        rel_current = current_path.relative_to(root)
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS and not is_ignored(rel_current / name, ignores)]
        for name in files:
            path = current_path / name
            if not is_ignored(path.relative_to(root), ignores):
                yield path


def scan_sources(source_root: Path, findings: list[Finding], ignores: list[tuple[str, str]]) -> tuple[str, list[str], list[str]]:
    cloudbase = False
    custom_backend = False
    privacy_hits: set[str] = set()
    secret_hits: list[str] = []
    insecure_endpoint_hits: list[str] = []
    embedded_secret_hits: list[str] = []
    capability_hits: set[str] = set()
    junk_hits: list[str] = []

    for path in iter_source_files(source_root):
        rel = path.relative_to(source_root).as_posix()
        if SECRET_NAME_RE.search(path.name):
            secret_hits.append(rel)
        if path.name in JUNK_NAMES or "__MACOSX" in path.parts:
            junk_hits.append(rel)
    for path in iter_source_files(source_root, ignores):
        rel = path.relative_to(source_root).as_posix()
        if path.suffix.lower() not in {".js", ".ts", ".wxml", ".json"}:
            continue
        try:
            if path.stat().st_size > 2 * 1024 * 1024:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "wx.cloud" in text:
            cloudbase = True
        if any(token in text for token in ("wx.request", "wx.uploadFile", "wx.downloadFile", "wx.connectSocket")):
            custom_backend = True
        for token, category in PRIVACY_TOKENS.items():
            if token in text:
                privacy_hits.add(category)
        for capability, tokens in CAPABILITY_TOKENS.items():
            if any(token in text for token in tokens):
                capability_hits.add(capability)
        if INSECURE_ENDPOINT_RE.search(text):
            insecure_endpoint_hits.append(rel)
        if EMBEDDED_SECRET_RE.search(text):
            embedded_secret_hits.append(rel)

    for rel in secret_hits[:20]:
        findings.append(Finding("WARNING", "possible-secret-file", "Possible private credential or environment file; confirm it is excluded from upload and source handoff.", rel))
    if len(secret_hits) > 20:
        findings.append(Finding("WARNING", "possible-secret-files-more", f"{len(secret_hits) - 20} additional possible secret files were omitted from this report."))
    for rel in junk_hits[:20]:
        findings.append(Finding("WARNING", "archive-junk", "Remove operating-system metadata from the release handoff and upload package.", rel))
    if privacy_hits:
        findings.append(Finding("UNKNOWN", "privacy-inventory", "Confirm the platform privacy guide and consent flow cover: " + ", ".join(sorted(privacy_hits))))
    for rel in insecure_endpoint_hits[:20]:
        findings.append(Finding("BLOCKER", "insecure-or-local-endpoint", "A release package references HTTP or a local development endpoint; replace it with the intended production HTTPS service.", rel))
    for rel in embedded_secret_hits[:20]:
        findings.append(Finding("BLOCKER", "embedded-secret", "A possible hard-coded credential is present in client-readable source; remove and rotate it.", rel))
    if capability_hits:
        findings.append(Finding("UNKNOWN", "scenario-compliance", "Apply current platform, privacy, qualification, and operational checks for detected capabilities: " + ", ".join(sorted(capability_hits))))

    if cloudbase and custom_backend:
        mode = "hybrid"
    elif cloudbase:
        mode = "cloudbase"
    elif custom_backend:
        mode = "custom-backend"
    else:
        mode = "local-only-or-undetected"
    return mode, sorted(privacy_hits), sorted(capability_hits)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit WeChat Mini Program project structure before preview or release.")
    parser.add_argument("project", nargs="?", default=".", help="Directory containing project.config.json")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    findings: list[Finding] = []
    config_path = project / "project.config.json"
    config = read_json(config_path, findings)

    root_value = str(config.get("miniprogramRoot") or ".")
    source_root = (project / root_value).resolve()
    if not within(source_root, project):
        findings.append(Finding("BLOCKER", "invalid-source-root", "miniprogramRoot resolves outside the project directory.", root_value))
    if not source_root.is_dir():
        findings.append(Finding("BLOCKER", "missing-source-root", "Mini Program source root does not exist.", str(source_root)))

    appid = str(config.get("appid") or "").strip()
    if not appid or appid in {"touristappid", "wx0000000000000000"}:
        findings.append(Finding("BLOCKER", "missing-appid", "A real AppID is required for preview and upload.", str(config_path)))
    if config.get("setting", {}).get("urlCheck") is False:
        findings.append(Finding("WARNING", "domain-check-disabled", "Developer Tools domain validation is disabled; production domains still require manual verification.", str(config_path)))

    app_json_path = source_root / "app.json"
    app = read_json(app_json_path, findings)
    if not any((source_root / f"app{extension}").exists() for extension in SCRIPT_EXTENSIONS):
        findings.append(Finding("BLOCKER", "missing-app-script", "Missing app entry script (.js or .ts).", str(source_root)))
    inspect_components(app, app_json_path, source_root, findings)

    routes: list[tuple[str, Path]] = []
    top_routes: set[str] = set()
    pages = app.get("pages", [])
    if not isinstance(pages, list) or not pages:
        findings.append(Finding("BLOCKER", "missing-pages", "app.json must declare at least one page.", str(app_json_path)))
        pages = []
    for raw in pages:
        route = normalize_route(str(raw))
        if not route:
            continue
        top_routes.add(route)
        routes.append((route, source_root / route))

    subpackages = app.get("subPackages", app.get("subpackages", []))
    if subpackages and not isinstance(subpackages, list):
        findings.append(Finding("BLOCKER", "invalid-subpackages", "subPackages should be an array.", str(app_json_path)))
        subpackages = []
    for package in subpackages or []:
        if not isinstance(package, dict):
            findings.append(Finding("BLOCKER", "invalid-subpackage", "Each subpackage should be an object.", str(app_json_path)))
            continue
        package_root = normalize_route(str(package.get("root") or ""))
        package_pages = package.get("pages", [])
        if not package_root or not isinstance(package_pages, list):
            findings.append(Finding("BLOCKER", "invalid-subpackage-shape", "Subpackage root/pages are incomplete.", str(app_json_path)))
            continue
        for raw in package_pages:
            route = normalize_route(f"{package_root}/{normalize_route(str(raw))}")
            routes.append((route, source_root / route))

    seen: set[str] = set()
    for route, base in routes:
        if route in seen:
            findings.append(Finding("WARNING", "duplicate-route", "Route is declared more than once.", route))
            continue
        seen.add(route)
        require_companion_files(base, "page", findings)
        page_json_path = base.with_suffix(".json")
        page_config = read_json(page_json_path, findings, required=False)
        if page_config:
            inspect_components(page_config, page_json_path, source_root, findings)

    tabbar = app.get("tabBar", {})
    if tabbar and not isinstance(tabbar, dict):
        findings.append(Finding("BLOCKER", "invalid-tabbar", "tabBar should be an object.", str(app_json_path)))
        tabbar = {}
    tab_list = tabbar.get("list", []) if isinstance(tabbar, dict) else []
    if tab_list and not isinstance(tab_list, list):
        findings.append(Finding("BLOCKER", "invalid-tabbar-list", "tabBar.list should be an array.", str(app_json_path)))
        tab_list = []
    for item in tab_list or []:
        if not isinstance(item, dict):
            findings.append(Finding("BLOCKER", "invalid-tabbar-item", "Each tabBar item should be an object.", str(app_json_path)))
            continue
        route = normalize_route(str(item.get("pagePath") or ""))
        if route not in top_routes:
            findings.append(Finding("BLOCKER", "invalid-tabbar-route", "tabBar pagePath must reference a declared top-level page.", route))
        for key in ("iconPath", "selectedIconPath"):
            value = item.get(key)
            if value and not (source_root / normalize_route(str(value))).is_file():
                findings.append(Finding("BLOCKER", "missing-tabbar-icon", f"{key} does not exist.", str(value)))
    if isinstance(tabbar, dict) and tabbar.get("custom") is True:
        require_companion_files(source_root / "custom-tab-bar" / "index", "custom-tab-bar", findings)

    ignores = load_ignores(config, root_value)
    mode, privacy_hits, capability_hits = scan_sources(source_root, findings, ignores) if source_root.is_dir() else ("unknown", [], [])
    has_cloudbase_shape = bool(config.get("cloudbaseRoot")) or (project / "cloudfunctions").is_dir() or (source_root / "cloudfunctions").is_dir()
    if has_cloudbase_shape and mode == "custom-backend":
        mode = "hybrid"
    elif has_cloudbase_shape and mode == "local-only-or-undetected":
        mode = "cloudbase"
    findings.append(Finding("UNKNOWN", "release-console", "Confirm filing, service categories, qualifications, privacy declarations, configured domains, and submitted version in official consoles."))
    findings.append(Finding("UNKNOWN", "real-device", "Compile in WeChat Developer Tools and complete experience-build testing on real devices."))

    order = {"BLOCKER": 0, "WARNING": 1, "UNKNOWN": 2, "PASS": 3}
    findings.sort(key=lambda item: (order.get(item.severity, 9), item.code, item.path))
    blocker_count = sum(item.severity == "BLOCKER" for item in findings)
    warning_count = sum(item.severity == "WARNING" for item in findings)
    unknown_count = sum(item.severity == "UNKNOWN" for item in findings)
    summary = {
        "project": str(project),
        "source_root": str(source_root),
        "appid_present": bool(appid and appid not in {"touristappid", "wx0000000000000000"}),
        "backend_mode": mode,
        "routes": len(seen),
        "privacy_categories_detected": privacy_hits,
        "capabilities_detected": capability_hits,
        "blockers": blocker_count,
        "warnings": warning_count,
        "unknown": unknown_count,
        "gate": "BLOCKED" if blocker_count else "STATIC_CHECK_PASSED_EXTERNAL_CONFIRMATION_REQUIRED",
    }

    if args.json:
        print(json.dumps({"summary": summary, "findings": [asdict(item) for item in findings]}, ensure_ascii=False, indent=2))
    else:
        print(f"Project: {project}")
        print(f"Source root: {source_root}")
        print(f"Backend mode: {mode}")
        print(f"Routes checked: {len(seen)}")
        print(f"Gate: {summary['gate']}")
        print(f"Counts: {blocker_count} blocker(s), {warning_count} warning(s), {unknown_count} unknown check(s)")
        print()
        for item in findings:
            location = f" [{item.path}]" if item.path else ""
            print(f"{item.severity:7} {item.code}: {item.message}{location}")
    return 2 if blocker_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
