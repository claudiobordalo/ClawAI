from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .failure_analysis import FailureCategory
from .review_result import ReviewResult
from .success_analysis import SuccessAnalysis


@dataclass
class ExecutionAssessment:
    goal_id: str
    goal_title: str
    success: bool
    review_result: ReviewResult
    failure_category: Optional[FailureCategory] = None
    success_analysis: Optional[SuccessAnalysis] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "goal_title": self.goal_title,
            "success": self.success,
            "review_result": self.review_result.value,
            "failure_category": self.failure_category.value if self.failure_category else None,
            "success_analysis": self.success_analysis.to_dict() if self.success_analysis else None,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "duration": self.duration,
            "retry_count": self.retry_count,
            "metadata": dict(self.metadata),
        }
