from __future__ import annotations

from unittest.mock import MagicMock

from clawai.agent import AgentConfiguration, AgentContext, AgentLoop, RetryPolicy
from clawai.agent.agent_context import AgentConfiguration as AgentConfigurationAlias
from clawai.cognition import CognitiveFactory
from clawai.executor import ExecutionResult
from clawai.goals import Goal, GoalBacklog, GoalEventBus, GoalPlanner, PlanningContext


def _make_reasoning_result(
    *,
    next_action: str = "continue",
    should_retry: bool = False,
    failure_category: str | None = None,
    confidence: float = 1.0,
    recommendation: str = "continue",
    reason: str = "ok",
    assessment_value: str = "SUCCESS",
) -> MagicMock:
    return MagicMock(
        assessment=MagicMock(value=assessment_value),
        next_action=next_action,
        should_retry=should_retry,
        failure_category=failure_category,
        confidence=confidence,
        recommendation=recommendation,
        reason=reason,
    )


def _make_goal(goal_id: str = "g1", title: str = "t1") -> Goal:
    return Goal(
        id=goal_id,
        title=title,
        description="d",
        success_criteria="s",
        priority=1,
    )


def _make_context(
    planner: MagicMock,
    *,
    config: AgentConfiguration,
    executor: MagicMock,
    reasoning_result: MagicMock,
) -> AgentContext:
    goal_manager = MagicMock()
    goal_manager.add_goal.return_value = MagicMock()
    goal_manager.create_backlog.return_value = MagicMock()
    goal_manager.complete_goal.return_value = None
    goal_manager.fail_goal.return_value = None

    reasoning_engine = MagicMock()
    reasoning_engine.analyze.return_value = reasoning_result

    return AgentContext(
        planner=planner,
        goal_manager=goal_manager,
        executor=executor,
        memory=MagicMock(),
        event_bus=GoalEventBus(),
        reasoning_engine=reasoning_engine,
        retry_policy=RetryPolicy(),
        config=config,
        checkpoint_manager=None,
    )


def test_agent_loop_uses_planner_and_executes_single_goal() -> None:
    planner = MagicMock(spec=GoalPlanner)
    planner.plan.return_value = GoalBacklog(goals=(_make_goal(),))

    executor = MagicMock()
    executor.run.return_value = ExecutionResult(
        success=True,
        summary="ok",
        repair_result=None,
        applied_results=(),
    )

    ctx = _make_context(
        planner,
        config=AgentConfiguration(max_goals=0),
        executor=executor,
        reasoning_result=_make_reasoning_result(next_action="continue"),
    )
    loop = AgentLoop(ctx)

    session = loop.run("objective")

    planner.plan.assert_called_once()
    args, kwargs = planner.plan.call_args
    assert args == ("objective",)
    assert isinstance(kwargs["context"], PlanningContext)
    assert kwargs["context"].objective == "objective"

    ctx.executor.run.assert_called_once()
    ctx.goal_manager.complete_goal.assert_called_once_with("g1")
    ctx.goal_manager.fail_goal.assert_not_called()
    assert session.state.value == "completed" or session.state.name == "COMPLETED"
    assert session.completed_goals == ["g1"]
    assert session.failed_goals == []
    assert len(session.results) == 1


def test_agent_loop_completes_without_goals_when_planner_returns_empty_backlog() -> None:
    planner = MagicMock(spec=GoalPlanner)
    planner.plan.return_value = GoalBacklog(goals=())

    executor = MagicMock()
    executor.run.return_value = ExecutionResult(
        success=True,
        summary="ok",
        repair_result=None,
        applied_results=(),
    )

    ctx = _make_context(
        planner,
        config=AgentConfiguration(max_goals=0),
        executor=executor,
        reasoning_result=_make_reasoning_result(next_action="continue"),
    )
    loop = AgentLoop(ctx)

    session = loop.run("objective")

    planner.plan.assert_called_once()
    ctx.executor.run.assert_not_called()
    ctx.goal_manager.complete_goal.assert_not_called()
    ctx.goal_manager.fail_goal.assert_not_called()
    assert session.completed_goals == []
    assert session.failed_goals == []
    assert session.results == []
    assert session.state.value == "completed" or session.state.name == "COMPLETED"


def test_agent_loop_marks_goal_failed_when_executor_reports_failure() -> None:
    planner = MagicMock(spec=GoalPlanner)
    planner.plan.return_value = GoalBacklog(goals=(_make_goal(),))

    executor = MagicMock()
    executor.run.return_value = ExecutionResult(
        success=False,
        summary="failed",
        error="boom",
        repair_result=None,
        applied_results=(),
    )

    ctx = _make_context(
        planner,
        config=AgentConfiguration(max_goals=0),
        executor=executor,
        reasoning_result=_make_reasoning_result(
            next_action="replan",
            should_retry=False,
            failure_category="execution_failure",
            confidence=0.2,
            recommendation="replan",
            reason="failed",
            assessment_value="FAILURE",
        ),
    )
    loop = AgentLoop(ctx)

    session = loop.run("objective")

    planner.plan.assert_called_once()
    ctx.executor.run.assert_called_once()
    ctx.goal_manager.complete_goal.assert_not_called()
    ctx.goal_manager.fail_goal.assert_called_once_with("g1")
    assert len(session.failed_goals) == 1
    assert session.failed_goals == ["g1"]
    assert len(session.completed_goals) == 0
    assert len(session.results) == 1
    assert session.state.value == "completed" or session.state.name == "COMPLETED"


def test_agent_loop_honors_max_goals_limit() -> None:
    planner = MagicMock(spec=GoalPlanner)
    planner.plan.return_value = GoalBacklog(
        goals=(
            _make_goal("g1", "goal-1"),
            _make_goal("g2", "goal-2"),
        )
    )

    executor = MagicMock()
    executor.run.return_value = ExecutionResult(
        success=True,
        summary="ok",
        repair_result=None,
        applied_results=(),
    )

    ctx = _make_context(
        planner,
        config=AgentConfiguration(max_goals=1),
        executor=executor,
        reasoning_result=_make_reasoning_result(next_action="continue"),
    )
    loop = AgentLoop(ctx)

    session = loop.run("objective")

    planner.plan.assert_called_once()
    assert len(session.completed_goals) == 1
    assert session.completed_goals == ["g1"]
    assert ctx.executor.run.call_count == 1
    ctx.goal_manager.complete_goal.assert_called_once_with("g1")