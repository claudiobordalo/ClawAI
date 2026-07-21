from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .models import ProjectScan


TEXT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".toml", ".yml", ".yaml"}
PYTHON_EXTENSIONS = {".py"}
JS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}

# We want the scanner to focus on the real source tree, not generated or vendored content.
EXCLUDED_DIRS = {
    ".git",
    ".npx",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    ".env",
    ".tox",
    ".cache",
    "__pycache__",
    "build",
    "dist",
    "release",
    "node_modules",
}

EXCLUDED_PATH_PARTS = {
    "site-packages",
    "dist-packages",
    "lib",
    "libs",
}

# Default scope for the scanner output.
SOURCE_TOP_LEVEL_DIRS = {"clawai", "desktop", "frontend"}
TEST_TOP_LEVEL_DIRS = {"tests"}


def _detect_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root).resolve()
    return Path(__file__).resolve().parents[2]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _is_excluded_path(path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True
    if any(part in EXCLUDED_PATH_PARTS for part in path.parts):
        return True
    return False


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for current, dirs, filenames in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        if _is_excluded_path(current_path):
            continue
        for filename in filenames:
            path = current_path / filename
            if _is_excluded_path(path):
                continue
            files.append(path)
    return files


def _top_directory(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    return rel.parts[0] if rel.parts else "(root)"


def _is_source_file(root: Path, path: Path) -> bool:
    top = _top_directory(root, path)
    return top in SOURCE_TOP_LEVEL_DIRS


def _is_test_file(root: Path, path: Path) -> bool:
    top = _top_directory(root, path)
    if top in TEST_TOP_LEVEL_DIRS:
        return True
    name = path.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or name.endswith(".test.py")


def _count_by_top_directory(root: Path, files: list[Path]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for path in files:
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        top = rel.parts[0] if rel.parts else "(root)"
        counts[top] += 1
    return [{"path": name, "files": count} for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]


def _count_python(files: list[Path]) -> int:
    return sum(1 for path in files if path.suffix.lower() in PYTHON_EXTENSIONS)


def _count_js(files: list[Path]) -> int:
    return sum(1 for path in files if path.suffix.lower() in JS_EXTENSIONS)


def scan_project(root: str | Path | None = None, *, source_only: bool = True) -> ProjectScan:
    project_root = _detect_root(root)
    files = _walk_files(project_root)

    if source_only:
        source_files = [path for path in files if _is_source_file(project_root, path)]
        test_files = [path for path in files if _is_test_file(project_root, path)]
    else:
        source_files = files
        test_files = [path for path in files if _is_test_file(project_root, path)]

    python_files = [path for path in source_files if path.suffix.lower() in PYTHON_EXTENSIONS]
    js_files = [path for path in source_files if path.suffix.lower() in JS_EXTENSIONS]
    test_python_files = [path for path in test_files if path.suffix.lower() in PYTHON_EXTENSIONS]
    test_js_files = [path for path in test_files if path.suffix.lower() in JS_EXTENSIONS]

    entrypoints: list[str] = []
    for candidate in [project_root / "main.py", project_root / "ClawAI.bat", project_root / "desktop" / "main.py"]:
        if candidate.exists():
            entrypoints.append(str(candidate.relative_to(project_root)).replace("\\", "/"))

    frontend = "frontend" if (project_root / "frontend").exists() else None
    backend = "clawai" if (project_root / "clawai").exists() else None

    dependencies: list[str] = []
    package_json = project_root / "frontend" / "package.json"
    if package_json.exists():
        try:
            data = json.loads(_read_text(package_json))
            dependencies.extend(sorted(data.get("dependencies", {}).keys()))
        except Exception:
            pass

    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        text = _read_text(pyproject)
        for line in text.splitlines():
            if line.strip().startswith(("fastapi", "pywebview", "uvicorn", "httpx", "psutil")):
                dependencies.append(line.strip())

    branch = os.environ.get("GIT_BRANCH")

    scan = ProjectScan(
        project=project_root.name,
        root=str(project_root),
        branch=branch,
        python_files=len(python_files),
        javascript_files=len(js_files),
        test_python_files=len(test_python_files),
        test_javascript_files=len(test_js_files),
        entrypoints=entrypoints,
        frontend=frontend,
        backend=backend,
        dependencies=sorted(set(dependencies)),
        scripts=["build_desktop.bat", "ClawAI.bat"] if (project_root / "build_desktop.bat").exists() else [],
        directories=_count_by_top_directory(project_root, source_files),
        python_directories=_count_by_top_directory(project_root, python_files),
        test_directories=_count_by_top_directory(project_root, test_files),
        git={"branch": branch} if branch else {},
    )
    return scan


def main() -> None:
    scan = scan_project()
    print(json.dumps(scan.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
