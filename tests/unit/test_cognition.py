"""Tests for the Cognition Layer (Sprint 5)."""

from unittest.mock import MagicMock

import pytest

from clawai.cognition import (
    AbstractDecisionEngine,
    AbstractReviewer,
    DecisionEngine,
    ExecutionAssessment,
    FailureAnalysis,
    FailureCategory,
    ReasoningEngine,
    ReasoningResult,
    ReflectionEngine,
    ReflectionEntry,
    ReplanningEngine,
    ReviewResult,
    Reviewer,
    SuccessAnalysis,
)
from clawai.engineering import EngineeringMemory
from clawai.goals import Goal, GoalBacklog, GoalPlanner, GoalPriority, GoalStatus


# ===== ABCs =====

class TestAbstractReviewer:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            AbstractReviewer()  # type: ignore[abstract]

    def test_reviewer_is_subclass(self):
        assert issubclass(Reviewer, AbstractReviewer)


class TestAbstractDecisionEngine:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            AbstractDecisionEngine()  # type: ignore[abstract]

    def test_decision_engine_is_subclass(self):
        assert issubclass(DecisionEngine, AbstractDecisionEngine)


# ===== ReviewResult =====

class TestReviewResult:
    def test_values(self):
        assert ReviewResult.SUCCESS.value == "success"
        assert ReviewResult.PARTIAL.value == "partial"
        assert ReviewResult.FAILURE.value == "failure"
        assert ReviewResult.NEEDS_REPLAN.value == "needs_replan"
        assert ReviewResult.UNKNOWN.value == "unknown"

    def test_str(self):
        assert str(ReviewResult.SUCCESS) == "success"


# ===== ReasoningResult =====

class TestReasoningResult:
    def test_defaults(self):
        r = ReasoningResult(assessment=ReviewResult.SUCCESS)
        assert r.confidence == 1.0
        assert r.reason == ""
        assert r.next_action == "continue"
        assert not r.should_retry
        assert not r.requires_replan

    def test_with_data(self):
        r = ReasoningResult(
            assessment=ReviewResult.FAILURE,
            confidence=0.5,
            reason="failed",
            next_action="retry",
            should_retry=True,
            requires_replan=False,
        )
        assert r.assessment == ReviewResult.FAILURE
        assert r.should_retry
        assert r.next_action == "retry"


# ===== FailureAnalysis =====

class TestFailureAnalysis:
    def test_classify_timeout(self):
        assert FailureAnalysis.classify("request timed out") == FailureCategory.TIMEOUT
        assert FailureAnalysis.classify("timeout error") == FailureCategory.TIMEOUT

    def test_classify_tool(self):
        assert FailureAnalysis.classify("tool failed to apply") == FailureCategory.TOOL_FAILURE
        assert FailureAnalysis.classify("editor error") == FailureCategory.TOOL_FAILURE

    def test_classify_validation(self):
        assert FailureAnalysis.classify("validation error") == FailureCategory.VALIDATION_FAILURE
        assert FailureAnalysis.classify("invalid schema") == FailureCategory.VALIDATION_FAILURE

    def test_classify_planning(self):
        assert FailureAnalysis.classify("plan failed") == FailureCategory.PLANNING_FAILURE
        assert FailureAnalysis.classify("ambiguous objective") == FailureCategory.PLANNING_FAILURE

    def test_classify_dependency(self):
        assert FailureAnalysis.classify("dependency not found") == FailureCategory.DEPENDENCY_FAILURE
        assert FailureAnalysis.classify("import error") == FailureCategory.DEPENDENCY_FAILURE

    def test_classify_execution_default(self):
        assert FailureAnalysis.classify("random error") == FailureCategory.EXECUTION_FAILURE
        assert FailureAnalysis.classify("") == FailureCategory.EXECUTION_FAILURE


# ===== SuccessAnalysis =====

class TestSuccessAnalysis:
    def test_defaults(self):
        s = SuccessAnalysis()
        assert s.duration == 0.0
        assert s.quality_score == 1.0
        assert s.tests_passed == 0
        assert s.files_modified == 0
        assert s.impact_score == 0.5
        assert s.recommendations == []

    def test_with_data(self):
        s = SuccessAnalysis(duration=1.5, quality_score=0.9, tests_passed=5, files_modified=2)
        assert s.duration == 1.5
        assert s.tests_passed == 5
        assert s.files_modified == 2


# ===== ExecutionAssessment =====

class TestExecutionAssessment:
    def test_defaults(self):
        a = ExecutionAssessment(
            goal_id="g1", goal_title="test",
            success=True, review_result=ReviewResult.SUCCESS,
        )
        assert a.errors == []
        assert a.warnings == []
        assert a.duration == 0.0
        assert a.retry_count == 0

    def test_with_failure(self):
        a = ExecutionAssessment(
            goal_id="g1", goal_title="test",
            success=False, review_result=ReviewResult.FAILURE,
            failure_category=FailureCategory.TIMEOUT,
            errors=["timeout"], duration=30.0,
        )
        assert a.failure_category == FailureCategory.TIMEOUT
        assert a.duration == 30.0


# ===== Reviewer =====

class TestReviewer:
    def test_success(self):
        r = Reviewer()
        assert r.review(success=True) == ReviewResult.SUCCESS

    def test_failure(self):
        r = Reviewer()
        assert r.review(success=False, errors=["error"]) == ReviewResult.FAILURE

    def test_needs_replan(self):
        r = Reviewer()
        assert r.review(success=False, errors=["needs replan"]) == ReviewResult.NEEDS_REPLAN

    def test_replan_on_high_retries(self):
        r = Reviewer()
        assert r.review(success=False, errors=["error"], retry_count=5) == ReviewResult.NEEDS_REPLAN

    def test_partial_on_long_duration(self):
        r = Reviewer()
        assert r.review(success=False, duration=400.0) == ReviewResult.PARTIAL

    def test_unknown(self):
        r = Reviewer()
        assert r.review(success=False) == ReviewResult.UNKNOWN


# ===== DecisionEngine =====

class TestDecisionEngine:
    def test_decide_success(self):
        d = DecisionEngine()
        a = ExecutionAssessment(goal_id="g1", goal_title="t", success=True, review_result=ReviewResult.SUCCESS)
        result = d.decide(a)
        assert result.next_action == "continue"
        assert not result.should_retry

    def test_decide_needs_replan(self):
        d = DecisionEngine()
        a = ExecutionAssessment(goal_id="g1", goal_title="t", success=False, review_result=ReviewResult.NEEDS_REPLAN)
        result = d.decide(a)
        assert result.next_action == "replan"
        assert result.requires_replan

    def test_decide_retry(self):
        d = DecisionEngine()
        a = ExecutionAssessment(goal_id="g1", goal_title="t", success=False, review_result=ReviewResult.FAILURE, retry_count=0)
        result = d.decide(a)
        assert result.next_action == "retry"
        assert result.should_retry

    def test_decide_replan_after_max_retries(self):
        d = DecisionEngine()
        a = ExecutionAssessment(goal_id="g1", goal_title="t", success=False, review_result=ReviewResult.FAILURE, retry_count=3)
        result = d.decide(a)
        assert result.next_action == "replan"
        assert result.requires_replan


# ===== ReflectionEngine =====

class TestReflectionEngine:
    def test_empty(self):
        eng = ReflectionEngine()
        assert eng.count == 0
        assert eng.entries() == ()

    def test_record(self):
        eng = ReflectionEngine()
        entry = ReflectionEntry(goal_id="g1", goal_title="test", success=True)
        eng.record(entry)
        assert eng.count == 1
        assert eng.entries()[0].goal_id == "g1"

    def test_clear(self):
        eng = ReflectionEngine()
        eng.record(ReflectionEntry(goal_id="g1", goal_title="t", success=True))
        eng.clear()
        assert eng.count == 0

    def test_recent_failures(self):
        eng = ReflectionEngine()
        eng.record(ReflectionEntry(goal_id="g1", goal_title="s1", success=True))
        eng.record(ReflectionEntry(goal_id="g2", goal_title="f1", success=False))
        eng.record(ReflectionEntry(goal_id="g3", goal_title="f2", success=False))
        failures = eng.recent_failures()
        assert len(failures) == 2

    def test_repeated_errors(self):
        eng = ReflectionEngine()
        eng.record(ReflectionEntry(goal_id="g1", goal_title="t", success=False, what_failed=["auth error"]))
        eng.record(ReflectionEntry(goal_id="g2", goal_title="t", success=False, what_failed=["auth error"]))
        eng.record(ReflectionEntry(goal_id="g3", goal_title="t", success=False, what_failed=["other error"]))
        repeated = eng.repeated_errors(min_count=2)
        assert "auth error" in repeated
        assert repeated["auth error"] == 2

    def test_record_with_memory(self):
        mem = EngineeringMemory()
        eng = ReflectionEngine(memory=mem)
        entry = ReflectionEntry(goal_id="g1", goal_title="test", success=True)
        eng.record(entry)
        assert eng.count == 1


# ===== ReasoningEngine =====

class TestReasoningEngine:
    def test_analyze_success(self):
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(), failure_analysis=FailureAnalysis())
        result = eng.analyze(
            goal_id="g1", goal_title="t1",
            success=True, output="done",
        )
        assert result.next_action == "continue"
        assert result.confidence == 1.0

    def test_analyze_failure(self):
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(), failure_analysis=FailureAnalysis())
        result = eng.analyze(
            goal_id="g1", goal_title="t1",
            success=False, errors=["error occurred"],
        )
        assert result.next_action == "retry"
        assert result.should_retry

    def test_analyze_with_reflection(self):
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(), failure_analysis=FailureAnalysis())
        eng.analyze(goal_id="g1", goal_title="t1", success=True)
        eng.analyze(goal_id="g2", goal_title="t2", success=False, errors=["error"])
        assert eng.reflection_engine.count == 2
        assert eng.review_count == 2

    def test_analyze_with_typed_fields(self):
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(), failure_analysis=FailureAnalysis())
        result = eng.analyze(
            goal_id="g1", goal_title="t1",
            success=False, errors=["needs replan"],
        )
        assert result.requires_replan
        assert result.review_result == "needs_replan"

    def test_failure_classification(self):
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(), failure_analysis=FailureAnalysis())
        result = eng.analyze(
            goal_id="g1", goal_title="t1",
            success=False, errors=["request timed out"],
        )
        assert result.failure_category == "timeout"


# ===== ReplanningEngine =====

class TestReplanningEngine:
    def test_replan_preserves_completed(self):
        planner = GoalPlanner()
        eng = ReplanningEngine(planner)
        g1 = Goal(id="g1", title="Completed task", description="d", success_criteria="s", priority=1, status=GoalStatus.DONE)
        g2 = Goal(id="g2", title="Failed task", description="d", success_criteria="s", priority=1, status=GoalStatus.BLOCKED)
        backlog = eng.replan("Completed task\nFailed task", current_goals=(g1, g2))
        assert len(backlog.goals) >= 1

    def test_replan_without_completed(self):
        planner = GoalPlanner()
        eng = ReplanningEngine(planner)
        g1 = Goal(id="g1", title="Failed task", description="d", success_criteria="s", priority=1, status=GoalStatus.BLOCKED)
        backlog = eng.replan("Failed task", current_goals=(g1,))
        assert len(backlog.goals) >= 1

    def test_replan_with_memory(self):
        mem = EngineeringMemory()
        planner = GoalPlanner()
        eng = ReplanningEngine(planner, memory=mem)
        backlog = eng.replan("Fix bug", current_goals=())
        assert len(backlog.goals) >= 1


# ===== Integration: ReasoningEngine + ReflectionEngine =====

class TestCognitionIntegration:
    def test_full_flow_success(self):
        mem = EngineeringMemory()
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(memory=mem), failure_analysis=FailureAnalysis())
        result = eng.analyze(
            goal_id="g1", goal_title="Add login",
            success=True, output="login added",
            duration=5.0,
        )
        assert result.next_action == "continue"
        assert eng.reflection_engine.count == 1
        assert eng.review_count == 1

    def test_full_flow_failure_then_replan(self):
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(), failure_analysis=FailureAnalysis())
        result = eng.analyze(
            goal_id="g1", goal_title="Complex feature",
            success=False, errors=["needs replan"],
            retry_count=0, duration=10.0,
        )
        assert result.requires_replan

    def test_full_flow_retry(self):
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(), failure_analysis=FailureAnalysis())
        result = eng.analyze(
            goal_id="g1", goal_title="Flaky test",
            success=False, errors=["tool error"],
            retry_count=1,
        )
        assert result.should_retry
        assert not result.requires_replan

    def test_repeated_errors_detection(self):
        eng = ReasoningEngine(reviewer=Reviewer(), decision_engine=DecisionEngine(), reflection_engine=ReflectionEngine(memory=EngineeringMemory()), failure_analysis=FailureAnalysis())
        for i in range(3):
            eng.analyze(
                goal_id=f"g{i}", goal_title=f"Fix bug {i}",
                success=False, errors=["timeout error"],
                duration=1.0,
            )
        repeated = eng.reflection_engine.repeated_errors(min_count=2)
        assert "timeout error" in repeated
        assert repeated["timeout error"] >= 2


# ===== ABC Implementations (LLM future) =====

class TestABCImplementations:
    """Verify ABCs can be extended for future LLM-based implementations."""

    def test_custom_reviewer(self):
        class AlwaysSuccess(AbstractReviewer):
            def review(self, **kwargs) -> ReviewResult:
                return ReviewResult.SUCCESS

        r = AlwaysSuccess()
        assert r.review(success=False) == ReviewResult.SUCCESS

    def test_custom_decision_engine(self):
        class AlwaysReplan(AbstractDecisionEngine):
            def decide(self, assessment: ExecutionAssessment) -> ReasoningResult:
                return ReasoningResult(
                    assessment=assessment.review_result,
                    next_action="replan",
                    requires_replan=True,
                )

        d = AlwaysReplan()
        a = ExecutionAssessment(goal_id="g1", goal_title="t", success=False, review_result=ReviewResult.FAILURE)
        r = d.decide(a)
        assert r.requires_replan
        assert r.next_action == "replan"
