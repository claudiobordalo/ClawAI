from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from clawai.mission.mission import Mission
from clawai.prompt.prompt_engine import PromptEngine


@dataclass
class DummyContextBuilderResult:
    context: str
    selected_files: list[str]


def _make_mission() -> Mission:
    return Mission(
        id="m1",
        objective="Do something",
        priority=3,
    )


def test_prompt_engine_mount_complete_prompt_deterministic_order() -> None:
    engine = PromptEngine()

    mission = _make_mission()
    mission.context = {"k": "v"}
    mission.result = {"r": 1}
    mission.history = [{"step": 1}]
    mission.current_step = 2

    ctx = DummyContextBuilderResult(context="CTX", selected_files=["a.txt"])

    workspace = MagicMock()
    workspace.is_open = True
    workspace.get_tree.return_value = MagicMock(name="tree")

    user_instruction = "USER: patch App"

    prompt = engine.build(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction=user_instruction,
    )

    # ordem determinística dos blocos
    assert "==================== MISSION" in prompt
    assert "==================== CONTEXT" in prompt
    assert "================ WORKSPACE STATE" in prompt
    assert "================== USER REQUEST" in prompt

    assert prompt.index("==================== MISSION") < prompt.index("==================== CONTEXT")
    assert prompt.index("==================== CONTEXT") < prompt.index("================ WORKSPACE STATE")
    assert prompt.index("================ WORKSPACE STATE") < prompt.index("================== USER REQUEST")

    # includes
    assert "CTX" in prompt
    assert "USER: patch App" in prompt
    workspace.get_tree.assert_called_once()


def test_prompt_engine_missing_required_fields_raises() -> None:
    engine = PromptEngine()
    mission = _make_mission()
    ctx = DummyContextBuilderResult(context="CTX", selected_files=[])

    with pytest.raises(ValueError):
        engine.build(mission=None, context_builder_result=ctx, workspace=MagicMock(), user_instruction="u")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        engine.build(mission=mission, context_builder_result=None, workspace=MagicMock(), user_instruction="u")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        engine.build(mission=mission, context_builder_result=ctx, workspace=None, user_instruction="u")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        engine.build(mission=mission, context_builder_result=ctx, workspace=MagicMock(), user_instruction=None)  # type: ignore[arg-type]


def test_prompt_engine_handles_empty_inputs() -> None:
    engine = PromptEngine()

    mission = _make_mission()
    mission.context = {}
    mission.result = {}
    mission.history = []
    mission.current_step = 0

    ctx = DummyContextBuilderResult(context="", selected_files=[])

    workspace = MagicMock()
    workspace.is_open = False
    workspace.get_tree.return_value = {"root": "x"}  # deterministic repr

    prompt = engine.build(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction="",
    )

    assert "==================== MISSION" in prompt
    assert "==================== CONTEXT" in prompt
    assert "================ WORKSPACE STATE" in prompt
    assert "================== USER REQUEST" in prompt

    # saída sempre contém blocos
    assert "\n" in prompt
    workspace.get_tree.assert_called_once()


def test_prompt_engine_output_stability_for_same_inputs() -> None:
    engine = PromptEngine()

    mission = _make_mission()
    mission.context = {"k": "v"}
    mission.result = {"r": 1}
    mission.history = [{"step": 1}]
    mission.current_step = 2

    ctx = DummyContextBuilderResult(context="CTX", selected_files=["a.txt"])

    workspace = MagicMock()
    workspace.is_open = True
    workspace.get_tree.return_value = {"children": []}

    user_instruction = "USER"

    prompt1 = engine.build(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction=user_instruction,
    )
    prompt2 = engine.build(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction=user_instruction,
    )

    assert prompt1 == prompt2


def test_prompt_engine_workspace_block_contains_json_with_is_open_and_tree_repr() -> None:
    engine = PromptEngine()

    mission = _make_mission()
    ctx = DummyContextBuilderResult(context="CTX", selected_files=[])

    workspace = MagicMock()
    workspace.is_open = True
    workspace.get_tree.return_value = {"root": "r"}

    prompt = engine.build(
        mission=mission,
        context_builder_result=ctx,
        workspace=workspace,
        user_instruction="U",
    )

    # extrai o JSON do workspace block (o engine injeta um JSON formatado com indent)
    marker = "================ WORKSPACE STATE ================"
    workspace_part = prompt.split(marker, 1)[1].strip()

    start = workspace_part.find("{")
    end = workspace_part.rfind("}")
    assert start != -1 and end != -1 and end > start

    workspace_json_text = workspace_part[start : end + 1]
    data: dict[str, Any] = json.loads(workspace_json_text)

    assert set(data.keys()) == {"is_open", "tree"}
    assert data["is_open"] is True
    assert isinstance(data["tree"], str) or data["tree"] is None
