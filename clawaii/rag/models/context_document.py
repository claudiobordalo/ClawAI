from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ContextDocument:

    path: Path
    content: str
    score: float = 0.0
