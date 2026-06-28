from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from clawai.agent.agent_context import AgentConfiguration
from clawai.agent.agent_context import AgentContext
from clawai.agent.agent_loop import AgentLoop
from clawai.agent.execution_events import COGNITIVE_DECISION
from clawai.agent.execution_events import COGNITIVE_REVIEW
from clawai.agent.execution_events import EXECUTOR_FINISHED
from clawai.agent.execution_events import EXECUTOR_STARTED
from clawai.agent.execution_events import GOAL_FAILED
from clawai.agent.execution_events import GOAL_FINISHED
from clawai.agent.execution_events import GOAL_RETRIED
from clawai.agent.execution_events import GOAL_STARTED
from clawai.agent.execution_events import PLANNER_FINISHED
from clawai.agent.execution_events import PLANNER_STARTED
from clawai.agent.execution_events import REPLAN_COMPLETED
from clawai.agent.execution_events import REPLAN_STARTED
from clawai.agent.execution_events import SESSION_CANCELLED
from clawai.agent.execution_events import SESSION_FINISHED
from clawai.agent.execution_events import SESSION_STARTED
from clawai.agent.execution_session import ExecutionSession
from clawai.agent.execution_state import ExecutionState
from clawai.agent.goal_execution_result import GoalExecutionResult
from clawai.agent.retry_policy import RetryPolicy
from clawai.executor import ExecutionRequest
from clawai.goals import Goal
from clawai.goals import GoalBacklog
from clawai.goals import GoalPriority
from clawai.goals import GoalStatus
from clawai.goals import PlanningContext


def _make_goal(
    goal_id: str = "g1",
    title: str = "Implementar ajuste",
    description: str = "Atualizar o comportamento do loop.",
) -> Goal:
    return Goal(
        id=goal_id,
        title=title,
        description=description,
        success_criteria="Concluir a alteração sem quebrar os testes.",
        priority=GoalPriority.HIGH,
        status=GoalStatus.TODO,
        tags=("agent-loop",),
    )


def _make_reasoning(
    *,
    next_action: str = "continue",
    should_retry: bool = False,
    assessment_value: str = "continue",
    failure_category: str | None = None,
    confidence: float = 0.9,
    reason: str = "ok",
    recommendation: str = "continue",
) -> SimpleNamespace:
    return SimpleNamespace(
        assessment=SimpleNamespace(value=assessment_value),
        next_action=next_action,
        should_retry=should_retry,
        failure_category=failure_category,
        confidence=confidence,
        reason=reason,
        recommendation=recommendation,
    )


def _make_execution_result(
    *,
    success: bool = True,
    summary: str = "concluído",
    error: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        success=success,
        summary=summary,
        error=error,
    )


def _make_context(
    *,
    auto_replan: bool = True,
    max_goals: int = 0,
    max_retries: int = 1,
) -> AgentContext:
    planner = MagicMock()
    goal_manager = MagicMock()
    executor = MagicMock()
    memory = MagicMock()
    event_bus = MagicMock()
    reasoning_engine = MagicMock()
    retry_policy = RetryPolicy(
        max_retries=max_retries,
        base_delay=0.0,
        backoff_factor=1.0,
    )
    config = AgentConfiguration(
        max_goals=max_goals,
        auto_replan=auto_replan,
        checkpoint_enabled=False,
    )

    return AgentContext(
        planner=planner,
        goal_manager=goal_manager,
        executor=executor,
        memory=memory,
        event_bus=event_bus,
        reasoning_engine=reasoning_engine,
        retry_policy=retry_policy,
        config=config,
    )


def _make_loop(context: AgentContext | None = None) -> AgentLoop:
    return AgentLoop(context or _make_context())


def _event_types(event_bus: MagicMock) -> list[str]:
    return [call.args[0] for call in event_bus.emit.call_args_list]


def test_agent_loop_initialization_keeps_context_and_metrics() -> None:
    context = _make_context()
    loop = AgentLoop(context)

    assert loop.context is context
    assert loop.metrics.goals_completed == 0
    assert loop.metrics.goals_failed == 0
    assert loop.metrics.goals_retried == 0
    assert loop.is_cancelled is False


def test_run_completes_without_goals() -> None:
    context = _make_context()
    context.planner.plan.return_value = GoalBacklog(goals=tuple())

    loop = _make_loop(context)
    session = loop.run("objetivo vazio")

    assert isinstance(session, ExecutionSession)
    assert session.state == ExecutionState.COMPLETED
    assert session.started_at is not None
    assert session.finished_at is not None
    assert session.current_goal is None
    assert session.results == []
    assert session.completed_goals == []
    assert session.failed_goals == []
    assert context.session is session

    context.planner.plan.assert_called_once()
    call = context.planner.plan.call_args
    assert call.args == ("objetivo vazio",)
    planning_context = call.kwargs["context"]
    assert isinstance(planning_context, PlanningContext)
    assert planning_context.objective == "objetivo vazio"
    assert planning_context.previous_attempts == 0
    assert planning_context.repository_state == []

    emitted = _event_types(context.event_bus)
    assert SESSION_STARTED in emitted
    assert PLANNER_STARTED in emitted
    assert PLANNER_FINISHED in emitted
    assert SESSION_FINISHED in emitted
    assert GOAL_STARTED not in emitted
    assert GOAL_FINISHED not in emitted


def test_run_completes_successful_goal() -> None:
    context = _make_context(auto_replan=False)
    goal = _make_goal()
    context.planner.plan.return_value = GoalBacklog(goals=(goal,))
    context.executor.run.return_value = _make_execution_result(
        success=True,
        summary="arquivo atualizado",
        error=None,
    )
    context.reasoning_engine.analyze.return_value = _make_reasoning(
        next_action="continue",
        should_retry=False,
        assessment_value="continue",
        confidence=0.95,
        reason="tudo certo",
        recommendation="continue",
    )

    loop = _make_loop(context)
    session = loop.run("ajustar o agente")

    assert session.state == ExecutionState.COMPLETED
    assert session.current_goal == goal.id
    assert session.completed_goals == [goal.id]
    assert session.failed_goals == []
    assert len(session.results) == 1

    result = session.results[0]
    assert isinstance(result, GoalExecutionResult)
    assert result.goal == goal
    assert result.success is True
    assert result.output == "arquivo atualizado"
    assert result.requires_replan is False
    assert result.attempts == 1
    assert result.next_action == "continue"

    context.goal_manager.add_goal.assert_called_once_with(goal)
    context.goal_manager.create_backlog.assert_called_once()
    context.goal_manager.complete_goal.assert_called_once_with(goal.id)
    context.goal_manager.fail_goal.assert_not_called()

    context.executor.run.assert_called_once()
    request = context.executor.run.call_args.args[0]
    assert isinstance(request, ExecutionRequest)
    assert request.objective == goal.title
    assert request.target_query == goal.title
    assert request.instructions == goal.description
    assert request.max_iterations == 3

    reasoning_call = context.reasoning_engine.analyze.call_args.kwargs
    assert reasoning_call["goal_id"] == goal.id
    assert reasoning_call["goal_title"] == goal.title
    assert reasoning_call["success"] is True
    assert reasoning_call["errors"] is None
    assert reasoning_call["output"] == "arquivo atualizado"

    emitted = _event_types(context.event_bus)
    assert GOAL_STARTED in emitted
    assert EXECUTOR_STARTED in emitted
    assert EXECUTOR_FINISHED in emitted
    assert COGNITIVE_REVIEW in emitted
    assert COGNITIVE_DECISION in emitted
    assert GOAL_FINISHED in emitted
    assert SESSION_FINISHED in emitted


def test_run_retries_then_succeeds() -> None:
    context = _make_context(auto_replan=False, max_retries=1)
    goal = _make_goal(goal_id="g2", title="Tarefa com retry")
    context.planner.plan.return_value = GoalBacklog(goals=(goal,))
    context.executor.run.side_effect = [
        _make_execution_result(success=False, summary="falhou 1", error="erro temporário"),
        _make_execution_result(success=True, summary="falhou 1 corrigido", error=None),
    ]
    context.reasoning_engine.analyze.side_effect = [
        _make_reasoning(
            next_action="retry",
            should_retry=True,
            assessment_value="retry",
            confidence=0.4,
            reason="tentar novamente",
            recommendation="retry",
        ),
        _make_reasoning(
            next_action="continue",
            should_retry=False,
            assessment_value="continue",
            confidence=0.9,
            reason="corrigido",
            recommendation="continue",
        ),
    ]

    loop = _make_loop(context)

    from unittest.mock import patch

    with patch("clawai.agent.agent_loop.time.sleep", return_value=None):
        session = loop.run("executar com retry")

    assert session.state == ExecutionState.COMPLETED
    assert session.completed_goals == [goal.id]
    assert session.failed_goals == []
    assert len(session.results) == 1
    assert session.results[0].attempts == 2
    assert session.results[0].success is True

    assert context.executor.run.call_count == 2
    context.goal_manager.complete_goal.assert_called_once_with(goal.id)
    assert context.goal_manager.fail_goal.call_count == 0
    assert GOAL_RETRIED in _event_types(context.event_bus)


def test_run_replans_when_goal_requires_replan() -> None:
    context = _make_context(auto_replan=True)
    goal = _make_goal(goal_id="g3", title="Replanejar")
    context.planner.plan.side_effect = [
        GoalBacklog(goals=(goal,)),
        GoalBacklog(goals=tuple()),
    ]
    context.executor.run.return_value = _make_execution_result(
        success=False,
        summary="checagem falhou",
        error="regra violada",
    )
    context.reasoning_engine.analyze.return_value = _make_reasoning(
        next_action="replan",
        should_retry=False,
        assessment_value="failed",
        failure_category="validation",
        confidence=0.2,
        reason="precisa replanejar",
        recommendation="replan",
    )

    loop = _make_loop(context)
    session = loop.run("replanejar tarefa")

    assert session.state == ExecutionState.COMPLETED
    assert session.failed_goals == [goal.id]
    assert session.completed_goals == []
    assert len(session.results) == 1
    assert session.results[0].success is False
    assert session.results[0].requires_replan is True

    assert context.planner.plan.call_count == 2
    first_ctx = context.planner.plan.call_args_list[0].kwargs["context"]
    second_ctx = context.planner.plan.call_args_list[1].kwargs["context"]

    assert isinstance(first_ctx, PlanningContext)
    assert first_ctx.previous_attempts == 0
    assert first_ctx.repository_state == []

    assert isinstance(second_ctx, PlanningContext)
    assert second_ctx.previous_attempts == 1
    assert list(second_ctx.repository_state) == [goal]

    context.goal_manager.fail_goal.assert_called_once_with(goal.id)
    context.goal_manager.complete_goal.assert_not_called()

    emitted = _event_types(context.event_bus)
    assert REPLAN_STARTED in emitted
    assert REPLAN_COMPLETED in emitted
    assert PLANNER_STARTED in emitted
    assert PLANNER_FINISHED in emitted
    assert GOAL_FAILED in emitted


def test_run_cancels_before_goal_execution() -> None:
    context = _make_context()
    goal = _make_goal(goal_id="g4", title="Cancelar")
    context.planner.plan.return_value = GoalBacklog(goals=(goal,))

    loop = _make_loop(context)
    loop.cancel()

    session = loop.run("cancelar execução")

    assert session.state == ExecutionState.CANCELLED
    assert session.completed_goals == []
    assert session.failed_goals == []
    assert session.results == []
    assert context.executor.run.call_count == 0
    assert SESSION_CANCELLED in _event_types(context.event_bus)
    assert SESSION_FINISHED in _event_types(context.event_bus)


def test_run_sets_session_on_context() -> None:
    context = _make_context()
    context.planner.plan.return_value = GoalBacklog(goals=tuple())

    loop = _make_loop(context)
    session = loop.run("vincular sessão")

    assert context.session is session
    assert isinstance(context.session, ExecutionSession)
    assert context.session.objective == "vincular sessão"


def test_run_respects_max_goals_limit() -> None:
    context = _make_context(max_goals=1)
    goal = _make_goal(goal_id="g5", title="Limite")
    context.planner.plan.return_value = GoalBacklog(goals=(goal,))
    context.executor.run.return_value = _make_execution_result(
        success=True,
        summary="ok",
        error=None,
    )

    context.reasoning_engine.analyze.return_value = _make_reasoning(
        next_action="continue",
        should_retry=False,
        assessment_value="continue",
    )

    loop = _make_loop(context)
    session = loop.run("limitar execução")
    # print(context.executor.run.call_args_list)
    assert session.state == ExecutionState.COMPLETED
    context.goal_manager.add_goal.assert_called_once_with(goal)
    context.goal_manager.create_backlog.assert_called_once()
    assert context.executor.run.call_count == 1

    context.goal_manager.complete_goal.assert_called_once_with(goal.id)
    context.goal_manager.fail_goal.assert_not_called()

    assert session.completed_goals == [goal.id]
    assert session.failed_goals == []

    request = context.executor.run.call_args.args[0]
    assert request.objective == goal.title

    # context.executor.run.assert_not_called()
    # assert session.completed_goals == []
    # assert session.failed_goals == []
