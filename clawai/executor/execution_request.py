from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutionRequest:
    project_root: Path
    objective: str
    target_query: str
    instructions: str
    max_iterations: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_root", Path(self.project_root))
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
