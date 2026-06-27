from __future__ import annotations

from enum import Enum


class ReviewResult(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    NEEDS_REPLAN = "needs_replan"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value
