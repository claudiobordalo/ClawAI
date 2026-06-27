from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from clawai.agent import AgentConfiguration, AgentContext, AgentLoop
from clawai.config.agent_config import AgentConfig
from clawai.cognition import CognitiveFactory, ReasoningEngine
from clawai.engineering import EngineeringMemory
from clawai.goals import GoalEventBus, GoalManager, GoalPlanner
from clawai.agent import RetryPolicy
from clawai.executor import AbstractExecutor


def test_agent_config_defaults() -> None:
    config = AgentConfig()

    assert config.max_iterations == 10
    assert config.memory_messages_limit == 10
    assert config.provider_timeout == 30.0
    assert config.provider_temperature == 0.7
    assert config.provider_max_tokens == 1024
    assert config.enable_tools is True
    assert config.enable_memory is True
    assert config.enable_workspace is True
    assert config.enable_system_prompt is True
    assert config.enable_tool_discovery is True


def test_agent_config_immutable() -> None:
    config = AgentConfig()

    with pytest.raises(Exception):
        config.max_iterations = 20  # type: ignore[assignment]


def _make_context(*, config: AgentConfiguration, planner: MagicMock | None = None, executor: MagicMock | None = None) -> AgentContext:
    planner_obj = planner if planner is not None else GoalPlanner()
    executor_obj = executor if executor is not None else MagicMock(spec=AbstractExecutor)

    # GoalPlanner -> GoalBacklog -> goals will be iterated by AgentLoop
    mem = EngineeringMemory()
    gm = GoalManager(MagicMock())

    # Use EngineeringMemoryGoalRepository contract via GoalManager? GoalManager implementation expects repository.
    # In these tests we mock goal_manager directly where needed, so keep gm unused.
    # However AgentLoop uses gm methods -> so we still provide a real GoalManager for method presence.
    event_bus = GoalEventBus()

    return AgentContext(
        planner=planner_obj,
        goal_manager=gm,
        executor=executor_obj,
        memory=mem,
        event_bus=event_bus,
        reasoning_engine=CognitiveFactory().create_reasoning_engine(),
        retry_policy=RetryPolicy(),
        config=config,
        checkpoint_manager=None,
    )


def test_agent_loop_accepts_agent_configuration_from_context() -> None:
    # Validates AgentLoop public API: AgentLoop(context).run(objective) uses context.config.
    config = AgentConfiguration(max_goals=1)

    # Mock planner to return exactly 1 goal, AgentLoop will execute it once.
    planner = MagicMock(spec=GoalPlanner)
    from clawai.goals import GoalBacklog, Goal

    planner.plan.return_value = GoalBacklog(
        goals=(Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1),),
    )

    # Mock goal_manager to track completion calls.
    goal_manager = MagicMock()
    goal_manager.add_goal.return_value = MagicMock()
    goal_manager.create_backlog.return_value = MagicMock()
    goal_manager.complete_goal.return_value = None
    goal_manager.fail_goal.return_value = None

    # Mock executor to succeed.
    executor = MagicMock()
    from clawai.executor import ExecutionRequest, ExecutionResult

    executor.run.return_value = ExecutionResult(success=True, summary="ok", repair_result=None, applied_results=())

    ctx = AgentContext(
        planner=planner,
        goal_manager=goal_manager,
        executor=executor,
        memory=MagicMock(),
        event_bus=GoalEventBus(),
        reasoning_engine=MagicMock(analyze=MagicMock(return_value=MagicMock(
            assessment=MagicMock(value="review"),
            next_action="continue",
            should_retry=False,
            failure_category="cat",
            confidence=0.9,
            recommendation="dec",
            reason="r",
        ))),
        retry_policy=MagicMock(max_retries=0, base_delay=0.0, compute_delay=MagicMock(return_value=0.0), is_retryable=MagicMock(return_value=False)),
        config=config,
        checkpoint_manager=None,
    )

    loop = AgentLoop(ctx)
    session = loop.run("objective")

    assert session.state.value == "completed" or session.state.name == "COMPLETED"
    assert len(session.completed_goals) <= 1
    goal_manager.complete_goal.assert_called()


def test_agent_loop_stops_when_max_goals_reached() -> None:
    # Validates AgentLoop uses context.config.max_goals.
    config = AgentConfiguration(max_goals=1)

    planner = MagicMock(spec=GoalPlanner)
    from clawai.goals import GoalBacklog, Goal

    planner.plan.return_value = GoalBacklog(
        goals=(
            Goal(id="g1", title="t1", description="d", success_criteria="s", priority=1),
            Goal(id="g2", title="t2", description="d", success_criteria="s", priority=1),
        ),
    )

    goal_manager = MagicMock()
    goal_manager.add_goal.return_value = MagicMock()
    goal_manager.create_backlog.return_value = MagicMock()
    goal_manager.complete_goal.return_value = None
    goal_manager.fail_goal.return_value = None

    executor = MagicMock()
    from clawai.executor import ExecutionResult

    executor.run.return_value = ExecutionResult(success=True, summary="ok", repair_result=None, applied_results=())

    reasoning_result = MagicMock(
        assessment=MagicMock(value="review"),
        next_action="continue",
        should_retry=False,
        failure_category="cat",
        confidence=0.9,
        recommendation="dec",
        reason="r",
    )

    ctx = AgentContext(
        planner=planner,
        goal_manager=goal_manager,
        executor=executor,
        memory=MagicMock(),
        event_bus=GoalEventBus(),
        reasoning_engine=MagicMock(analyze=MagicMock(return_value=reasoning_result)),
        retry_policy=MagicMock(max_retries=0, compute_delay=MagicMock(return_value=0.0), is_retryable=MagicMock(return_value=False)),
        config=config,
        checkpoint_manager=None,
    )

    loop = AgentLoop(ctx)
    session = loop.run("objective")

    # With max_goals=1, loop should not complete more than 1 goal.
    assert len(session.completed_goals) <= 1

