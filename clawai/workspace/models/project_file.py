from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ProjectFile:

    path: Path
    extension: str
    size: int
