from __future__ import annotations

from dataclasses import dataclass

from clawai.mission.mission import Mission
from clawai.prompt.prompt_engine import PromptEngine
from clawai.memory.conversation_memory import ConversationMemory, ConversationMessage
from clawai.tools.filesystem_tool import FilesystemTool
from clawai.tools.tool_discovery import ToolDiscovery
from clawai.tools.tool_registry import ToolRegistry


@dataclass
class DummyContextBuilderResult:
    context: str
    selected_files: list[str]


def _make_mission(*, objective: str = "Test objective") -> Mission:
    # Usa um ID que não conflita com conteúdos de mensagens como "m0", "m1", ...
    return Mission(id="mission-001", objective=objective, priority=3)


def _make_workspace():
    class WS:
        is_open = True

        def get_tree(self):
            return {"root": "project"}

    return WS()


def test_prompt_without_memory_remains_compatible() -> None:
    engine = PromptEngine()
    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert "==================== MISSION" in prompt
    assert "=============== CONVERSATION HISTORY" not in prompt


def test_prompt_with_empty_memory_omits_section() -> None:
    mem = ConversationMemory()
    engine = PromptEngine(conversation_memory=mem)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert "=============== CONVERSATION HISTORY" not in prompt


def test_prompt_with_one_message() -> None:
    mem = ConversationMemory()
    mem.add(role="user", content="Olá")

    engine = PromptEngine(conversation_memory=mem)
    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert "=============== CONVERSATION HISTORY" in prompt
    assert "USER:" in prompt
    assert "Olá" in prompt


def test_prompt_with_multiple_messages_and_order() -> None:
    mem = ConversationMemory()
    mem.add(role="user", content="primeira")
    mem.add(role="assistant", content="segunda")
    mem.add(role="user", content="terceira")

    engine = PromptEngine(conversation_memory=mem)
    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Ordem cronológica
    i1 = prompt.index("primeira")
    i2 = prompt.index("segunda")
    i3 = prompt.index("terceira")
    assert i1 < i2 < i3


def test_prompt_respects_memory_messages_limit() -> None:
    mem = ConversationMemory()
    for i in range(5):
        mem.add(role="user", content=f"m{i}")

    engine = PromptEngine(conversation_memory=mem, memory_messages_limit=2)
    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Apenas m3 e m4 aparecem
    assert "m3" in prompt and "m4" in prompt
    assert "m0" not in prompt and "m1" not in prompt and "m2" not in prompt


def test_prompt_with_memory_and_tools_integration() -> None:
    mem = ConversationMemory()
    mem.add(role="user", content="olá")

    registry = ToolRegistry()
    registry.register(FilesystemTool())
    discovery = ToolDiscovery(tool_registry=registry)

    engine = PromptEngine(conversation_memory=mem, tool_discovery=discovery)
    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # As duas seções estão presentes e na ordem correta
    assert "=============== CONVERSATION HISTORY" in prompt
    assert "=============== AVAILABLE TOOLS" in prompt

    hist_idx = prompt.index("=============== CONVERSATION HISTORY")
    user_idx = prompt.index("================== USER REQUEST")
    tools_idx = prompt.index("=============== AVAILABLE TOOLS")

    assert hist_idx < user_idx < tools_idx


def test_prompt_does_not_modify_memory() -> None:
    mem = ConversationMemory()
    mem.add(role="user", content="a")
    size_before = mem.size()

    engine = PromptEngine(conversation_memory=mem)
    _ = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert mem.size() == size_before


def test_prompt_memory_stability_same_inputs() -> None:
    mem = ConversationMemory()
    mem.add(role="user", content="a")
    mem.add(role="assistant", content="b")

    engine = PromptEngine(conversation_memory=mem)

    p1 = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )
    p2 = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    assert p1 == p2
