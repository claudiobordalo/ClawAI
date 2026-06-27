from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from clawai.agent.agent_engine import AgentEngine
from clawai.agent.agent_engine import AgentResult
from clawai.context.context_builder import ContextBuilder
from clawai.execution.action_executor import ActionExecutor
from clawai.llm.llm_executor import LLMExecutor
from clawai.llm.llm_executor import LLMResult
from clawai.parser.response_parser import ParseResult
from clawai.parser.response_parser import ResponseParser
from clawai.providers.base.response import ProviderResponse


@dataclass
class DummyIncrementalContextResult:
    context: str
    selected_files: list[str]


def _make_mock_workspace(*, tree_root: str = "/project") -> MagicMock:
    """Cria um Workspace mockado com get_tree e is_open."""
    workspace = MagicMock()
    workspace.is_open = True
    tree = MagicMock()
    tree.root = tree_root
    workspace.get_tree.return_value = tree
    return workspace


def _make_mission(*, objective: str = "Test objective") -> MagicMock:
    mission = MagicMock()
    mission.id = "m1"
    mission.objective = objective
    return mission


def _make_provider_response(content: str) -> ProviderResponse:
    return ProviderResponse(content=content, model="gpt-4", provider="openai")


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_agent_engine_initialization() -> None:
    """Injeção de dependência bem-sucedida."""
    engine = AgentEngine(
        context_builder=MagicMock(spec=ContextBuilder),
        llm_executor=MagicMock(spec=LLMExecutor),
        response_parser=MagicMock(spec=ResponseParser),
        action_executor=MagicMock(spec=ActionExecutor),
    )

    assert isinstance(engine.context_builder, ContextBuilder) or isinstance(
        engine.context_builder, MagicMock
    )
    assert isinstance(engine.llm_executor, LLMExecutor) or isinstance(
        engine.llm_executor, MagicMock
    )
    assert isinstance(engine.response_parser, ResponseParser) or isinstance(
        engine.response_parser, MagicMock
    )
    assert isinstance(engine.action_executor, ActionExecutor) or isinstance(
        engine.action_executor, MagicMock
    )


@pytest.mark.parametrize(
    "ctx_builder, llm_ex, resp_parser, action_ex, expected_msg",
    [
        (None, MagicMock(), MagicMock(), MagicMock(), "context_builder"),
        (MagicMock(), None, MagicMock(), MagicMock(), "llm_executor"),
        (MagicMock(), MagicMock(), None, MagicMock(), "response_parser"),
        (MagicMock(), MagicMock(), MagicMock(), None, "action_executor"),
    ],
)
def test_agent_engine_initialization_none_dependency_raises(
    ctx_builder,
    llm_ex,
    resp_parser,
    action_ex,
    expected_msg: str,
) -> None:
    """Cada dependência None dispara ValueError."""
    with pytest.raises(ValueError, match=expected_msg):
        AgentEngine(
            context_builder=ctx_builder,  # type: ignore[arg-type]
            llm_executor=llm_ex,  # type: ignore[arg-type]
            response_parser=resp_parser,  # type: ignore[arg-type]
            action_executor=action_ex,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Fluxo completo bem-sucedido
# ---------------------------------------------------------------------------


def test_execute_full_success_with_tool_action() -> None:
    """
    Fluxo completo bem-sucedido:
    ContextBuilder -> LLMExecutor -> ResponseParser -> ActionExecutor.
    """
    # --- Mocks ---
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.incremental_build.return_value = DummyIncrementalContextResult(
        context="contexto relevante",
        selected_files=["main.py"],
    )

    llm_executor = MagicMock(spec=LLMExecutor)
    llm_executor.execute.return_value = LLMResult(
        success=True,
        response=_make_provider_response(
            '{"type":"tool","tool":"filesystem.read_file","arguments":{"path":"README.md"}}'
        ),
    )

    response_parser = MagicMock(spec=ResponseParser)
    response_parser.parse.return_value = ParseResult(
        success=True,
        action={
            "type": "tool",
            "tool": "filesystem.read_file",
            "arguments": {"path": "README.md"},
        },
    )

    action_executor = MagicMock(spec=ActionExecutor)
    action_executor.execute.return_value = {
        "success": True,
        "tool": "filesystem.read_file",
        "result": {"content": "# Readme\n"},
        "error": None,
        "duration_ms": 10.5,
    }

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    mission = _make_mission()
    workspace = _make_mock_workspace()

    result = engine.execute(
        mission=mission,
        workspace=workspace,
        user_instruction="Leia o README.md",
    )

    # --- Asserts ---
    assert result.success is True
    assert result.llm_response is not None
    assert '"tool"' in result.llm_response
    assert result.action is not None
    assert result.action["type"] == "tool"
    assert result.action["tool"] == "filesystem.read_file"
    assert result.execution_result is not None
    assert result.execution_result["success"] is True
    assert result.error is None

    # --- Verificação da ordem correta das chamadas ---
    context_builder.incremental_build.assert_called_once_with(
        project=workspace.get_tree().root,
        objective=mission.objective,
    )
    llm_executor.execute.assert_called_once()
    response_parser.parse.assert_called_once()
    action_executor.execute.assert_called_once_with(result.action)


# ---------------------------------------------------------------------------
# Resposta textual sem Action
# ---------------------------------------------------------------------------


def test_execute_textual_response_without_action() -> None:
    """
    LLM responde com texto (não JSON), sem Action.
    O ciclo é bem-sucedido, mas action e execution_result são None.
    """
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.incremental_build.return_value = DummyIncrementalContextResult(
        context="contexto",
        selected_files=[],
    )

    llm_executor = MagicMock(spec=LLMExecutor)
    llm_executor.execute.return_value = LLMResult(
        success=True,
        response=_make_provider_response(
            "O arquivo README.md contém informações sobre o projeto."
        ),
    )

    response_parser = MagicMock(spec=ResponseParser)
    response_parser.parse.return_value = ParseResult(
        success=False,
        error="ResponseParser: resposta vazia.",
    )

    action_executor = MagicMock(spec=ActionExecutor)

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="Explique o projeto",
    )

    assert result.success is True
    assert result.llm_response is not None
    assert "README.md" in result.llm_response
    assert result.action is None
    assert result.execution_result is None
    assert result.error is None

    # ActionExecutor não deve ser chamado quando não há Action
    action_executor.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Falha no ContextBuilder
# ---------------------------------------------------------------------------


def test_execute_context_builder_failure() -> None:
    """
    Falha no ContextBuilder: exceção é capturada e retornada como erro.
    Etapas seguintes não devem ser executadas.
    """
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.incremental_build.side_effect = RuntimeError(
        "Erro ao construir contexto"
    )

    llm_executor = MagicMock(spec=LLMExecutor)
    response_parser = MagicMock(spec=ResponseParser)
    action_executor = MagicMock(spec=ActionExecutor)

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="Leia o README",
    )

    assert result.success is False
    assert result.llm_response is None
    assert result.action is None
    assert result.execution_result is None
    assert result.error is not None
    assert "ContextBuilder" in result.error
    assert "Erro ao construir contexto" in result.error

    # Etapas seguintes não executadas
    llm_executor.execute.assert_not_called()
    response_parser.parse.assert_not_called()
    action_executor.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Falha no LLMExecutor
# ---------------------------------------------------------------------------


def test_execute_llm_executor_failure() -> None:
    """
    Falha no LLMExecutor: exceção é capturada e retornada como erro.
    Etapas seguintes não devem ser executadas.
    """
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.incremental_build.return_value = DummyIncrementalContextResult(
        context="ctx", selected_files=[]
    )

    llm_executor = MagicMock(spec=LLMExecutor)
    llm_executor.execute.side_effect = ConnectionError("API indisponível")

    response_parser = MagicMock(spec=ResponseParser)
    action_executor = MagicMock(spec=ActionExecutor)

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="Leia o README",
    )

    assert result.success is False
    assert result.llm_response is None
    assert result.action is None
    assert result.execution_result is None
    assert result.error is not None
    assert "LLMExecutor" in result.error
    assert "API indisponível" in result.error

    response_parser.parse.assert_not_called()
    action_executor.execute.assert_not_called()


def test_execute_llm_executor_returns_failure() -> None:
    """
    LLMExecutor retorna LLMResult com success=False.
    O erro deve ser propagado sem executar etapas seguintes.
    """
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.incremental_build.return_value = DummyIncrementalContextResult(
        context="ctx", selected_files=[]
    )

    llm_executor = MagicMock(spec=LLMExecutor)
    llm_executor.execute.return_value = LLMResult(
        success=False,
        error="LLMExecutor: falha no Provider: Rate limit exceeded",
    )

    response_parser = MagicMock(spec=ResponseParser)
    action_executor = MagicMock(spec=ActionExecutor)

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="Leia o README",
    )

    assert result.success is False
    assert result.llm_response is None
    assert result.error is not None
    assert "Rate limit exceeded" in result.error

    response_parser.parse.assert_not_called()
    action_executor.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Falha no ResponseParser
# ---------------------------------------------------------------------------


def test_execute_response_parser_failure() -> None:
    """
    Falha no ResponseParser: exceção é capturada e retornada como erro.
    ActionExecutor não deve ser chamado.
    """
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.incremental_build.return_value = DummyIncrementalContextResult(
        context="ctx", selected_files=[]
    )

    llm_executor = MagicMock(spec=LLMExecutor)
    llm_executor.execute.return_value = LLMResult(
        success=True,
        response=_make_provider_response('{"type":"tool"...'),
    )

    response_parser = MagicMock(spec=ResponseParser)
    response_parser.parse.side_effect = ValueError("Erro no parse do JSON")

    action_executor = MagicMock(spec=ActionExecutor)

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="Execute ação",
    )

    assert result.success is False
    assert result.llm_response is not None
    assert result.action is None
    assert result.execution_result is None
    assert result.error is not None
    assert "ResponseParser" in result.error
    assert "Erro no parse do JSON" in result.error

    action_executor.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Falha no ActionExecutor
# ---------------------------------------------------------------------------


def test_execute_action_executor_failure() -> None:
    """
    Falha no ActionExecutor: exceção é capturada e retornada como erro.
    """
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.incremental_build.return_value = DummyIncrementalContextResult(
        context="ctx", selected_files=[]
    )

    llm_executor = MagicMock(spec=LLMExecutor)
    llm_executor.execute.return_value = LLMResult(
        success=True,
        response=_make_provider_response(
            '{"type":"tool","tool":"filesystem.read_file","arguments":{"path":"x"}}'
        ),
    )

    response_parser = MagicMock(spec=ResponseParser)
    response_parser.parse.return_value = ParseResult(
        success=True,
        action={
            "type": "tool",
            "tool": "filesystem.read_file",
            "arguments": {"path": "x"},
        },
    )

    action_executor = MagicMock(spec=ActionExecutor)
    action_executor.execute.side_effect = PermissionError("Acesso negado")

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="Leia arquivo",
    )

    assert result.success is False
    assert result.llm_response is not None
    assert result.action is not None
    assert result.execution_result is None
    assert result.error is not None
    assert "ActionExecutor" in result.error
    assert "Acesso negado" in result.error


def test_execute_action_executor_returns_failure() -> None:
    """
    ActionExecutor executa mas retorna success=False.
    O erro do contrato deve ser propagado.
    """
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.incremental_build.return_value = DummyIncrementalContextResult(
        context="ctx", selected_files=[]
    )

    llm_executor = MagicMock(spec=LLMExecutor)
    llm_executor.execute.return_value = LLMResult(
        success=True,
        response=_make_provider_response(
            '{"type":"tool","tool":"filesystem.read_file","arguments":{"path":"x"}}'
        ),
    )

    response_parser = MagicMock(spec=ResponseParser)
    response_parser.parse.return_value = ParseResult(
        success=True,
        action={"type": "tool", "tool": "filesystem.read_file", "arguments": {"path": "x"}},
    )

    action_executor = MagicMock(spec=ActionExecutor)
    action_executor.execute.return_value = {
        "success": False,
        "tool": "filesystem.read_file",
        "result": None,
        "error": "Arquivo não encontrado",
        "duration_ms": 5.0,
    }

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="Leia arquivo",
    )

    assert result.success is False
    assert result.llm_response is not None
    assert result.action is not None
    assert result.execution_result is not None
    assert result.execution_result["success"] is False
    assert result.error == "Arquivo não encontrado"


# ---------------------------------------------------------------------------
# Validação das entradas obrigatórias
# ---------------------------------------------------------------------------


def test_execute_mission_none_returns_error() -> None:
    """Mission None retorna erro padronizado."""
    engine = _make_valid_engine()
    result = engine.execute(
        mission=None,  # type: ignore[arg-type]
        workspace=MagicMock(),
        user_instruction="test",
    )

    assert result.success is False
    assert result.llm_response is None
    assert "mission" in (result.error or "")
    assert "obrigatório" in (result.error or "")


def test_execute_workspace_none_returns_error() -> None:
    """Workspace None retorna erro padronizado."""
    engine = _make_valid_engine()
    result = engine.execute(
        mission=_make_mission(),
        workspace=None,  # type: ignore[arg-type]
        user_instruction="test",
    )

    assert result.success is False
    assert "workspace" in (result.error or "")
    assert "obrigatório" in (result.error or "")


def test_execute_user_instruction_empty_returns_error() -> None:
    """User instruction vazia retorna erro padronizado."""
    engine = _make_valid_engine()
    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="",
    )

    assert result.success is False
    assert "user_instruction" in (result.error or "")
    assert "obrigatório" in (result.error or "")


def test_execute_user_instruction_none_returns_error() -> None:
    """User instruction None retorna erro padronizado."""
    engine = _make_valid_engine()
    result = engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction=None,  # type: ignore[arg-type]
    )

    assert result.success is False
    assert "user_instruction" in (result.error or "")
    assert "obrigatório" in (result.error or "")


def test_execute_mission_without_objective_returns_error() -> None:
    """Mission sem 'objective' retorna erro."""
    engine = _make_valid_engine()

    mission = MagicMock()
    mission.id = "m1"
    # Não define objective
    del mission.objective

    result = engine.execute(
        mission=mission,
        workspace=_make_mock_workspace(),
        user_instruction="test",
    )

    assert result.success is False
    assert "mission.objective" in (result.error or "")
    assert "obrigatório" in (result.error or "")


# ---------------------------------------------------------------------------
# Verificação da ordem correta das chamadas
# ---------------------------------------------------------------------------


def test_execute_call_order() -> None:
    """
    Verifica a ordem exata das chamadas entre os componentes:
    1. ContextBuilder.incremental_build
    2. LLMExecutor.execute
    3. ResponseParser.parse
    4. ActionExecutor.execute
    """
    call_tracker: list[str] = []

    context_builder = MagicMock(spec=ContextBuilder)

    def track_context(*args, **kwargs):
        call_tracker.append("context_builder")
        return DummyIncrementalContextResult(context="ctx", selected_files=[])

    context_builder.incremental_build.side_effect = track_context

    llm_executor = MagicMock(spec=LLMExecutor)

    def track_llm(*args, **kwargs):
        call_tracker.append("llm_executor")
        return LLMResult(
            success=True,
            response=_make_provider_response(
                '{"type":"tool","tool":"filesystem.list_dir","arguments":{"path":"."}}'
            ),
        )

    llm_executor.execute.side_effect = track_llm

    response_parser = MagicMock(spec=ResponseParser)

    def track_parse(*args, **kwargs):
        call_tracker.append("response_parser")
        return ParseResult(
            success=True,
            action={
                "type": "tool",
                "tool": "filesystem.list_dir",
                "arguments": {"path": "."},
            },
        )

    response_parser.parse.side_effect = track_parse

    action_executor = MagicMock(spec=ActionExecutor)

    def track_action(*args, **kwargs):
        call_tracker.append("action_executor")
        return {
            "success": True,
            "tool": "filesystem.list_dir",
            "result": {"files": ["a.txt"]},
            "error": None,
            "duration_ms": 1.0,
        }

    action_executor.execute.side_effect = track_action

    engine = AgentEngine(
        context_builder=context_builder,
        llm_executor=llm_executor,
        response_parser=response_parser,
        action_executor=action_executor,
    )

    engine.execute(
        mission=_make_mission(),
        workspace=_make_mock_workspace(),
        user_instruction="Liste diretório",
    )

    assert call_tracker == [
        "context_builder",
        "llm_executor",
        "response_parser",
        "action_executor",
    ]


# ---------------------------------------------------------------------------
# Propagação correta dos resultados
# ---------------------------------------------------------------------------


def test_agent_result_dataclass_contract() -> None:
    """
    AgentResult possui todos os campos do contrato padronizado.
    """
    result_ok = AgentResult(success=True)
    assert result_ok.success is True
    assert result_ok.llm_response is None
    assert result_ok.action is None
    assert result_ok.execution_result is None
    assert result_ok.error is None

    result_full = AgentResult(
        success=True,
        llm_response="resposta",
        action={"type": "tool"},
        execution_result={"success": True},
        error=None,
    )
    assert result_full.llm_response == "resposta"
    assert result_full.action == {"type": "tool"}
    assert result_full.execution_result == {"success": True}


def test_agent_result_immutability() -> None:
    """
    AgentResult é imutável (dataclass frozen).
    """
    result = AgentResult(success=True)

    with pytest.raises(AttributeError):
        result.success = False  # type: ignore[misc]

    with pytest.raises(AttributeError):
        result.llm_response = "novo"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        result.error = "erro"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Helper: engine válido para testes de validação
# ---------------------------------------------------------------------------


def _make_valid_engine() -> AgentEngine:
    """Cria um AgentEngine com todos os componentes mockados (não chamados)."""
    return AgentEngine(
        context_builder=MagicMock(spec=ContextBuilder),
        llm_executor=MagicMock(spec=LLMExecutor),
        response_parser=MagicMock(spec=ResponseParser),
        action_executor=MagicMock(spec=ActionExecutor),
    )