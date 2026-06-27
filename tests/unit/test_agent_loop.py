from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from clawai.agent.agent_engine import AgentEngine
from clawai.agent.agent_engine import AgentResult
from clawai.agent.agent_loop import AgentLoop
from clawai.agent.agent_loop import IterationRecord
from clawai.agent.agent_loop import LoopResult
from clawai.providers.base.response import ProviderResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent_engine_mock() -> MagicMock:
    """Cria um AgentEngine mockado com spec."""
    return MagicMock(spec=AgentEngine)


def _make_engine_result(
    *,
    success: bool = True,
    llm_response: str | None = "resposta do LLM",
    action: dict[str, Any] | None = None,
    execution_result: dict[str, Any] | None = None,
    error: str | None = None,
) -> AgentResult:
    return AgentResult(
        success=success,
        llm_response=llm_response,
        action=action,
        execution_result=execution_result,
        error=error,
    )


def _make_successful_tool_action(
    *,
    tool: str = "filesystem.read_file",
    arguments: dict[str, Any] | None = None,
    result_content: Any = None,
) -> AgentResult:
    """Helper para criar um AgentResult de sucesso com Action tool."""
    if arguments is None:
        arguments = {"path": "test.txt"}
    if result_content is None:
        result_content = {"content": "# Conteúdo do arquivo"}

    return _make_engine_result(
        success=True,
        llm_response=f'{{"type":"tool","tool":"{tool}","arguments":{arguments}}}',
        action={"type": "tool", "tool": tool, "arguments": arguments},
        execution_result={
            "success": True,
            "tool": tool,
            "result": result_content,
            "error": None,
            "duration_ms": 5.0,
        },
    )


def _make_failed_tool_action(
    *,
    tool: str = "filesystem.read_file",
    arguments: dict[str, Any] | None = None,
    error_msg: str = "Arquivo não encontrado",
) -> AgentResult:
    """Helper para criar um AgentResult com Action tool que falhou."""
    if arguments is None:
        arguments = {"path": "inexistente.txt"}

    return _make_engine_result(
        success=True,
        llm_response=f'{{"type":"tool","tool":"{tool}","arguments":{arguments}}}',
        action={"type": "tool", "tool": tool, "arguments": arguments},
        execution_result={
            "success": False,
            "tool": tool,
            "result": None,
            "error": error_msg,
            "duration_ms": 3.0,
        },
    )


def _make_textual_response(text: str = "Resposta textual final") -> AgentResult:
    """Helper para criar um AgentResult de sucesso sem Action (apenas texto)."""
    return _make_engine_result(
        success=True,
        llm_response=text,
        action=None,
        execution_result=None,
    )


def _make_loop(agent_engine: MagicMock | None = None) -> AgentLoop:
    """Cria um AgentLoop com engine mockado."""
    if agent_engine is None:
        agent_engine = _make_agent_engine_mock()
    return AgentLoop(agent_engine=agent_engine)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_agent_loop_initialization() -> None:
    """Injeção de dependência bem-sucedida."""
    engine = _make_agent_engine_mock()
    loop = AgentLoop(agent_engine=engine)

    assert loop.agent_engine is engine


def test_agent_loop_initialization_none_raises() -> None:
    """AgentEngine None dispara ValueError."""
    with pytest.raises(ValueError, match="agent_engine"):
        AgentLoop(agent_engine=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Validação de entradas
# ---------------------------------------------------------------------------


def test_run_mission_none_returns_error() -> None:
    """Mission None retorna erro padronizado."""
    loop = _make_loop()
    result = loop.run(
        mission=None,  # type: ignore[arg-type]
        workspace=MagicMock(),
        user_instruction="test",
    )

    assert result.success is False
    assert result.iterations == 0
    assert "mission" in (result.error or "")
    assert "obrigatório" in (result.error or "")


def test_run_workspace_none_returns_error() -> None:
    """Workspace None retorna erro padronizado."""
    loop = _make_loop()
    result = loop.run(
        mission=MagicMock(),
        workspace=None,  # type: ignore[arg-type]
        user_instruction="test",
    )

    assert result.success is False
    assert result.iterations == 0
    assert "workspace" in (result.error or "")
    assert "obrigatório" in (result.error or "")


def test_run_user_instruction_empty_returns_error() -> None:
    """User instruction vazia retorna erro padronizado."""
    loop = _make_loop()
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="",
    )

    assert result.success is False
    assert result.iterations == 0
    assert "user_instruction" in (result.error or "")
    assert "obrigatório" in (result.error or "")


def test_run_user_instruction_none_returns_error() -> None:
    """User instruction None retorna erro padronizado."""
    loop = _make_loop()
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction=None,  # type: ignore[arg-type]
    )

    assert result.success is False
    assert result.iterations == 0
    assert "user_instruction" in (result.error or "")
    assert "obrigatório" in (result.error or "")


def test_run_max_iterations_zero_returns_error() -> None:
    """max_iterations = 0 retorna erro."""
    loop = _make_loop()
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="test",
        max_iterations=0,
    )

    assert result.success is False
    assert result.iterations == 0
    assert "max_iterations" in (result.error or "")
    assert ">= 1" in (result.error or "")


# ---------------------------------------------------------------------------
# Execução sem Actions (resposta textual)
# ---------------------------------------------------------------------------


def test_run_no_actions_textual_response() -> None:
    """
    LLM responde apenas com texto, sem Action.
    O loop deve encerrar imediatamente com sucesso.
    """
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_textual_response(
        "O arquivo README.md contém informações do projeto."
    )

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Explique o projeto",
    )

    assert result.success is True
    assert result.iterations == 1
    assert result.final_response == "O arquivo README.md contém informações do projeto."
    assert result.last_action is None
    assert result.error is None
    assert len(result.history) == 1
    assert result.history[0].iteration == 1
    assert result.history[0].action is None
    assert result.history[0].execution_result is None

    # AgentEngine executado apenas uma vez
    engine.execute.assert_called_once()


# ---------------------------------------------------------------------------
# Uma Action
# ---------------------------------------------------------------------------


def test_run_one_action_then_stop() -> None:
    """
    LLM executa uma Action com sucesso e depois responde apenas com texto.
    O loop deve executar 2 iterações e encerrar.
    """
    engine = _make_agent_engine_mock()
    engine.execute.side_effect = [
        _make_successful_tool_action(
            tool="filesystem.read_file",
            arguments={"path": "README.md"},
            result_content={"content": "# Projeto\n"},
        ),
        _make_textual_response("Arquivo lido com sucesso. Conteúdo: # Projeto"),
    ]

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Leia o README.md",
    )

    assert result.success is True
    assert result.iterations == 2
    assert result.final_response == "Arquivo lido com sucesso. Conteúdo: # Projeto"
    assert result.last_action is not None
    assert result.last_action["tool"] == "filesystem.read_file"
    assert result.error is None

    # Histórico com 2 iterações
    assert len(result.history) == 2
    assert result.history[0].iteration == 1
    assert result.history[0].action is not None
    assert result.history[0].action["tool"] == "filesystem.read_file"
    assert result.history[0].execution_result is not None
    assert result.history[0].execution_result["success"] is True

    assert result.history[1].iteration == 2
    assert result.history[1].action is None
    assert result.history[1].execution_result is None

    # AgentEngine executado 2 vezes
    assert engine.execute.call_count == 2


# ---------------------------------------------------------------------------
# Múltiplas Actions
# ---------------------------------------------------------------------------


def test_run_multiple_actions_then_stop() -> None:
    """
    LLM executa múltiplas Actions sucessivas e depois responde apenas texto.
    """
    engine = _make_agent_engine_mock()
    engine.execute.side_effect = [
        _make_successful_tool_action(
            tool="filesystem.read_file",
            arguments={"path": "src/main.py"},
            result_content={"content": "def main():\n    pass"},
        ),
        _make_successful_tool_action(
            tool="filesystem.search",
            arguments={"pattern": "*.py"},
            result_content={"files": ["main.py", "utils.py"]},
        ),
        _make_textual_response(
            "Encontrados 2 arquivos Python. O principal é main.py."
        ),
    ]

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Analise o código fonte",
    )

    assert result.success is True
    assert result.iterations == 3
    assert result.error is None

    # Histórico com 3 iterações
    assert len(result.history) == 3

    # Iteração 1: read_file
    assert result.history[0].iteration == 1
    assert result.history[0].action["tool"] == "filesystem.read_file"

    # Iteração 2: search
    assert result.history[1].iteration == 2
    assert result.history[1].action["tool"] == "filesystem.search"

    # Iteração 3: apenas texto
    assert result.history[2].iteration == 3
    assert result.history[2].action is None

    assert engine.execute.call_count == 3


# ---------------------------------------------------------------------------
# Encerramento por ausência de Action
# ---------------------------------------------------------------------------


def test_run_stops_when_no_action() -> None:
    """
    O loop encerra imediatamente quando o LLM não retorna Action.
    """
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_textual_response("Resposta final.")

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Diga algo",
    )

    assert result.success is True
    assert result.iterations == 1
    assert result.final_response == "Resposta final."
    assert result.last_action is None
    assert len(result.history) == 1

    engine.execute.assert_called_once()


# ---------------------------------------------------------------------------
# Encerramento por max_iterations
# ---------------------------------------------------------------------------


def test_run_stops_at_max_iterations() -> None:
    """
    LLM sempre retorna Action. O loop deve encerrar quando atingir
    max_iterations, com erro padronizado.
    """
    engine = _make_agent_engine_mock()
    # Sempre retorna Action (nunca para)
    engine.execute.return_value = _make_successful_tool_action(
        tool="filesystem.read_file",
        arguments={"path": "x.txt"},
        result_content={"content": "data"},
    )

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Execute",
        max_iterations=3,
    )

    assert result.success is False
    assert result.iterations == 3
    assert result.error is not None
    assert "máximo" in result.error or "max_iterations" in result.error or "atingido" in result.error

    # 3 iterações executadas
    assert len(result.history) == 3
    assert engine.execute.call_count == 3

    # Todas as iterações têm Action
    for record in result.history:
        assert record.action is not None


# ---------------------------------------------------------------------------
# Propagação de erros do AgentEngine
# ---------------------------------------------------------------------------


def test_run_engine_error_fatal_stops_loop() -> None:
    """
    Erro fatal do AgentEngine interrompe o loop.
    """
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_engine_result(
        success=False,
        error="LLMExecutor: falha no Provider: Rate limit",
    )

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Execute",
    )

    assert result.success is False
    assert result.iterations == 1
    assert result.error is not None
    assert "Rate limit" in result.error

    assert len(result.history) == 1
    assert result.history[0].error is not None
    assert "Rate limit" in result.history[0].error

    engine.execute.assert_called_once()


def test_run_engine_error_after_successful_iteration() -> None:
    """
    Após uma iteração bem-sucedida, erro fatal na segunda interrompe o loop.
    O histórico deve conter ambas as iterações.
    """
    engine = _make_agent_engine_mock()
    engine.execute.side_effect = [
        _make_successful_tool_action(
            tool="filesystem.read_file",
            arguments={"path": "a.txt"},
            result_content={"content": "data"},
        ),
        _make_engine_result(
            success=False,
            llm_response=None,
            error="AgentEngine: falha no ContextBuilder: disk full",
        ),
    ]

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Execute",
    )

    assert result.success is False
    assert result.iterations == 2
    assert result.error is not None
    assert "disk full" in result.error

    assert len(result.history) == 2
    assert result.history[0].action is not None  # primeira iteração: sucesso
    assert result.history[0].error is None
    assert result.history[1].error is not None  # segunda iteração: erro
    assert "disk full" in result.history[1].error

    assert engine.execute.call_count == 2


# ---------------------------------------------------------------------------
# Registro correto do histórico
# ---------------------------------------------------------------------------


def test_run_history_records_all_iterations() -> None:
    """
    Cada iteração é registrada corretamente no histórico com todos os campos.
    """
    engine = _make_agent_engine_mock()
    engine.execute.side_effect = [
        _make_successful_tool_action(
            tool="filesystem.read_file",
            arguments={"path": "a.txt"},
            result_content={"content": "aaa"},
        ),
        _make_successful_tool_action(
            tool="filesystem.search",
            arguments={"pattern": "*.md"},
            result_content={"files": ["readme.md"]},
        ),
        _make_textual_response("Concluído."),
    ]

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Execute tudo",
    )

    assert result.iterations == 3
    assert len(result.history) == 3

    # Iteração 1
    r1 = result.history[0]
    assert r1.iteration == 1
    assert r1.llm_response is not None
    assert r1.action is not None
    assert r1.action["tool"] == "filesystem.read_file"
    assert r1.execution_result is not None
    assert r1.execution_result["success"] is True
    assert r1.error is None

    # Iteração 2
    r2 = result.history[1]
    assert r2.iteration == 2
    assert r2.action is not None
    assert r2.action["tool"] == "filesystem.search"
    assert r2.execution_result is not None
    assert r2.execution_result["success"] is True
    assert r2.error is None

    # Iteração 3
    r3 = result.history[2]
    assert r3.iteration == 3
    assert r3.action is None
    assert r3.execution_result is None
    assert r3.error is None


# ---------------------------------------------------------------------------
# Atualização da instrução entre iterações
# ---------------------------------------------------------------------------


def test_run_updates_instruction_with_successful_result() -> None:
    """
    A instrução do usuário é atualizada entre iterações com o resultado
    da Action executada com sucesso.
    """
    engine = _make_agent_engine_mock()
    engine.execute.side_effect = [
        _make_successful_tool_action(
            tool="filesystem.read_file",
            arguments={"path": "data.txt"},
            result_content={"content": "conteúdo importante"},
        ),
        _make_textual_response("Arquivo lido. Conteúdo: conteúdo importante"),
    ]

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Leia o arquivo data.txt",
    )

    assert result.success is True
    assert result.iterations == 2

    # Verificar que a segunda chamada recebeu instrução atualizada
    second_call_args = engine.execute.call_args_list[1][1]
    updated_instruction = second_call_args["user_instruction"]

    assert "data.txt" in updated_instruction
    assert "Iteração 1" in updated_instruction
    assert "Action executada com sucesso" in updated_instruction
    assert "filesystem.read_file" in updated_instruction


def test_run_updates_instruction_with_failed_result() -> None:
    """
    A instrução do usuário é atualizada com erro quando a Action falha.
    """
    engine = _make_agent_engine_mock()
    engine.execute.side_effect = [
        _make_failed_tool_action(
            tool="filesystem.read_file",
            arguments={"path": "inexistente.txt"},
            error_msg="Arquivo não encontrado",
        ),
        _make_successful_tool_action(
            tool="filesystem.list_dir",
            arguments={"path": "."},
            result_content={"files": ["data.txt", "main.py"]},
        ),
        _make_textual_response("Arquivo não encontrado. Listando diretório."),
    ]

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Leia o arquivo",
    )

    assert result.success is True
    assert result.iterations == 3

    # Segunda chamada deve conter informação sobre o erro
    second_call_args = engine.execute.call_args_list[1][1]
    updated_instruction = second_call_args["user_instruction"]

    assert "Iteração 1" in updated_instruction
    assert "Action falhou" in updated_instruction
    assert "Arquivo não encontrado" in updated_instruction

    # Terceira chamada deve conter informação sobre sucesso da segunda
    third_call_args = engine.execute.call_args_list[2][1]
    third_instruction = third_call_args["user_instruction"]

    assert "Iteração 2" in third_instruction
    assert "Action executada com sucesso" in third_instruction


# ---------------------------------------------------------------------------
# LoopResult contract
# ---------------------------------------------------------------------------


def test_loop_result_dataclass_contract() -> None:
    """
    LoopResult possui todos os campos do contrato padronizado.
    """
    result = LoopResult(
        success=True,
        iterations=3,
        final_response="resposta",
        last_action={"type": "tool"},
        history=(
            IterationRecord(
                iteration=1,
                llm_response="resp",
            ),
        ),
        error=None,
    )

    assert result.success is True
    assert result.iterations == 3
    assert result.final_response == "resposta"
    assert result.last_action == {"type": "tool"}
    assert len(result.history) == 1
    assert result.error is None

    # Caso de erro
    error_result = LoopResult(
        success=False,
        iterations=0,
        error="erro fatal",
    )
    assert error_result.success is False
    assert error_result.error == "erro fatal"


def test_loop_result_immutability() -> None:
    """
    LoopResult é imutável (dataclass frozen).
    """
    result = LoopResult(success=True)

    with pytest.raises(AttributeError):
        result.success = False  # type: ignore[misc]

    with pytest.raises(AttributeError):
        result.iterations = 5  # type: ignore[misc]

    with pytest.raises(AttributeError):
        result.error = "novo erro"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# IterationRecord contract
# ---------------------------------------------------------------------------


def test_iteration_record_contract() -> None:
    """
    IterationRecord possui todos os campos.
    """
    record = IterationRecord(
        iteration=1,
        llm_response="resposta LLM",
        action={"type": "tool"},
        execution_result={"success": True},
        error=None,
    )

    assert record.iteration == 1
    assert record.llm_response == "resposta LLM"
    assert record.action == {"type": "tool"}
    assert record.execution_result == {"success": True}
    assert record.error is None

    # Caso com erro
    error_record = IterationRecord(
        iteration=2,
        error="erro no parser",
    )
    assert error_record.iteration == 2
    assert error_record.llm_response is None
    assert error_record.action is None
    assert error_record.execution_result is None
    assert error_record.error == "erro no parser"


def test_iteration_record_immutability() -> None:
    """
    IterationRecord é imutável (dataclass frozen).
    """
    record = IterationRecord(iteration=1)

    with pytest.raises(AttributeError):
        record.iteration = 2  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Default max_iterations
# ---------------------------------------------------------------------------


def test_run_default_max_iterations_is_10() -> None:
    """
    max_iterations padrão é 10.
    """
    engine = _make_agent_engine_mock()
    # Sempre retorna Action para testar o limite
    engine.execute.return_value = _make_successful_tool_action(
        tool="filesystem.read_file",
        arguments={"path": "x.txt"},
        result_content={"content": "data"},
    )

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Execute",
    )

    assert result.iterations == 10
    assert result.success is False  # estourou limite
    assert engine.execute.call_count == 10


# ---------------------------------------------------------------------------
# Action com execução falha (execution_result success=False)
# ---------------------------------------------------------------------------


def test_run_failed_tool_action_triggers_next_iteration() -> None:
    """
    Action executada mas com falha (ex: arquivo não encontrado).
    O loop continua para a próxima iteração com instrução atualizada.
    """
    engine = _make_agent_engine_mock()
    engine.execute.side_effect = [
        _make_failed_tool_action(
            tool="filesystem.read_file",
            arguments={"path": "inexistente.txt"},
            error_msg="File not found",
        ),
        _make_textual_response("Tentei ler mas não encontrei."),
    ]

    loop = _make_loop(engine)
    result = loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="Leia o arquivo",
    )

    assert result.success is True
    assert result.iterations == 2

    # Histórico: iteração 1 com falha, iteração 2 sem action
    assert result.history[0].execution_result is not None
    assert result.history[0].execution_result["success"] is False
    assert result.history[0].execution_result["error"] == "File not found"

    assert result.history[1].action is None


# ---------------------------------------------------------------------------
# Verifica que AgentEngine é usado exclusivamente
# ---------------------------------------------------------------------------


def test_run_only_uses_agent_engine() -> None:
    """
    AgentLoop não acessa nenhum componente diretamente.
    Toda execução passa exclusivamente pelo AgentEngine.
    """
    engine = _make_agent_engine_mock()
    engine.execute.return_value = _make_textual_response("pronto")

    loop = _make_loop(engine)
    loop.run(
        mission=MagicMock(),
        workspace=MagicMock(),
        user_instruction="teste",
    )

    # Apenas o método execute do AgentEngine foi chamado
    engine.execute.assert_called_once()

    # Nenhum outro método do engine foi chamado
    allowed_methods = {"execute"}
    for call in engine.method_calls:
        assert call[0] in allowed_methods