from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import ProjectScan


TEXT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".toml", ".yml", ".yaml"}
PYTHON_EXTENSIONS = {".py"}
JS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}


def _detect_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root).resolve()
    return Path(__file__).resolve().parents[2]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    ignore_parts = {".git", "node_modules", ".venv", "dist", "build", "release", "__pycache__", ".npx", ".pytest_cache", ".mypy_cache", ".ruff_cache"}

    for current, dirs, filenames in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if d not in ignore_parts]
        if any(part in ignore_parts for part in current_path.parts):
            continue
        for filename in filenames:
            path = current_path / filename
            if any(part in ignore_parts for part in path.parts):
                continue
            files.append(path)
    return files


def scan_project(root: str | Path | None = None) -> ProjectScan:
    project_root = _detect_root(root)
    files = _walk_files(project_root)

    python_files = [path for path in files if path.suffix.lower() in PYTHON_EXTENSIONS]
    js_files = [path for path in files if path.suffix.lower() in JS_EXTENSIONS]

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
        entrypoints=entrypoints,
        frontend=frontend,
        backend=backend,
        dependencies=sorted(set(dependencies)),
        scripts=["build_desktop.bat", "ClawAI.bat"] if (project_root / "build_desktop.bat").exists() else [],
        git={"branch": branch} if branch else {},
    )
    return scan


def main() -> None:
    scan = scan_project()
    print(json.dumps(scan.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
