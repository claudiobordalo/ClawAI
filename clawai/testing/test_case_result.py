from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

_ALLOWED = {"passed", "failed", "skipped", "error"}


@dataclass(frozen=True)
class TestCaseResult:
    """Immutable result of a single test case."""
    name: str
    status: str  # one of: passed, failed, skipped, error
    duration: float
    message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED:
            raise ValueError(f"invalid status: {self.status}")
        if self.duration < 0:
            raise ValueError("duration must be >= 0")
