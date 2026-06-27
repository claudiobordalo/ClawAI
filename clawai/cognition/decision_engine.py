from __future__ import annotations

from abc import ABC, abstractmethod

from .execution_assessment import ExecutionAssessment
from .reasoning_result import ReasoningResult
from .review_result import ReviewResult


class AbstractDecisionEngine(ABC):
    @abstractmethod
    def decide(self, assessment: ExecutionAssessment) -> ReasoningResult: ...


class DecisionEngine(AbstractDecisionEngine):
    def decide(self, assessment: ExecutionAssessment) -> ReasoningResult:
        if assessment.review_result == ReviewResult.SUCCESS:
            return ReasoningResult(
                assessment=assessment.review_result,
                reason="Goal completed successfully",
                recommendation="continue to next goal",
                next_action="continue",
                confidence=1.0,
            )

        if assessment.review_result == ReviewResult.NEEDS_REPLAN:
            return ReasoningResult(
                assessment=assessment.review_result,
                reason="Goal requires replanning",
                recommendation="replan the objective",
                next_action="replan",
                requires_replan=True,
                confidence=0.8,
            )

        if assessment.retry_count < 3:
            return ReasoningResult(
                assessment=assessment.review_result,
                reason=f"Goal failed (attempt {assessment.retry_count + 1}), will retry",
                recommendation=f"retry (attempt {assessment.retry_count + 2})",
                next_action="retry",
                should_retry=True,
                confidence=0.6,
            )

        return ReasoningResult(
            assessment=assessment.review_result,
            reason="Max retries exceeded, needs replan",
            recommendation="replan the objective",
            next_action="replan",
            requires_replan=True,
            confidence=0.5,
        )
