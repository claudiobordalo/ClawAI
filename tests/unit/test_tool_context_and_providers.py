from __future__ import annotations

from typing import Any

from clawai.autonomy.execution_state import ExecutionState
from clawai.autonomy.planner import Planner
from clawai.autonomy.tool_context import ToolContext
from clawai.tools.filesystem_tool import FilesystemTool
from clawai.tools.providers import LocalToolProvider


class DummyRouter:
    def ask(self, *, prompt: str, role: Any, system_prompt: str | None = None) -> str:
        return '{"goal":"x","reasoning":"ok","expected_result":"x","continue":true,"actions":[{"tool":"filesystem","args":{"action":"list_dir","path":"."}}]}'


def test_execution_state_domain_methods() -> None:
    state = ExecutionState(objective="demo")
    state.set_plan([{"id": "a1", "tool": "filesystem", "args": {}}])
    state.add_tool_result({"tool": "filesystem", "result": {"success": True}})
    state.mark_action_completed({"id": "a1", "tool": "filesystem"})
    state.add_hypothesis("the tool is available")
    state.register_error("timeout")

    assert state.current_plan[0]["id"] == "a1"
    assert state.tool_results[-1]["tool"] == "filesystem"
    assert state.completed_actions[-1]["id"] == "a1"
    assert state.hypotheses == ["the tool is available"]
    assert state.errors == ["timeout"]


def test_tool_context_and_local_provider() -> None:
    context = ToolContext(workspace="/tmp/project", execution_state=ExecutionState(objective="demo"))
    provider = LocalToolProvider([FilesystemTool()])

    assert context.workspace == "/tmp/project"
    assert provider.list_tools() == ["filesystem"]
    tool = provider.get_tool("filesystem")
    assert tool is not None
    assert tool.name == "filesystem"


def test_planner_adds_ids_to_actions() -> None:
    planner = Planner(router=DummyRouter())
    state = ExecutionState(objective="demo")

    plan = planner.plan(
        objective="demo",
        context="ctx",
        iteration=1,
        available_tools=[{"name": "filesystem", "description": "fs"}],
        state=state,
    )

    assert plan["actions"][0]["id"].startswith("action_")
    assert plan["actions"][0]["tool"] == "filesystem"
