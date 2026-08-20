from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from clawai.editor import EditOperation


@dataclass(frozen=True)
class PatchPlan:
    """Immutable patch plan containing edit operations to apply."""

    operations: Tuple[EditOperation, ...]
    summary: str
    success: bool
    error: Optional[str] = None

    @staticmethod
    def success_plan(operations: Tuple[EditOperation, ...], summary: str) -> "PatchPlan":
        return PatchPlan(operations=operations, summary=summary, success=True, error=None)

    @staticmethod
    def error_plan(error: str, summary: str = "") -> "PatchPlan":
        return PatchPlan(operations=tuple(), summary=summary, success=False, error=error)
