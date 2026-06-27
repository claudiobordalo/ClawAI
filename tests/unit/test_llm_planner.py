from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

import pytest

from clawai.planning import LLMPlanner, PlanningResult, ExecutionPlan
from clawai.providers.base.provider import BaseProvider
from clawai.providers.base.response import ProviderResponse


class DummyProvider(BaseProvider):
    def __init__(self, content: str) -> None:
        self._content = content

    def generate(self, prompt: str, system_prompt: str | None = None) -> ProviderResponse:  # type: ignore[override]
        return ProviderResponse(content=self._content, model="dummy", provider="dummy")


class RaisingProvider(BaseProvider):
    def generate(self, prompt: str, system_prompt: str | None = None) -> ProviderResponse:  # type: ignore[override]
        raise RuntimeError("Provider failure")


@dataclass
class DummyPromptEngine:
    pass


def test_success_multiple_steps() -> None:
    provider = DummyProvider('{"objective": "Obj", "steps": ["A", "B", "C"]}')
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=provider)

    result = planner.create_plan("Obj")

    assert isinstance(result, PlanningResult)
    assert result.success is True
    assert isinstance(result.plan, ExecutionPlan)
    assert len(result.plan.steps) == 3
    assert result.plan.steps[0].id == "step-1"
    assert result.plan.steps[0].description == "A"
    assert result.plan.steps[0].status == "pending"
    assert result.plan.steps[2].id == "step-3"
    assert result.plan.steps[2].description == "C"


def test_success_single_step() -> None:
    provider = DummyProvider('{"objective": "Obj", "steps": ["Only Step"]}')
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=provider)

    result = planner.create_plan("Obj")

    assert result.success is True
    assert result.plan is not None
    assert len(result.plan.steps) == 1
    assert result.plan.steps[0].id == "step-1"
    assert result.plan.steps[0].description == "Only Step"


def test_invalid_json_returns_error() -> None:
    provider = DummyProvider("isso nao eh json")
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=provider)

    result = planner.create_plan("Obj")

    assert result.success is False
    assert result.plan is None
    assert result.error is not None


def test_invalid_structure_missing_steps() -> None:
    provider = DummyProvider('{"objective": "Obj"}')
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=provider)

    result = planner.create_plan("Obj")

    assert result.success is False
    assert result.plan is None


def test_invalid_structure_steps_element_type() -> None:
    provider = DummyProvider('{"objective": "Obj", "steps": ["A", 123]}')
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=provider)

    result = planner.create_plan("Obj")

    assert result.success is False
    assert result.plan is None


def test_objective_required() -> None:
    provider = DummyProvider('{"objective": "Obj", "steps": ["A"]}')
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=provider)

    result = planner.create_plan("")

    assert result.success is False
    assert result.plan is None
    assert result.error is not None


def test_error_propagation_no_exceptions() -> None:
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=RaisingProvider())

    result = planner.create_plan("Obj")

    assert result.success is False
    assert result.plan is None
    assert result.error is not None
    assert "Provider failure" in result.error


def test_determinism_same_input_same_plan() -> None:
    provider = DummyProvider('{"objective": "Obj", "steps": ["A", "B"]}')
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=provider)

    r1 = planner.create_plan("Obj")
    r2 = planner.create_plan("Obj")

    assert r1.success and r2.success
    assert r1.plan == r2.plan


def test_no_tool_or_agent_dependencies_imported() -> None:
    provider = DummyProvider('{"objective": "Obj", "steps": ["A"]}')
    planner = LLMPlanner(prompt_engine=DummyPromptEngine(), provider=provider)

    _ = planner.create_plan("Obj")

    # Garante que módulos de execução/agent não foram importados como efeito colateral
    # (não depende da ordem global de execução dos testes).
    forbidden = [
        "clawai.agent.agent_loop",
        "clawai.agent.agent_engine",
        "clawai.tools.tool_executor",
    ]

    for mod in forbidden:
        sys.modules.pop(mod, None)

    _ = planner.create_plan("Obj")

    for mod in forbidden:
        assert mod not in sys.modules
