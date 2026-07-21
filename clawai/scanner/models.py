from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProjectScan:
    project: str
    root: str
    branch: str | None = None
    python_files: int = 0
    javascript_files: int = 0
    entrypoints: list[str] = field(default_factory=list)
    frontend: str | None = None
    backend: str | None = None
    dependencies: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    git: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "root": self.root,
            "branch": self.branch,
            "python_files": self.python_files,
            "javascript_files": self.javascript_files,
            "entrypoints": self.entrypoints,
            "frontend": self.frontend,
            "backend": self.backend,
            "dependencies": self.dependencies,
            "scripts": self.scripts,
            "git": self.git,
        }
