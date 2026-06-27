from __future__ import annotations

from dataclasses import dataclass

from clawai.tools.tool_descriptor import ToolDescriptor
from clawai.tools.tool_selection_policy import ToolSelectionPolicy


@dataclass
class DummyMission:
    objective: str = "Test mission"


dataclass
class DummyWorkspace:
    pass


def _make_tool(name: str, description: str = "desc") -> ToolDescriptor:
    return ToolDescriptor(name=name, description=description)


def test_select_with_empty_list_returns_empty_tuple() -> None:
    policy = ToolSelectionPolicy()
    selected = policy.select([], DummyMission(), DummyWorkspace())

    assert selected == ()


def test_select_with_single_tool_returns_same_tool() -> None:
    policy = ToolSelectionPolicy()
    tool = _make_tool("alpha")

    selected = policy.select((tool,), DummyMission(), DummyWorkspace())

    assert selected == (tool,)


def test_select_with_multiple_tools_orders_by_name() -> None:
    policy = ToolSelectionPolicy()
    tools = (
        _make_tool("zebra"),
        _make_tool("alpha"),
        _make_tool("beta"),
    )

    selected = policy.select(tools, DummyMission(), DummyWorkspace())

    assert tuple(tool.name for tool in selected) == ("alpha", "beta", "zebra")


def test_select_removes_duplicates_by_name() -> None:
    policy = ToolSelectionPolicy()
    tools = (
        _make_tool("alpha"),
        _make_tool("beta"),
        _make_tool("alpha", description="duplicate"),
    )

    selected = policy.select(tools, DummyMission(), DummyWorkspace())

    assert len(selected) == 2
    assert tuple(tool.name for tool in selected) == ("alpha", "beta")
    assert selected[0].description == "desc"


def test_select_ignores_invalid_tools() -> None:
    policy = ToolSelectionPolicy()
    tools = (
        _make_tool("alpha"),
        "invalid",
        _make_tool("beta"),
        ToolDescriptor(name="", description="bad"),
    )

    selected = policy.select(tools, DummyMission(), DummyWorkspace())

    assert tuple(tool.name for tool in selected) == ("alpha", "beta")


def test_prompt_engine_uses_tool_selection_policy_if_provided() -> None:
    from unittest.mock import MagicMock

    from clawai.mission.mission import Mission
    from clawai.prompt.prompt_engine import PromptEngine
    from clawai.tools.tool_descriptor import ToolDescriptor
    from clawai.tools.tool_discovery import ToolDiscovery
    from clawai.tools.tool_registry import ToolRegistry

    @dataclass
    class DummyTool:
        name: str

        def describe(self) -> ToolDescriptor:
            return ToolDescriptor(name=self.name, description="desc")

    registry = ToolRegistry()
    registry.register(DummyTool(name="beta"))
    registry.register(DummyTool(name="alpha"))

    discovery = ToolDiscovery(tool_registry=registry)
    policy = ToolSelectionPolicy()
    engine = PromptEngine(tool_discovery=discovery, tool_selection_policy=policy)

    mission = Mission(id="m1", objective="Test", priority=1)
    workspace = MagicMock()
    workspace.is_open = True
    workspace.get_tree.return_value = {"root": "project"}

    prompt = engine.build(
        mission=mission,
        context_builder_result=MagicMock(context="CTX"),
        workspace=workspace,
        user_instruction="USER",
    )

    assert prompt.index("alpha") < prompt.index("beta")
