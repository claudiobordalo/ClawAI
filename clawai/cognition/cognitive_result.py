from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .execution_assessment import ExecutionAssessment
from .failure_analysis import FailureCategory
from .review_result import ReviewResult
from .success_analysis import SuccessAnalysis


@dataclass(frozen=True)
class CognitiveResult:
    review_result: ReviewResult
    assessment: ExecutionAssessment
    confidence: float = 1.0
    reasoning: str = ""
    recommendation: str = ""
    next_action: str = "continue"
    failure_category: Optional[FailureCategory] = None
    success_analysis: Optional[SuccessAnalysis] = None
    reflection_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "review_result": self.review_result.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "recommendation": self.recommendation,
            "next_action": self.next_action,
            "failure_category": self.failure_category.value if self.failure_category else None,
            "success_analysis": self.success_analysis.to_dict() if self.success_analysis else None,
            "reflection_id": self.reflection_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": dict(self.metadata),
        }
        return base

    @classmethod
    def from_assessment(
        cls,
        review_result: ReviewResult,
        assessment: ExecutionAssessment,
        **kwargs: Any,
    ) -> CognitiveResult:
        return cls(
            review_result=review_result,
            assessment=assessment,
            failure_category=assessment.failure_category,
            success_analysis=assessment.success_analysis,
            **kwargs,
        )
