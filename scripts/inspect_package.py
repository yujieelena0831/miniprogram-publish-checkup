#!/usr/bin/env python3
"""Package-first WeChat Mini Program release preflight for a directory or ZIP."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


SKIP_DISCOVERY_DIRS = {".git", "__MACOSX", "node_modules"}


@dataclass
class Finding:
    status: str
    code: str
    category: str
    evidence: str
    impact: str
    remediation: str
    retest: str
    location: str = ""
    evidence_class: str = "PACKAGE"


REMEDIATIONS: dict[str, tuple[str, str]] = {
    "missing-json": ("Restore the required JSON file in the detected Mini Program root.", "Run the package inspection again and confirm the file parses."),
    "invalid-json": ("Correct the JSON syntax at the reported path.", "Parse the file and rerun the package inspection."),
    "invalid-json-shape": ("Change the file root value to a JSON object.", "Rerun the package inspection."),
    "invalid-source-root": ("Set miniprogramRoot to a directory inside the supplied project.", "Rerun inspection and compile from that root."),
    "missing-source-root": ("Restore the configured miniprogramRoot directory or correct project.config.json.", "Rerun inspection and compile in Developer Tools."),
    "missing-appid": ("Set the real Mini Program AppID in project.config.json before preview or upload.", "Open the project in Developer Tools and verify its identity."),
    "missing-app-script": ("Restore app.js or app.ts in the detected Mini Program root.", "Rerun inspection and compile from a clean start."),
    "missing-pages": ("Declare at least one valid page in app.json.", "Rerun inspection and open the initial page."),
    "missing-page-file": ("Restore the missing page companion file or remove the invalid route.", "Rerun inspection and compile the affected page."),
    "missing-page-script": ("Add the page .js or .ts entry file.", "Rerun inspection and compile the affected page."),
    "missing-component-file": ("Restore the missing component companion file or correct usingComponents.", "Rerun inspection and render every page using the component."),
    "missing-component-script": ("Add the component .js or .ts entry file.", "Rerun inspection and render the component."),
    "invalid-tabbar-route": ("Point tabBar.pagePath to a declared top-level page.", "Rerun inspection and switch to every tab on a device."),
    "missing-tabbar-icon": ("Restore the icon or correct its exact relative path and letter case.", "Rerun inspection and inspect normal and selected states."),
    "possible-secret-file": ("Remove the credential from the client package, rotate it if exposed, and keep it in a protected server or CI secret store.", "Rerun inspection and search the final upload artifact for the credential."),
    "domain-check-disabled": ("Enable domain validation for the release configuration and confirm production domains in the platform console.", "Compile the release build with domain validation enabled."),
    "insecure-or-local-endpoint": ("Replace HTTP, localhost, loopback, or development endpoints with the intended production HTTPS endpoint and configure its domain in the platform console.", "Search the final artifact again and test the production endpoint from an experience build."),
    "embedded-secret": ("Remove the credential from client-readable code, rotate it, and move privileged calls to a trusted backend.", "Search the final artifact again and verify the old credential is revoked."),
    "archive-junk": ("Remove .DS_Store, __MACOSX, Thumbs.db, and similar operating-system metadata before rebuilding the package.", "Rerun inspection and confirm no archive-junk finding remains."),
    "privacy-inventory": ("Make the platform privacy guide and consent timing match every detected information type, including SDK and backend processing.", "Test first consent, denial, later authorization, revocation, deletion, and account cancellation where applicable."),
    "scenario-compliance": ("Apply current official category, qualification, privacy, content, customer-service, refund, moderation, and safety rules only for the detected capabilities.", "Match current console evidence and runtime paths to every detected capability."),
}


def safe_extract(archive: Path, destination: Path) -> list[Finding]:
    findings: list[Finding] = []
    with zipfile.ZipFile(archive) as zf:
        seen: set[str] = set()
        for info in zf.infolist():
            normalized = info.filename.replace("\\", "/")
            parts = PurePosixPath(normalized).parts
            mode = info.external_attr >> 16
            if not normalized or normalized.startswith("/") or ".." in parts:
                findings.append(Finding("BLOCKER", "unsafe-archive-path", "artifact", normalized, "The ZIP can write outside its extraction directory.", "Create a new ZIP containing only relative project paths.", "Inspect and extract the rebuilt ZIP successfully.", normalized))
                continue
            if stat.S_ISLNK(mode):
                findings.append(Finding("BLOCKER", "archive-symlink", "artifact", normalized, "Symlinks make the delivered artifact ambiguous or unsafe.", "Replace the symlink with the intended regular file inside the project.", "Rebuild the ZIP and rerun inspection.", normalized))
                continue
            key = normalized.rstrip("/")
            if key in seen:
                findings.append(Finding("WARNING", "duplicate-archive-entry", "artifact", normalized, "Duplicate ZIP entries can produce different files in different extractors.", "Rebuild the ZIP with one entry per path.", "List the rebuilt ZIP and confirm every path is unique.", normalized))
                continue
            seen.add(key)
            target = destination.joinpath(*parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    return findings


def discover_roots(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in root.rglob("project.config.json"):
        if not any(part in SKIP_DISCOVERY_DIRS for part in path.relative_to(root).parts):
            candidates.append(path.parent)
    return sorted(candidates, key=lambda path: (len(path.relative_to(root).parts), path.as_posix()))


def run_json(script: Path, project: Path, extra: list[str] | None = None) -> tuple[dict[str, Any], int, str]:
    command = [sys.executable, str(script), str(project), "--json", *(extra or [])]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    try:
        return json.loads(completed.stdout), completed.returncode, completed.stderr.strip()
    except json.JSONDecodeError:
        return {}, completed.returncode, (completed.stderr or completed.stdout).strip()


def convert_audit_finding(item: dict[str, Any]) -> Finding:
    status = "UNKNOWN" if item.get("severity") in {"MANUAL", "UNKNOWN"} else str(item.get("severity") or "WARNING")
    code = str(item.get("code") or "audit-finding")
    message = str(item.get("message") or "Static inspection produced a finding.")
    remediation, retest = REMEDIATIONS.get(
        code,
        ("Correct the reported configuration or file at the affected location.", "Rerun package inspection, then compile and test the affected path."),
    )
    if status == "UNKNOWN" and code not in REMEDIATIONS:
        remediation = "Provide current evidence from the named console or runtime check; fix any failed item it reveals."
        retest = "Verify the evidence is current and matches this AppID, version, subject, and production environment."
    return Finding(status, code, "static-project", message, message, remediation, retest, str(item.get("path") or ""), "PLATFORM" if status == "UNKNOWN" else "PACKAGE")


def inspect(input_path: Path, per_package_limit: float, total_limit: float) -> dict[str, Any]:
    findings: list[Finding] = []
    temporary: tempfile.TemporaryDirectory[str] | None = None
    try:
        if input_path.is_dir():
            unpacked = input_path
            input_kind = "directory"
        elif input_path.is_file() and zipfile.is_zipfile(input_path):
            temporary = tempfile.TemporaryDirectory(prefix="miniprogram-checkup-")
            unpacked = Path(temporary.name)
            input_kind = "zip"
            findings.extend(safe_extract(input_path, unpacked))
        else:
            findings.append(Finding("BLOCKER", "unsupported-input", "artifact", str(input_path), "The input is neither a readable directory nor a valid ZIP.", "Provide the complete project directory or a standard ZIP archive.", "Run the inspector again on the replacement input.", str(input_path)))
            return build_report(input_path, input_kind="unsupported", project=None, audit={}, package={}, findings=findings)

        roots = discover_roots(unpacked)
        if not roots:
            findings.append(Finding("BLOCKER", "project-root-not-found", "artifact", "No project.config.json found.", "The supplied package cannot be identified as a complete Mini Program project.", "Include project.config.json and all required project files in the handoff.", "Rerun inspection and confirm one project root is detected.", str(unpacked)))
            return build_report(input_path, input_kind, None, {}, {}, findings)
        if len(roots) > 1:
            listed = ", ".join(str(path.relative_to(unpacked)) for path in roots[:8])
            findings.append(Finding("BLOCKER", "multiple-project-roots", "artifact", listed, "The intended release project is ambiguous.", "Deliver one Mini Program project per package or remove unrelated project roots.", "Rerun inspection and confirm exactly one root is detected.", str(unpacked)))
            return build_report(input_path, input_kind, None, {}, {}, findings)

        project = roots[0]
        package_json = project / "package.json"
        if package_json.exists():
            try:
                package_config = json.loads(package_json.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                package_config = {}
            dependency_text = json.dumps(
                {
                    "scripts": package_config.get("scripts", {}),
                    "dependencies": package_config.get("dependencies", {}),
                    "devDependencies": package_config.get("devDependencies", {}),
                },
                ensure_ascii=False,
            ).lower()
            needs_reproducible_build = any(
                token in dependency_text for token in ("taro", "uni-app", "weapp", "miniprogram", "webpack", "vite")
            )
            lockfiles = [project / name for name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb")]
            if needs_reproducible_build and not any(path.exists() for path in lockfiles):
                findings.append(Finding("WARNING", "missing-dependency-lock", "artifact", str(package_json), "A dependency-based build may not be reproducible across machines.", "Generate and include the lockfile for the package manager used by the project.", "Install dependencies from a clean directory using the lockfile and reproduce the Mini Program output.", str(project)))
        script_dir = Path(__file__).resolve().parent
        audit, _, audit_error = run_json(script_dir / "audit_miniprogram.py", project)
        package, _, package_error = run_json(script_dir / "estimate_package_size.py", project, ["--limit-mb", str(per_package_limit), "--total-limit-mb", str(total_limit)])
        if audit_error or not audit:
            findings.append(Finding("BLOCKER", "audit-tool-failed", "tooling", audit_error or "No audit JSON returned.", "The package could not be structurally evaluated.", "Correct the reported parsing or tool error.", "Rerun inspection and obtain a complete audit result.", str(project), "DERIVED"))
        else:
            findings.extend(
                convert_audit_finding(item)
                for item in audit.get("findings", [])
                if item.get("code") not in {"real-device", "release-console"}
            )
        if package_error or not package:
            findings.append(Finding("BLOCKER", "package-size-tool-failed", "tooling", package_error or "No package-size JSON returned.", "Package boundaries and size could not be evaluated.", "Correct the reported configuration or parsing error.", "Rerun inspection and obtain main and subpackage totals.", str(project), "DERIVED"))
        elif package.get("status") != "OK":
            over = ", ".join(package.get("over_target_packages", [])) or "aggregate package"
            findings.append(Finding("BLOCKER", "package-over-target", "package-size", over, "One or more estimated package boundaries exceed the configured safety target.", "Move optional code or assets into appropriate subpackages or remote services, remove unused files, and preserve required runtime files.", "Rerun size inspection and confirm the compiled upload result against current official limits.", str(project), "DERIVED"))
        else:
            findings.append(Finding("PASS", "package-size-estimate", "package-size", f"Main={package.get('main_package_bytes', 0)} bytes; total={package.get('total_bytes', 0)} bytes.", "Configured source-package safety targets were met.", "No change required.", "Confirm the compiled upload result in Developer Tools.", str(project), "DERIVED"))

        findings.append(Finding("UNKNOWN", "compiled-build-evidence", "runtime", "No authoritative compiled upload result is contained in a source package.", "Source inspection cannot prove that the actual upload artifact compiles or meets current limits.", "Build from a clean checkout in current WeChat Developer Tools or miniprogram-ci and retain the result.", "Confirm compilation succeeds with no blocker and record the compiled package result.", evidence_class="RUNTIME"))
        findings.append(Finding("UNKNOWN", "platform-compliance-evidence", "compliance", "Private console state is not contained in the package.", "Filing, categories, qualifications, privacy guide, domain allowlists, and review state cannot be proven from source files.", "Supply current console evidence for this AppID or complete the generated console checklist.", "Match every item to the AppID, subject, submitted version, and detected capabilities.", evidence_class="PLATFORM"))
        findings.append(Finding("UNKNOWN", "real-device-evidence", "runtime", "No experience-build device result is contained in the package.", "Simulator and static checks cannot prove core journeys, permissions, networks, and platform differences work.", "Test the experience build on representative iOS and Android devices.", "Record devices, versions, core paths, permission denial, weak network, and recovery results.", evidence_class="RUNTIME"))
        findings.append(Finding("UNKNOWN", "release-operations-evidence", "operations", "Release ownership and recovery evidence are not contained in the package.", "A build can pass review yet fail without monitoring, rollback, backup, or incident ownership.", "Define release owner, observation window, alerts, rollback trigger and target, and backup/restore evidence.", "Perform a release rehearsal or verify the operating record before formal release.", evidence_class="LEGAL_OR_OPERATIONAL"))
        return build_report(input_path, input_kind, project, audit, package, findings)
    finally:
        if temporary is not None:
            temporary.cleanup()


def build_report(input_path: Path, input_kind: str, project: Path | None, audit: dict[str, Any], package: dict[str, Any], findings: list[Finding]) -> dict[str, Any]:
    blockers = sum(item.status == "BLOCKER" for item in findings)
    unknown = sum(item.status == "UNKNOWN" for item in findings)
    if blockers:
        decision = "BLOCKED"
    elif unknown:
        decision = "PACKAGE_CHECK_PASSED_EXTERNAL_CONFIRMATION_REQUIRED"
    else:
        decision = "READY_FOR_SUBMISSION_OR_RELEASE"
    order = {"BLOCKER": 0, "WARNING": 1, "UNKNOWN": 2, "PASS": 3, "NOT_APPLICABLE": 4}
    findings.sort(key=lambda item: (order.get(item.status, 9), item.category, item.code, item.location))
    return {
        "decision": decision,
        "input": str(input_path),
        "input_kind": input_kind,
        "detected_project_root": str(project) if project else None,
        "scope": audit.get("summary", {}),
        "package": package,
        "counts": {status: sum(item.status == status for item in findings) for status in order},
        "findings": [asdict(item) for item in findings],
    }


def print_text(report: dict[str, Any]) -> None:
    labels = {
        "BLOCKED": "不能进入提审或发布",
        "PACKAGE_CHECK_PASSED_EXTERNAL_CONFIRMATION_REQUIRED": "包体静态检查未发现阻断项，但外部证据待确认",
        "READY_FOR_SUBMISSION_OR_RELEASE": "具备进入提审或发布的证据",
    }
    print(f"结论：{labels.get(report['decision'], report['decision'])}")
    print(f"输入：{report['input']}")
    if report.get("detected_project_root"):
        print(f"项目根目录：{report['detected_project_root']}")
    print("数量：" + ", ".join(f"{key}={value}" for key, value in report["counts"].items()))
    for finding in report["findings"]:
        if finding["status"] == "PASS":
            continue
        location = f" [{finding['location']}]" if finding.get("location") else ""
        print(f"\n{finding['status']} {finding['code']}{location}")
        print(f"原因：{finding['impact']}")
        print(f"证据：{finding['evidence']}")
        print(f"修改：{finding['remediation']}")
        print(f"复验：{finding['retest']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a WeChat Mini Program directory or ZIP and produce a release decision.")
    parser.add_argument("input", help="Project directory or ZIP archive")
    parser.add_argument("--limit-mb", type=float, default=2.0, help="Configurable main/subpackage safety target")
    parser.add_argument("--total-limit-mb", type=float, default=20.0, help="Configurable aggregate safety target")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    report = inspect(Path(args.input).expanduser().resolve(), args.limit_mb, args.total_limit_mb)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 2 if report["decision"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
