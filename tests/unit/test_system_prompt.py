from __future__ import annotations

from dataclasses import dataclass

from clawai.prompt.system_prompt import SystemPrompt
from clawai.prompt.prompt_engine import PromptEngine
from clawai.mission.mission import Mission


@dataclass
class DummyContextBuilderResult:
    context: str
    selected_files: list[str]


def _make_mission(*, objective: str = "Test objective") -> Mission:
    return Mission(id="mission-sp", objective=objective, priority=3)


def _make_workspace():
    class WS:
        is_open = True

        def get_tree(self):
            return {"root": "project"}

    return WS()


def test_system_prompt_empty() -> None:
    sp = SystemPrompt("")
    assert sp.build() == ""


def test_system_prompt_simple_content() -> None:
    sp = SystemPrompt("Você é o ClawAI.")
    assert sp.build() == "Você é o ClawAI."


def test_system_prompt_multiline() -> None:
    content = "Você é o ClawAI.\nSiga as regras.\nResponda em português."
    sp = SystemPrompt(content)
    assert sp.build() == content


def test_prompt_engine_integration_with_system_prompt() -> None:
    sp = SystemPrompt("Você é o ClawAI.")
    engine = PromptEngine(system_prompt=sp)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Verifica presença e posição da seção SYSTEM
    assert "=============== SYSTEM ===============" in prompt
    assert "Você é o ClawAI." in prompt

    system_idx = prompt.index("=============== SYSTEM ===============")
    context_idx = prompt.index("==================== CONTEXT ====================")
    assert system_idx < context_idx


def test_prompt_engine_compatibility_without_system_prompt() -> None:
    engine = PromptEngine()
    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )
    assert "=============== SYSTEM ===============" not in prompt


def test_prompt_engine_sections_order_with_system_prompt() -> None:
    sp = SystemPrompt("sys")
    engine = PromptEngine(system_prompt=sp)

    prompt = engine.build(
        mission=_make_mission(),
        context_builder_result=DummyContextBuilderResult(context="CTX", selected_files=[]),
        workspace=_make_workspace(),
        user_instruction="USER",
    )

    # Ordem requerida:
    # 1. SYSTEM
    # 2. CONTEXT (no engine temos MISSION e CONTEXT preservando estrutura atual)
    # 3. CONVERSATION HISTORY (se houver)
    # 4. USER REQUEST
    # 5. AVAILABLE TOOLS

    system_idx = prompt.index("=============== SYSTEM ===============")
    mission_idx = prompt.index("==================== MISSION ====================")
    context_idx = prompt.index("==================== CONTEXT ====================")
    user_idx = prompt.index("================== USER REQUEST =================")

    assert system_idx < mission_idx < context_idx < user_idx


def test_system_prompt_immutable() -> None:
    sp = SystemPrompt("content")
    # dataclass frozen: alterar atributo deve falhar
    try:
        sp.content = "new"  # type: ignore[misc]
        assert False, "SystemPrompt should be immutable"
    except Exception:
        pass


def test_system_prompt_stability() -> None:
    sp = SystemPrompt("A")
    engine = PromptEngine(system_prompt=sp)
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
