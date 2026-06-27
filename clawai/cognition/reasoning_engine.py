from __future__ import annotations

from typing import Any, Dict, List, Optional

from clawai.engineering import AbstractMemory

from .abstract_reasoning_engine import AbstractReasoningEngine
from .cognitive_result import CognitiveResult
from .decision_engine import AbstractDecisionEngine
from .execution_assessment import ExecutionAssessment
from .failure_analysis import AbstractFailureAnalysis, FailureCategory
from .reasoning_result import ReasoningResult
from .reflection_engine import AbstractReflectionEngine, ReflectionEntry
from .reviewer import AbstractReviewer
from .success_analysis import SuccessAnalysis


class ReasoningEngine(AbstractReasoningEngine):
    def __init__(
        self,
        reviewer: AbstractReviewer,
        decision_engine: AbstractDecisionEngine,
        reflection_engine: AbstractReflectionEngine,
        failure_analysis: AbstractFailureAnalysis,
    ) -> None:
        self._reviewer = reviewer
        self._decision_engine = decision_engine
        self._reflection_engine = reflection_engine
        self._failure_analysis = failure_analysis
        self._review_count = 0

    @property
    def reflection_engine(self) -> AbstractReflectionEngine:
        return self._reflection_engine

    @property
    def review_count(self) -> int:
        return self._review_count

    def analyze(
        self,
        *,
        goal_id: str,
        goal_title: str,
        success: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        output: str = "",
        duration: float = 0.0,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReasoningResult:
        self._review_count += 1

        review_result = self._reviewer.review(
            success=success,
            errors=errors,
            warnings=warnings,
            output=output,
            duration=duration,
            retry_count=retry_count,
            metadata=metadata,
        )

        failure_category: Optional[FailureCategory] = None
        if not success and errors:
            for err in errors:
                failure_category = self._failure_analysis.classify(
                    err, duration=duration
                )
                break

        success_analysis: Optional[SuccessAnalysis] = None
        if success:
            success_analysis = SuccessAnalysis(duration=duration)

        assessment = ExecutionAssessment(
            goal_id=goal_id,
            goal_title=goal_title,
            success=success,
            review_result=review_result,
            failure_category=failure_category,
            success_analysis=success_analysis,
            errors=errors or [],
            warnings=warnings or [],
            duration=duration,
            retry_count=retry_count,
            metadata=metadata or {},
        )

        cognitive = self.reflect(assessment)

        result = self._decision_engine.decide(assessment)
        result.review_result = review_result.value
        if failure_category:
            result.failure_category = failure_category.value
        result.review_count = self._review_count
        result.reflection_id = cognitive.reflection_id
        return result

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
    ) -> CognitiveResult:
        review_result = self._reviewer.review(
            success=success,
            errors=errors,
            warnings=warnings,
            output=output,
            duration=duration,
            retry_count=retry_count,
            metadata=metadata,
        )
        assessment = ExecutionAssessment(
            goal_id="", goal_title="",
            success=success, review_result=review_result,
            errors=errors or [], warnings=warnings or [],
            duration=duration, retry_count=retry_count,
            metadata=metadata or {},
        )
        return CognitiveResult(
            review_result=review_result,
            assessment=assessment,
            confidence=1.0,
        )

    def reflect(self, assessment: ExecutionAssessment) -> CognitiveResult:
        reflection_entry = ReflectionEntry(
            goal_id=assessment.goal_id,
            goal_title=assessment.goal_title,
            success=assessment.success,
            review_result=assessment.review_result,
            failure_category=assessment.failure_category,
            what_worked=[] if not assessment.success else assessment.metadata.get("output", ""),
            what_failed=assessment.errors,
            duration=assessment.duration,
        )
        self._reflection_engine.record(reflection_entry)
        return CognitiveResult(
            review_result=assessment.review_result,
            assessment=assessment,
            failure_category=assessment.failure_category,
            success_analysis=assessment.success_analysis,
            reflection_id=reflection_entry.goal_id,
        )

    def decide(self, assessment: ExecutionAssessment) -> CognitiveResult:
        result = self._decision_engine.decide(assessment)
        return CognitiveResult(
            review_result=result.assessment,
            assessment=assessment,
            confidence=result.confidence,
            reasoning=result.reason,
            recommendation=result.recommendation,
            next_action=result.next_action,
            failure_category=assessment.failure_category,
            success_analysis=assessment.success_analysis,
            metadata={"review_count": self._review_count},
        )
