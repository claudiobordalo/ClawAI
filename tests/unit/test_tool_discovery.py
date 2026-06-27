from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from clawai.tools.filesystem_tool import FilesystemTool
from clawai.tools.tool import Tool
from clawai.tools.tool_descriptor import ArgumentDescriptor
from clawai.tools.tool_descriptor import ToolDescriptor
from clawai.tools.tool_discovery import ToolDiscovery
from clawai.tools.tool_registry import ToolRegistry


# ---------------------------------------------------------------------------
# Helpers: ferramentas mockadas para testes
# ---------------------------------------------------------------------------


class MockToolWithDescribe:
    """Ferramenta mockada que implementa describe() corretamente."""

    def __init__(self, name: str, description: str = "") -> None:
        self._name = name
        self._description = description

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
            arguments=(
                ArgumentDescriptor(
                    name="input",
                    type="string",
                    description="Argumento de entrada",
                    required=True,
                ),
            ),
            examples=('{"input":"test"}',),
            version="1.0.0",
        )


class MockToolWithoutDescribe:
    """Ferramenta mockada SEM describe(), usando fallback."""

    def __init__(self, name: str, description: str = "") -> None:
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description


class MockToolDescriptorInvalid:
    """Ferramenta cujo describe() retorna algo que não é ToolDescriptor."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "description"

    def describe(self) -> str:  # type: ignore[override]
        return "invalid - not a ToolDescriptor"


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_tool_discovery_initialization() -> None:
    """Injeção de dependência bem-sucedida."""
    registry = ToolRegistry()
    discovery = ToolDiscovery(tool_registry=registry)

    assert discovery.tool_registry is registry


def test_tool_discovery_initialization_none_raises() -> None:
    """ToolRegistry None dispara ValueError."""
    with pytest.raises(ValueError, match="tool_registry"):
        ToolDiscovery(tool_registry=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Descoberta de uma ferramenta
# ---------------------------------------------------------------------------


def test_discover_one_tool() -> None:
    """
    Descoberta de uma única ferramenta registrada.
    """
    registry = ToolRegistry()
    tool = MockToolWithDescribe(name="filesystem", description="Operações de arquivo")
    registry.register(tool)

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()

    assert len(descriptors) == 1
    desc = descriptors[0]
    assert desc.name == "filesystem"
    assert desc.description == "Operações de arquivo"
    assert len(desc.arguments) == 1
    assert desc.arguments[0].name == "input"
    assert desc.examples == ('{"input":"test"}',)
    assert desc.version == "1.0.0"


def test_discover_one_tool_by_name() -> None:
    """
    Descoberta de uma única ferramenta pelo nome.
    """
    registry = ToolRegistry()
    tool = MockToolWithDescribe(name="search", description="Busca arquivos")
    registry.register(tool)

    discovery = ToolDiscovery(tool_registry=registry)
    desc = discovery.discover("search")

    assert desc is not None
    assert desc.name == "search"
    assert desc.description == "Busca arquivos"
    assert len(desc.arguments) == 1


def test_discover_nonexistent_tool_returns_none() -> None:
    """
    Descoberta de ferramenta inexistente retorna None.
    """
    registry = ToolRegistry()
    discovery = ToolDiscovery(tool_registry=registry)

    desc = discovery.discover("inexistente")
    assert desc is None


# ---------------------------------------------------------------------------
# Descoberta de múltiplas ferramentas
# ---------------------------------------------------------------------------


def test_discover_multiple_tools() -> None:
    """
    Descoberta de múltiplas ferramentas registradas.
    """
    registry = ToolRegistry()
    registry.register(MockToolWithDescribe(name="filesystem"))
    registry.register(MockToolWithDescribe(name="search"))
    registry.register(MockToolWithDescribe(name="git"))

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()

    assert len(descriptors) == 3
    names = [d.name for d in descriptors]
    assert "filesystem" in names
    assert "search" in names
    assert "git" in names


# ---------------------------------------------------------------------------
# Ordenação determinística
# ---------------------------------------------------------------------------


def test_discover_returns_sorted_by_name() -> None:
    """
    ToolDiscovery retorna ferramentas ordenadas deterministicamente por nome.
    """
    registry = ToolRegistry()
    # Registra em ordem alfabética reversa
    registry.register(MockToolWithDescribe(name="zebra"))
    registry.register(MockToolWithDescribe(name="alpha"))
    registry.register(MockToolWithDescribe(name="beta"))

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()

    assert len(descriptors) == 3
    names = [d.name for d in descriptors]
    assert names == ["alpha", "beta", "zebra"]


def test_discover_returns_sorted_consistently() -> None:
    """
    Múltiplas chamadas retornam a mesma ordem.
    """
    registry = ToolRegistry()
    registry.register(MockToolWithDescribe(name="gamma"))
    registry.register(MockToolWithDescribe(name="alpha"))
    registry.register(MockToolWithDescribe(name="beta"))

    discovery = ToolDiscovery(tool_registry=registry)

    result1 = discovery.discover_all()
    result2 = discovery.discover_all()

    names1 = [d.name for d in result1]
    names2 = [d.name for d in result2]
    assert names1 == names2
    assert names1 == ["alpha", "beta", "gamma"]


# ---------------------------------------------------------------------------
# Ferramenta sem describe() (fallback)
# ---------------------------------------------------------------------------


def test_discover_tool_without_describe() -> None:
    """
    Ferramenta sem describe(): fallback para name e description.
    """
    registry = ToolRegistry()
    tool = MockToolWithoutDescribe(name="simple", description="Ferramenta simples")
    registry.register(tool)

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()

    assert len(descriptors) == 1
    desc = descriptors[0]
    assert desc.name == "simple"
    assert desc.description == "Ferramenta simples"
    assert desc.arguments == ()
    assert desc.examples == ()
    assert desc.version == ""


# ---------------------------------------------------------------------------
# Ferramenta com describe() inválido
# ---------------------------------------------------------------------------


def test_discover_tool_with_invalid_describe_uses_fallback() -> None:
    """
    Ferramenta cujo describe() não retorna ToolDescriptor: usa fallback.
    """
    registry = ToolRegistry()
    tool = MockToolDescriptorInvalid(name="weird")
    registry.register(tool)

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()

    assert len(descriptors) == 1
    desc = descriptors[0]
    assert desc.name == "weird"
    assert desc.description == "description"
    assert desc.arguments == ()
    assert desc.examples == ()


# ---------------------------------------------------------------------------
# ToolRegistry vazio
# ---------------------------------------------------------------------------


def test_discover_empty_registry_returns_empty() -> None:
    """
    ToolRegistry vazio retorna tupla vazia.
    """
    registry = ToolRegistry()
    discovery = ToolDiscovery(tool_registry=registry)

    descriptors = discovery.discover_all()
    assert descriptors == ()


def test_discover_all_safe_when_list_fails() -> None:
    """
    Se ToolRegistry.list_tools() retorna falha, discover_all retorna vazio.
    """
    registry = MagicMock(spec=ToolRegistry)
    registry.list_tools.return_value = {
        "success": False,
        "result": None,
        "error": "error",
        "duration_ms": 0.0,
    }

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()
    assert descriptors == ()


def test_discover_all_safe_when_get_fails() -> None:
    """
    Se ToolRegistry.get() falha para uma ferramenta, ela é ignorada.
    """
    registry = MagicMock(spec=ToolRegistry)
    registry.list_tools.return_value = {
        "success": True,
        "result": ["tool_a", "tool_b"],
        "error": None,
        "duration_ms": 0.0,
    }
    registry.get.side_effect = [
        {"success": True, "result": MockToolWithDescribe(name="tool_a"), "error": None, "duration_ms": 0.0},
        {"success": False, "result": None, "error": "Tool not found: tool_b", "duration_ms": 0.0},
    ]

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()

    assert len(descriptors) == 1
    assert descriptors[0].name == "tool_a"


# ---------------------------------------------------------------------------
# Contrato de ToolDescriptor
# ---------------------------------------------------------------------------


def test_tool_descriptor_immutability() -> None:
    """
    ToolDescriptor é imutável (dataclass frozen).
    """
    desc = ToolDescriptor(name="test", description="desc")

    with pytest.raises(AttributeError):
        desc.name = "novo"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        desc.description = "nova desc"  # type: ignore[misc]


def test_tool_descriptor_default_values() -> None:
    """
    ToolDescriptor com valores padrão.
    """
    desc = ToolDescriptor(name="minimal", description="descrição")

    assert desc.arguments == ()
    assert desc.examples == ()
    assert desc.version == ""


def test_argument_descriptor_immutability() -> None:
    """
    ArgumentDescriptor é imutável (dataclass frozen).
    """
    arg = ArgumentDescriptor(name="path", type="string")

    with pytest.raises(AttributeError):
        arg.name = "novo"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        arg.type = "integer"  # type: ignore[misc]


def test_argument_descriptor_default_values() -> None:
    """
    ArgumentDescriptor com valores padrão.
    """
    arg = ArgumentDescriptor(name="path", type="string")

    assert arg.description == ""
    assert arg.required is True
    assert arg.default is None


# ---------------------------------------------------------------------------
# Uso real com FilesystemTool
# ---------------------------------------------------------------------------


def test_discover_filesystem_tool() -> None:
    """
    FilesystemTool real implementa describe() corretamente.
    """
    registry = ToolRegistry()
    tool = FilesystemTool()
    registry.register(tool)

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()

    assert len(descriptors) == 1
    desc = descriptors[0]
    assert desc.name == "filesystem"
    assert desc.description == "Filesystem operations with runtime result contract."
    assert len(desc.arguments) >= 7  # action, path, content, src, dst, pattern, max_chars, root
    assert len(desc.examples) == 3
    assert desc.version == "1.0.0"

    # Verifica argumento action
    action_arg = desc.arguments[0]
    assert action_arg.name == "action"
    assert action_arg.type == "string"
    assert action_arg.required is True


def test_discover_filesystem_tool_by_name() -> None:
    """
    Descoberta do FilesystemTool pelo nome.
    """
    registry = ToolRegistry()
    tool = FilesystemTool()
    registry.register(tool)

    discovery = ToolDiscovery(tool_registry=registry)
    desc = discovery.discover("filesystem")

    assert desc is not None
    assert desc.name == "filesystem"
    assert desc.version == "1.0.0"


# ---------------------------------------------------------------------------
# Descoberta não executa ferramentas
# ---------------------------------------------------------------------------


def test_discovery_does_not_execute_tools() -> None:
    """
    ToolDiscovery nunca chama execute() ou health() das ferramentas.
    """
    registry = ToolRegistry()
    tool = MagicMock(spec=Tool)
    tool.name = "mock_tool"
    tool.description = "Mock description"
    tool.describe.return_value = ToolDescriptor(
        name="mock_tool",
        description="Mock description",
    )
    registry.register(tool)

    discovery = ToolDiscovery(tool_registry=registry)
    descriptors = discovery.discover_all()

    assert len(descriptors) == 1

    # execute() e health() nunca devem ser chamados
    tool.execute.assert_not_called()
    tool.health.assert_not_called()

    # describe() foi chamado
    tool.describe.assert_called_once()