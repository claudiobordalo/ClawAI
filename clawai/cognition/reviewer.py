from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .review_result import ReviewResult


class AbstractReviewer(ABC):
    @abstractmethod
    def review(
        self,
        *,
        success: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        output: str = "",
        duration: float = 0.0,
        retry_count: int = 0,
        metadata: Optional[dict] = None,
    ) -> ReviewResult: ...


class Reviewer(AbstractReviewer):
    def review(
        self,
        *,
        success: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        output: str = "",
        duration: float = 0.0,
        retry_count: int = 0,
        metadata: Optional[dict] = None,
    ) -> ReviewResult:
        if success:
            return ReviewResult.SUCCESS

        if errors:
            for err in errors:
                lower = err.lower()
                if any(kw in lower for kw in ("replan", "objective", "invalid plan")):
                    return ReviewResult.NEEDS_REPLAN

        if retry_count >= 3:
            return ReviewResult.NEEDS_REPLAN

        if duration > 300.0:
            return ReviewResult.PARTIAL

        if errors:
            return ReviewResult.FAILURE

        return ReviewResult.UNKNOWN
