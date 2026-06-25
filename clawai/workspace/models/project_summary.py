from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ProjectSummary:

    name: str
    root: Path

    total_files: int
    total_directories: int

    languages: dict[str, int]

    readme: bool
    git: bool

    pyproject: bool
    requirements: bool
    package_json: bool
