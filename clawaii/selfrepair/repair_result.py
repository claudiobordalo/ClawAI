from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .repair_iteration import RepairIteration


@dataclass(frozen=True)
class RepairResult:
    success: bool
    iterations: Tuple[RepairIteration, ...]
    final_iteration: Optional[RepairIteration]
    summary: str
    error: Optional[str] = None
