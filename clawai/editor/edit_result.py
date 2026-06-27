from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class EditResult:
    """Immutable result for an edit application attempt."""

    success: bool
    file: Path
    previous_content: Optional[str]
    current_content: Optional[str]
    error: Optional[str]

    @staticmethod
    def ok(file: str | Path, previous_content: str, current_content: str | None) -> "EditResult":
        return EditResult(
            success=True,
            file=Path(file),
            previous_content=previous_content,
            current_content=current_content,
            error=None,
        )

    @staticmethod
    def fail(
        file: str | Path,
        previous_content: Optional[str],
        current_content: Optional[str],
        error: str,
    ) -> "EditResult":
        return EditResult(
            success=False,
            file=Path(file),
            previous_content=previous_content,
            current_content=current_content,
            error=error,
        )
