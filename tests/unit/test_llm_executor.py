from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from clawai.llm.llm_executor import LLMExecutor
from clawai.llm.llm_executor import LLMResult
from clawai.providers.base.response import ProviderResponse
from clawai.prompt.prompt_engine import PromptEngine


@dataclass
class DummyContextBuilderResult:
    context: str
    selected_files: list[str]


def _make_dummy_mission() -> MagicMock:
    mission = MagicMock()
    mission.id = "m1"
    mission.objective = "Do something"
    mission.priority = 3
    return mission


def test_llm_executor_initialization() -> None:
    prompt_engine = MagicMock(spec=PromptEngine)
    provider = MagicMock()

    executor = LLMExecutor(prompt_engine=prompt_engine, provider=provider)

    assert executor.prompt_engine is prompt_engine
    assert executor.provider is provider


def test_llm_executor_initialization_prompt_engine_none_raises() -> None:
    provider = MagicMock()

    with pytest.raises(ValueError, match="prompt_engine.*obrigatório"):
        LLMExecutor(prompt_engine=None, provider=provider)  # type: ignore[arg-type]


def test_llm_executor_initialization_provider_none_raises() -> None:
    prompt_engine = MagicMock(spec=PromptEngine)

    with pytest.raises(ValueError, match="provider.*obrigatório"):
        LLMExecutor(prompt_engine=prompt_engine, provider=None)  # type: ignore[arg-type]


def test_execute_success_propagates_provider_response() -> None:
    """
    Execução bem-sucedida: PromptEngine constrói prompt, Provider gera resposta,
    resultado é propagado corretamente.
    """
    prompt_engine = MagicMock(spec=PromptEngine)
    prompt_engine.build.return_value = "PROMPT GERADO"

    provider = MagicMock()
    expected_response = ProviderResponse(
        content="Resposta do LLM",
        model="gpt-4",
        provider="openai",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    provider.generate.return_value = expected_response

    executor = LLMExecutor(prompt_engine=prompt_engine, provider=provider)

    mission = _make_dummy_mission()
    ctx = DummyContextBuilderResult(context="CTX", selected_files=["a.py"])
    workspace = MagicMock()

    result = executor.execute(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction="USER: faça algo",
    )

    assert result.success is True
    assert result.response is expected_response
    assert result.error is None

    # PromptEngine chamado com os parâmetros corretos
    prompt_engine.build.assert_called_once_with(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction="USER: faça algo",
    )

    # Provider chamado com o prompt retornado pelo PromptEngine
    provider.generate.assert_called_once_with(prompt="PROMPT GERADO")


def test_execute_prompt_engine_failure_returns_error() -> None:
    """
    Falha do PromptEngine: exceção é capturada e retornada como erro padronizado.
    """
    prompt_engine = MagicMock(spec=PromptEngine)
    prompt_engine.build.side_effect = RuntimeError("Erro no PromptEngine")

    provider = MagicMock()

    executor = LLMExecutor(prompt_engine=prompt_engine, provider=provider)

    result = executor.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="USER: faça algo",
    )

    assert result.success is False
    assert result.response is None
    assert result.error is not None
    assert "falha no PromptEngine" in result.error
    assert "Erro no PromptEngine" in result.error

    # Provider não deve ser chamado se PromptEngine falhou
    provider.generate.assert_not_called()


def test_execute_provider_failure_returns_error() -> None:
    """
    Falha do Provider: exceção é capturada e retornada como erro padronizado.
    """
    prompt_engine = MagicMock(spec=PromptEngine)
    prompt_engine.build.return_value = "PROMPT"

    provider = MagicMock()
    provider.generate.side_effect = ConnectionError("Falha de conexão com API")

    executor = LLMExecutor(prompt_engine=prompt_engine, provider=provider)

    result = executor.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="USER: faça algo",
    )

    assert result.success is False
    assert result.response is None
    assert result.error is not None
    assert "falha no Provider" in result.error
    assert "Falha de conexão com API" in result.error

    # PromptEngine foi chamado, Provider foi chamado mas falhou
    prompt_engine.build.assert_called_once()
    provider.generate.assert_called_once_with(prompt="PROMPT")


def test_execute_mission_none_returns_error() -> None:
    """
    Validação das entradas obrigatórias: mission None retorna erro.
    """
    executor = LLMExecutor(
        prompt_engine=MagicMock(spec=PromptEngine),
        provider=MagicMock(),
    )

    result = executor.execute(
        mission=None,  # type: ignore[arg-type]
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="USER: faça algo",
    )

    assert result.success is False
    assert result.response is None
    assert result.error is not None
    assert "mission" in result.error
    assert "obrigatório" in result.error


def test_execute_context_builder_result_none_returns_error() -> None:
    """
    Validação das entradas obrigatórias: context_builder_result None retorna erro.
    """
    executor = LLMExecutor(
        prompt_engine=MagicMock(spec=PromptEngine),
        provider=MagicMock(),
    )

    result = executor.execute(
        mission=_make_dummy_mission(),
        context_builder_result=None,  # type: ignore[arg-type]
        workspace=MagicMock(),
        user_instruction="USER: faça algo",
    )

    assert result.success is False
    assert result.response is None
    assert result.error is not None
    assert "context_builder_result" in result.error
    assert "obrigatório" in result.error


def test_execute_workspace_none_returns_error() -> None:
    """
    Validação das entradas obrigatórias: workspace None retorna erro.
    """
    executor = LLMExecutor(
        prompt_engine=MagicMock(spec=PromptEngine),
        provider=MagicMock(),
    )

    result = executor.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=None,  # type: ignore[arg-type]
        user_instruction="USER: faça algo",
    )

    assert result.success is False
    assert result.response is None
    assert result.error is not None
    assert "workspace" in result.error
    assert "obrigatório" in result.error


def test_execute_user_instruction_empty_returns_error() -> None:
    """
    Validação das entradas obrigatórias: user_instruction vazia retorna erro.
    """
    executor = LLMExecutor(
        prompt_engine=MagicMock(spec=PromptEngine),
        provider=MagicMock(),
    )

    result = executor.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="",
    )

    assert result.success is False
    assert result.response is None
    assert result.error is not None
    assert "user_instruction" in result.error
    assert "obrigatório" in result.error


def test_execute_user_instruction_none_returns_error() -> None:
    """
    Validação das entradas obrigatórias: user_instruction None retorna erro.
    """
    executor = LLMExecutor(
        prompt_engine=MagicMock(spec=PromptEngine),
        provider=MagicMock(),
    )

    result = executor.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction=None,  # type: ignore[arg-type]
    )

    assert result.success is False
    assert result.response is None
    assert result.error is not None
    assert "user_instruction" in result.error
    assert "obrigatório" in result.error


def test_execute_prompt_engine_called_exactly_once() -> None:
    """
    PromptEngine é chamado exatamente uma vez durante a execução bem-sucedida.
    """
    prompt_engine = MagicMock(spec=PromptEngine)
    prompt_engine.build.return_value = "PROMPT"

    provider = MagicMock()
    provider.generate.return_value = ProviderResponse(
        content="ok", model="gpt-4", provider="openai"
    )

    executor = LLMExecutor(prompt_engine=prompt_engine, provider=provider)

    result = executor.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="USER: faça algo",
    )

    assert result.success is True
    prompt_engine.build.assert_called_once()
    provider.generate.assert_called_once()


def test_execute_provider_called_with_correct_prompt() -> None:
    """
    Provider é chamado exatamente com o prompt retornado pelo PromptEngine,
    sem modificações.
    """
    expected_prompt = "PROMPT DETERMINÍSTICO"

    prompt_engine = MagicMock(spec=PromptEngine)
    prompt_engine.build.return_value = expected_prompt

    provider = MagicMock()
    provider.generate.return_value = ProviderResponse(
        content="ok", model="gpt-4", provider="openai"
    )

    executor = LLMExecutor(prompt_engine=prompt_engine, provider=provider)

    executor.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="USER",
    )

    provider.generate.assert_called_once_with(prompt=expected_prompt)


def test_execute_with_real_prompt_engine_and_mock_provider() -> None:
    """
    Integração com PromptEngine real + Provider mockado.
    Garante que o fluxo PromptEngine -> Provider funciona ponta a ponta.
    """
    from clawai.mission.mission import Mission

    prompt_engine = PromptEngine()
    provider = MagicMock()
    expected_response = ProviderResponse(
        content="Resposta final",
        model="claude-3",
        provider="anthropic",
    )
    provider.generate.return_value = expected_response

    executor = LLMExecutor(prompt_engine=prompt_engine, provider=provider)

    mission = Mission(id="m1", objective="Test mission", priority=1)
    ctx = DummyContextBuilderResult(
        context="Código fonte importante",
        selected_files=["main.py"],
    )
    workspace = MagicMock()
    workspace.is_open = True
    workspace.get_tree.return_value = {"root": "project"}

    result = executor.execute(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction="Implemente a feature X",
    )

    assert result.success is True
    assert result.response is expected_response
    assert result.response.content == "Resposta final"
    assert result.response.provider == "anthropic"

    # Verifica que o prompt montado contém os blocos esperados
    actual_prompt = prompt_engine.build(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction="Implemente a feature X",
    )
    provider.generate.assert_called_once_with(prompt=actual_prompt)
    assert "Implemente a feature X" in actual_prompt
    assert "Código fonte importante" in actual_prompt


def test_llm_result_dataclass() -> None:
    """Verifica que LLMResult funciona como dataclass imutável."""
    response = ProviderResponse(content="c", model="m", provider="p")

    success_result = LLMResult(success=True, response=response)
    assert success_result.success is True
    assert success_result.response is response
    assert success_result.error is None

    error_result = LLMResult(success=False, error="algum erro")
    assert error_result.success is False
    assert error_result.response is None
    assert error_result.error == "algum erro"


def test_execute_different_providers_workflow() -> None:
    """
    Verifica que o LLMExecutor funciona com qualquer Provider (OpenAI, Anthropic, etc.)
    sem conhecer a implementação concreta.
    """
    prompt_engine = MagicMock(spec=PromptEngine)
    prompt_engine.build.return_value = "PROMPT"

    # Simula um Provider estilo OpenAI
    openai_provider = MagicMock()
    openai_provider.generate.return_value = ProviderResponse(
        content="Resposta OpenAI", model="gpt-4", provider="openai"
    )

    executor_openai = LLMExecutor(prompt_engine=prompt_engine, provider=openai_provider)
    result_openai = executor_openai.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="USER",
    )
    assert result_openai.success is True
    assert result_openai.response.provider == "openai"

    # Simula um Provider estilo Anthropic
    anthropic_provider = MagicMock()
    anthropic_provider.generate.return_value = ProviderResponse(
        content="Resposta Anthropic", model="claude-3", provider="anthropic"
    )

    executor_anthropic = LLMExecutor(prompt_engine=prompt_engine, provider=anthropic_provider)
    result_anthropic = executor_anthropic.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="USER",
    )
    assert result_anthropic.success is True
    assert result_anthropic.response.provider == "anthropic"

    # Simula um Provider estilo Ollama (local)
    ollama_provider = MagicMock()
    ollama_provider.generate.return_value = ProviderResponse(
        content="Resposta Ollama", model="llama3", provider="ollama"
    )

    executor_ollama = LLMExecutor(prompt_engine=prompt_engine, provider=ollama_provider)
    result_ollama = executor_ollama.execute(
        mission=_make_dummy_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=MagicMock(),
        user_instruction="USER",
    )
    assert result_ollama.success is True
    assert result_ollama.response.provider == "ollama"