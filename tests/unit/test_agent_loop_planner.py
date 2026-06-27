from __future__ import annotations

from unittest.mock import MagicMock

from clawai.agent.agent_context import AgentConfiguration, AgentContext
from clawai.agent.agent_loop import AgentLoop
from clawai.cognition import CognitiveFactory
from clawai.executor import ExecutionResult
from clawai.goals import GoalBacklog, GoalEventBus, GoalPlanner, PlanningContext, Goal
from clawai.agent import RetryPolicy


def _make_ctx(planner: MagicMock, *, config: AgentConfiguration) -> AgentContext:
    # Production validates: AgentLoop(context).run(objective) calls context.planner.plan(objective, context=PlanningContext(...))
    goal_manager = MagicMock()
    goal_manager.add_goal.return_value = MagicMock()
    goal_manager.create_backlog.return_value = MagicMock()
    goal_manager.complete_goal.return_value = None
    goal_manager.fail_goal.return_value = None

    executor = MagicMock()
    executor.run.return_value = ExecutionResult(
        success=True,
        summary="ok",
        repair_result=None,
        applied_results=(),
    )

    reasoning_engine = MagicMock()
    reasoning_engine.analyze.return_value = MagicMock(
        assessment=MagicMock(value="review"),
        next_action="continue",
        should_retry=False,
        failure_category="cat",
        confidence=0.9,
        recommendation="dec",
        reason="r",
    )

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


def test_agent_loop_uses_planner_plan_and_runs_goals_when_backlog_has_goals() -> None:
    # Validates public API: AgentLoop.run(objective) uses context.planner.plan and executes returned GoalBacklog.goals.
    planner = MagicMock(spec=GoalPlanner)
    planner.plan.return_value = GoalBacklog(
        goals=(Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1),)
    )

    ctx = _make_ctx(planner, config=AgentConfiguration(max_goals=0))
    loop = AgentLoop(ctx)

    session = loop.run("objective")

    assert planner.plan.called
    _, kwargs = planner.plan.call_args
    assert "context" in kwargs

    assert session.state.value == "completed" or session.state.name == "COMPLETED"
    assert len(session.completed_goals) == 1


def test_agent_loop_completes_zero_when_planner_returns_empty_backlog() -> None:
    # Validates public API: if planner.plan returns GoalBacklog with no goals, session completes without executing any goal.
    planner = MagicMock(spec=GoalPlanner)
    planner.plan.return_value = GoalBacklog(goals=())

    ctx = _make_ctx(planner, config=AgentConfiguration(max_goals=0))
    loop = AgentLoop(ctx)

    session = loop.run("objective")

    assert session.completed_goals == []
    assert session.failed_goals == []


def test_agent_loop_marks_goal_failed_when_executor_reports_failure() -> None:
    # Validates public API: executor.run success=False triggers GoalExecutionResult with requires_replan=True and session.failed_goals updated.
    planner = MagicMock(spec=GoalPlanner)
    planner.plan.return_value = GoalBacklog(
        goals=(Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1),)
    )

    ctx = _make_ctx(planner, config=AgentConfiguration(max_goals=0))
    ctx.executor.run.return_value = ExecutionResult(
        success=False,
        summary="failed",
        error="boom",
        repair_result=None,
        applied_results=(),
    )
    # Force reasoning engine to follow failure path (not continue)
    ctx.reasoning_engine.analyze.return_value = MagicMock(
        assessment=MagicMock(value="review"),
        next_action="retry",
        should_retry=False,
        failure_category="cat",
        confidence=0.2,
        recommendation="dec",
        reason="r",
    )

    loop = AgentLoop(ctx)
    session = loop.run("objective")

    assert len(session.failed_goals) == 1

