#!/usr/bin/env python3
"""Estimate WeChat Mini Program source-package size after configured ignores."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


DEFAULT_SKIP_DIRS = {".git", "node_modules"}


def load_config(project: Path) -> dict:
    config_path = project / "project.config.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def resolve_package_root(project: Path, config: dict) -> tuple[Path, str]:
    root_value = str(config.get("miniprogramRoot") or ".").strip().strip("/") or "."
    return (project / root_value).resolve(), root_value


def load_ignores(config: dict, root_value: str) -> list[tuple[str, str]]:
    ignores = config.get("packOptions", {}).get("ignore", [])
    result: list[tuple[str, str]] = []
    for item in ignores:
        value = item.get("value")
        kind = item.get("type", "file")
        if value:
            normalized = value.strip("/")
            if root_value != "." and normalized.startswith(root_value + "/"):
                normalized = normalized[len(root_value) + 1 :]
            result.append((normalized, kind))
    return result


def is_ignored(rel: Path, ignores: list[tuple[str, str]]) -> bool:
    rel_posix = rel.as_posix()
    for value, kind in ignores:
        if kind == "folder":
            if rel_posix == value or rel_posix.startswith(value + "/"):
                return True
        elif rel_posix == value:
            return True
    return False


def iter_files(package_root: Path, ignores: list[tuple[str, str]]):
    for root, dirs, files in os.walk(package_root):
        root_path = Path(root)
        rel_root = root_path.relative_to(package_root)
        dirs[:] = [
            d
            for d in dirs
            if d not in DEFAULT_SKIP_DIRS and not is_ignored((rel_root / d), ignores)
        ]
        for name in files:
            path = root_path / name
            rel = path.relative_to(package_root)
            if not is_ignored(rel, ignores):
                yield rel, path.stat().st_size


def fmt_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.1f} {unit}" if unit != "B" else f"{num} B"
        num /= 1024
    return f"{num:.1f} GB"


def load_subpackage_roots(package_root: Path) -> list[str]:
    app_path = package_root / "app.json"
    if not app_path.exists():
        return []
    try:
        app = json.loads(app_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    packages = app.get("subPackages", app.get("subpackages", []))
    if not isinstance(packages, list):
        return []
    roots: list[str] = []
    for item in packages:
        if isinstance(item, dict):
            root = str(item.get("root") or "").strip().strip("/")
            if root and root not in roots:
                roots.append(root)
    return roots


def containing_subpackage(rel: Path, roots: list[str]) -> str | None:
    rel_posix = rel.as_posix()
    matches = [root for root in roots if rel_posix == root or rel_posix.startswith(root + "/")]
    return max(matches, key=len) if matches else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".", help="Mini Program project root")
    parser.add_argument("--limit-mb", type=float, default=2.0, help="Target source package limit")
    parser.add_argument("--total-limit-mb", type=float, default=20.0, help="Target aggregate package limit")
    parser.add_argument("--top", type=int, default=20, help="Largest included files to show")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    config = load_config(project)
    package_root, root_value = resolve_package_root(project, config)
    if not package_root.is_dir():
        parser.error(f"Mini Program source root does not exist: {package_root}")
    ignores = load_ignores(config, root_value)
    files = sorted(iter_files(package_root, ignores), key=lambda item: item[1], reverse=True)
    total = sum(size for _, size in files)
    per_package_limit = int(args.limit_mb * 1024 * 1024)
    total_limit = int(args.total_limit_mb * 1024 * 1024)
    subpackage_roots = load_subpackage_roots(package_root)
    buckets: dict[str, int] = {root: 0 for root in subpackage_roots}
    main_total = 0
    for rel, size in files:
        root = containing_subpackage(rel, subpackage_roots)
        if root is None:
            main_total += size
        else:
            buckets[root] += size
    over_packages = (["main"] if main_total > per_package_limit else []) + [
        root for root, size in buckets.items() if size > per_package_limit
    ]
    ok = not over_packages and total <= total_limit

    result = {
        "project": str(project),
        "source_root": str(package_root),
        "included_files": len(files),
        "total_bytes": total,
        "aggregate_target_bytes": total_limit,
        "per_package_target_bytes": per_package_limit,
        "main_package_bytes": main_total,
        "subpackage_bytes": buckets,
        "over_target_packages": over_packages,
        "status": "OK" if ok else "OVER_TARGET",
        "largest_files": [{"path": rel.as_posix(), "bytes": size} for rel, size in files[: args.top]],
        "note": "Targets are configurable safety thresholds; verify current official upload limits at execution time.",
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if ok else 2

    print(f"Project: {project}")
    print(f"Source root: {package_root}")
    print(f"Included files: {len(files)}")
    print(f"Estimated aggregate size: {fmt_size(total)}")
    print(f"Estimated main package: {fmt_size(main_total)}")
    for root, size in sorted(buckets.items()):
        print(f"Estimated subpackage {root}: {fmt_size(size)}")
    print(f"Per-package target: {fmt_size(per_package_limit)}")
    print(f"Aggregate target: {fmt_size(total_limit)}")
    print(f"Status: {'OK' if ok else 'OVER TARGET'}")
    print("Note: targets are configurable safety thresholds; verify current official upload limits at execution time.")
    print()
    print(f"Top {min(args.top, len(files))} included files:")
    for rel, size in files[: args.top]:
        print(f"{fmt_size(size):>10}  {rel.as_posix()}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
