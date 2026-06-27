from __future__ import annotations

from unittest.mock import MagicMock

from clawai.agent.agent_engine import AgentResult
from clawai.agent.agent_loop import AgentLoop
from clawai.agent.agent_loop import LoopResult
from clawai.planning.planner import Planner


def _make_agent_engine_mock() -> MagicMock:
    return MagicMock()


def _make_textual_response(text: str = "final response") -> AgentResult:
    return AgentResult(success=True, llm_response=text, action=None, execution_result=None)


def _make_failed_execution() -> AgentResult:
    return AgentResult(
        success=False,
        llm_response="erro fatal",
        action=None,
        execution_result=None,
        error="AgentEngine failure",
    )


def test_run_without_planner_preserves_legacy_flow() -> None:
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_textual_response("legacy response")

    loop = AgentLoop(agent_engine=engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Executar tarefa legado",
    )

    assert result.success is True
    assert result.iterations == 1
    assert result.final_response == "legacy response"
    assert result.error is None
    engine.execute.assert_called_once()
    _, kwargs = engine.execute.call_args
    assert kwargs["user_instruction"] == "Executar tarefa legado"


def test_run_with_planner_executes_single_plan_step() -> None:
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_textual_response("planner response")
    planner = Planner()

    loop = AgentLoop(agent_engine=engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Executar tarefa planejada",
        planner=planner,
    )

    assert result.success is True
    assert result.iterations == 1
    assert result.final_response == "planner response"
    assert result.error is None
    assert len(result.history) == 1
    engine.execute.assert_called_once()
    _, kwargs = engine.execute.call_args
    assert kwargs["user_instruction"] == "Executar tarefa planejada"


def test_run_with_planner_marks_step_completed_when_engine_succeeds() -> None:
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_textual_response("step completed")
    planner = MagicMock(spec=Planner)
    planner.create_plan.return_value = planner_plan = MagicMock()
    planner.next_step.side_effect = [MagicMock(id="step-1", description="Executar tarefa planejada"), None]
    planner.complete_step.return_value = planner_plan

    loop = AgentLoop(agent_engine=engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Executar tarefa planejada",
        planner=planner,
    )

    assert result.success is True
    assert result.iterations == 1
    planner.create_plan.assert_called_once_with("Executar tarefa planejada")
    planner.next_step.assert_called()
    planner.complete_step.assert_called_once_with(planner_plan, "step-1")
    planner.fail_step.assert_not_called()


def test_run_with_planner_marks_step_failed_when_execution_fails() -> None:
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_failed_execution()
    planner = MagicMock(spec=Planner)
    planner.create_plan.return_value = planner_plan = MagicMock()
    planner.next_step.side_effect = [MagicMock(id="step-1", description="Executar tarefa planejada"), None]
    planner.fail_step.return_value = planner_plan

    loop = AgentLoop(agent_engine=engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Executar tarefa planejada",
        planner=planner,
    )

    assert result.success is False
    assert result.error == "AgentEngine failure"
    assert result.iterations == 1
    planner.create_plan.assert_called_once_with("Executar tarefa planejada")
    planner.next_step.assert_called()
    planner.fail_step.assert_called_once_with(planner_plan, "step-1")
    planner.complete_step.assert_not_called()


def test_planner_path_not_used_when_planner_is_none() -> None:
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_textual_response("legacy response")

    loop = AgentLoop(agent_engine=engine)
    loop._run_with_planner = MagicMock()

    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Executar tarefa legado",
    )

    assert result.success is True
    loop._run_with_planner.assert_not_called()
