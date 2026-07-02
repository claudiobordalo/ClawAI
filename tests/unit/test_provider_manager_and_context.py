from __future__ import annotations

from clawai.autonomy.context_manager import ContextManager
from clawai.autonomy.execution_state import ExecutionState
from clawai.autonomy.llm_metrics import LLMCallMetrics
from clawai.tools.providers import LocalToolProvider


class DummyTool:
    name = "filesystem"
    description = "filesystem"

    def execute(self, **kwargs):
        return {"success": True, "result": kwargs, "error": None, "duration_ms": 1.0}

    def health(self):
        return {"success": True, "result": None, "error": None, "duration_ms": 1.0}

    def describe(self):
        return None


def test_context_manager_summarizes_state() -> None:
    state = ExecutionState(objective="inspect workspace")
    state.current_plan = [{"id": "a1", "tool": "filesystem", "args": {"action": "list_dir"}}]
    state.tool_results = [{"tool": "filesystem", "result": {"ok": True}}]
    state.decisions = ["start"]
    state.errors = []

    manager = ContextManager()
    prompt = manager.build_prompt(state=state, objective="inspect workspace")

    assert "inspect workspace" in prompt
    assert "a1" in prompt
    assert "filesystem" in prompt


def test_llm_metrics_enforce_limit() -> None:
    metrics = LLMCallMetrics(max_calls=2)
    metrics.record("planner")
    metrics.record("planner")
    assert metrics.should_abort is False

    metrics.record("reflection")
    assert metrics.should_abort is True


def test_local_provider_supports_lazy_loading() -> None:
    provider = LocalToolProvider([DummyTool()])
    assert provider.list_tools() == ["filesystem"]
    assert provider.get_tool("filesystem").name == "filesystem"
