from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .patch import Patch


@dataclass(frozen=True)
class PatchResult:
    success: bool
    patches: Tuple[Patch, ...]
    error: Optional[str] = None

    @staticmethod
    def ok(patches: Tuple[Patch, ...]) -> "PatchResult":
        return PatchResult(success=True, patches=patches, error=None)

    @staticmethod
    def fail(error: str) -> "PatchResult":
        return PatchResult(success=False, patches=tuple(), error=error)
