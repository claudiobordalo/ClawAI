from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from clawai.mission.mission import Mission
from clawai.prompt.prompt_engine import PromptEngine
from clawai.tools.filesystem_tool import FilesystemTool
from clawai.tools.tool import Tool
from clawai.tools.tool_descriptor import ArgumentDescriptor
from clawai.tools.tool_descriptor import ToolDescriptor
from clawai.tools.tool_discovery import ToolDiscovery
from clawai.tools.tool_registry import ToolRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class DummyContextBuilderResult:
    context: str
    selected_files: list[str]


def _make_mission(*, objective: str = "Test objective") -> Mission:
    return Mission(
        id="m1",
        objective=objective,
        priority=3,
    )


def _make_workspace() -> MagicMock:
    workspace = MagicMock()
    workspace.is_open = True
    workspace.get_tree.return_value = {"root": "project"}
    return workspace


# ---------------------------------------------------------------------------
# compatibilidade total sem ToolDiscovery
# ---------------------------------------------------------------------------


def test_prompt_engine_without_tool_discovery() -> None:
    """
    PromptEngine sem ToolDiscovery funciona exatamente como antes.
    Comportamento padrão: construtor sem argumentos.
    """
    engine = PromptEngine()

    assert engine.tool_discovery is None

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Blocos base presentes
    assert "==================== MISSION" in prompt
    assert "==================== CONTEXT" in prompt
    assert "================ WORKSPACE STATE" in prompt
    assert "================== USER REQUEST" in prompt

    # Seção de ferramentas NÃO deve estar presente
    assert "=============== AVAILABLE TOOLS" not in prompt


def test_prompt_engine_with_none_tool_discovery() -> None:
    """
    PromptEngine com ToolDiscovery=None funciona exatamente como antes.
    """
    engine = PromptEngine(tool_discovery=None)

    assert engine.tool_discovery is None

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert "==================== MISSION" in prompt
    assert "=============== AVAILABLE TOOLS" not in prompt


# ---------------------------------------------------------------------------
# Prompt com uma ferramenta
# ---------------------------------------------------------------------------


def test_prompt_engine_with_one_tool() -> None:
    """
    PromptEngine com ToolDiscovery com uma ferramenta registrada.
    """
    registry = ToolRegistry()
    registry.register(FilesystemTool())

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Blocos base
    assert "==================== MISSION" in prompt
    assert "==================== CONTEXT" in prompt
    assert "================ WORKSPACE STATE" in prompt
    assert "================== USER REQUEST" in prompt

    # Seção de ferramentas presente
    assert "=============== AVAILABLE TOOLS" in prompt

    # Nome da ferramenta
    assert "filesystem" in prompt

    # Description
    assert "Filesystem operations with runtime result contract." in prompt

    # Argumentos
    assert "action" in prompt
    assert "path" in prompt
    assert "string" in prompt
    assert "required" in prompt

    # Exemplos
    assert '{"action":"read_file","path":"README.md"}' in prompt


# ---------------------------------------------------------------------------
# Prompt com múltiplas ferramentas
# ---------------------------------------------------------------------------


def test_prompt_engine_with_multiple_tools() -> None:
    """
    PromptEngine com ToolDiscovery com múltiplas ferramentas.
    """
    registry = ToolRegistry()
    registry.register(MockTool(name="alpha", description="Primeira ferramenta"))
    registry.register(MockTool(name="beta", description="Segunda ferramenta"))
    registry.register(MockTool(name="gamma", description="Terceira ferramenta"))

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Todas as ferramentas estão no prompt
    assert "alpha" in prompt
    assert "beta" in prompt
    assert "gamma" in prompt


# ---------------------------------------------------------------------------
# Ordem determinística
# ---------------------------------------------------------------------------


def test_prompt_engine_tools_are_in_deterministic_order() -> None:
    """
    Ferramentas aparecem sempre na mesma ordem (alfabética).
    """
    registry = ToolRegistry()
    registry.register(MockTool(name="zebra", description="Última"))
    registry.register(MockTool(name="alpha", description="Primeira"))
    registry.register(MockTool(name="beta", description="Segunda"))

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt1 = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )
    prompt2 = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert prompt1 == prompt2

    # Ordem: alpha antes de beta antes de zebra
    alpha_idx = prompt1.index("alpha")
    beta_idx = prompt1.index("beta")
    zebra_idx = prompt1.index("zebra")
    assert alpha_idx < beta_idx < zebra_idx


# ---------------------------------------------------------------------------
# ToolDiscovery vazio
# ---------------------------------------------------------------------------


def test_prompt_engine_with_empty_tool_discovery() -> None:
    """
    ToolDiscovery vazio (sem ferramentas) não adiciona seção de ferramentas.
    """
    registry = ToolRegistry()
    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Seção de ferramentas NÃO deve estar presente
    assert "=============== AVAILABLE TOOLS" not in prompt


# ---------------------------------------------------------------------------
# Ferramentas com e sem exemplos
# ---------------------------------------------------------------------------


def test_prompt_engine_tool_with_examples() -> None:
    """
    Ferramenta com exemplos exibe a seção Examples.
    """
    registry = ToolRegistry()
    registry.register(FilesystemTool())

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert "Examples:" in prompt
    assert '{"action":"read_file","path":"README.md"}' in prompt


def test_prompt_engine_tool_without_examples() -> None:
    """
    Ferramenta sem exemplos não exibe seção Examples.
    """
    registry = ToolRegistry()
    registry.register(MockTool(name="simple", description="Ferramenta simples"))

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert "simple" in prompt
    assert "Examples:" not in prompt


# ---------------------------------------------------------------------------
# Ferramentas com múltiplos argumentos
# ---------------------------------------------------------------------------


def test_prompt_engine_tool_with_multiple_arguments() -> None:
    """
    Ferramenta com múltiplos argumentos exibe todos corretamente.
    """
    registry = ToolRegistry()
    registry.register(
        MockTool(
            name="multi",
            description="Ferramenta com múltiplos argumentos",
            arguments=(
                ArgumentDescriptor(
                    name="path", type="string", description="Caminho", required=True
                ),
                ArgumentDescriptor(
                    name="recursive",
                    type="boolean",
                    description="Busca recursiva",
                    required=False,
                ),
                ArgumentDescriptor(
                    name="max_results",
                    type="integer",
                    description="Máximo de resultados",
                    required=False,
                    default=10,
                ),
            ),
            examples=('{"path":".","recursive":true}',),
        )
    )

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Argumentos
    assert "path (string, required)" in prompt
    assert "Caminho" in prompt
    assert "recursive (boolean, optional)" in prompt
    assert "Busca recursiva" in prompt
    assert "max_results (integer, optional, default=10)" in prompt
    assert "Máximo de resultados" in prompt


# ---------------------------------------------------------------------------
# Garantir que nenhuma ferramenta seja executada
# ---------------------------------------------------------------------------


def test_prompt_engine_does_not_execute_tools() -> None:
    """
    PromptEngine nunca chama execute() ou health() das ferramentas
    durante a montagem do prompt.
    """
    tool = MagicMock(spec=Tool)
    tool.name = "magic_tool"
    tool.description = "Magic tool description"
    tool.describe.return_value = ToolDescriptor(
        name="magic_tool",
        description="Magic tool description",
        arguments=(
            ArgumentDescriptor(name="input", type="string", description="Input", required=True),
        ),
        examples=('{"input":"test"}',),
    )

    registry = ToolRegistry()
    registry.register(tool)

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert "magic_tool" in prompt
    assert "Magic tool description" in prompt

    # execute() e health() nunca devem ser chamados
    tool.execute.assert_not_called()
    tool.health.assert_not_called()

    # describe() foi chamado (via ToolDiscovery)
    tool.describe.assert_called()


# ---------------------------------------------------------------------------
# Tool com argumentos required/optional
# ---------------------------------------------------------------------------


def test_prompt_engine_required_and_optional_arguments() -> None:
    """
    Argumentos required e optional são identificados corretamente.
    """
    registry = ToolRegistry()
    registry.register(
        MockTool(
            name="test_tool",
            description="Test tool",
            arguments=(
                ArgumentDescriptor(
                    name="required_arg", type="string", required=True
                ),
                ArgumentDescriptor(
                    name="optional_arg", type="integer", required=False
                ),
            ),
        )
    )

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert "required_arg (string, required)" in prompt
    assert "optional_arg (integer, optional)" in prompt


# ---------------------------------------------------------------------------
# Estrutura do bloco de ferramentas
# ---------------------------------------------------------------------------


def test_prompt_engine_tools_block_separator() -> None:
    """
    A seção de ferramentas é claramente separada do restante do prompt.
    """
    registry = ToolRegistry()
    registry.register(FilesystemTool())

    discovery = ToolDiscovery(tool_registry=registry)
    engine = PromptEngine(tool_discovery=discovery)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(
            context="CTX", selected_files=[]
        ),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # O separador de ferramentas deve estar após o bloco USER REQUEST
    assert "================== USER REQUEST" in prompt
    assert "=============== AVAILABLE TOOLS" in prompt

    user_idx = prompt.index("================== USER REQUEST")
    tools_idx = prompt.index("=============== AVAILABLE TOOLS")
    assert tools_idx > user_idx


# ---------------------------------------------------------------------------
# MockTool helper
# ---------------------------------------------------------------------------


class MockTool:
    """Ferramenta mockada para testes do PromptEngine."""

    def __init__(
        self,
        name: str,
        description: str = "",
        arguments: tuple[ArgumentDescriptor, ...] = (),
        examples: tuple[str, ...] = (),
        version: str = "",
    ) -> None:
        self._name = name
        self._description = description
        self._arguments = arguments
        self._examples = examples
        self._version = version

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def describe(self) -> ToolDescriptor:
        return ToolDescriptor(
            name=self._name,
            description=self._description,
            arguments=self._arguments,
            examples=self._examples,
            version=self._version,
        )