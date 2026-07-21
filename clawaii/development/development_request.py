from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DevelopmentRequest:
    project_root: str | Path
    objective: str
    target_query: str
    instructions: str
