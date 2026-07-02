from __future__ import annotations

from clawai.autonomy.agent_runtime import AgentRuntime


class StubRouter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def ask(self, *, prompt: str, role, system_prompt: str | None = None) -> str:
        self.calls.append((getattr(role, "value", str(role)), system_prompt))
        if str(role) == "planner":
            return '{"plan": ["Inspecione o projeto"], "reason": "Precisamos entender o contexto", "should_continue": true, "next_action": {"tool": "filesystem", "arguments": {"action": "list_dir", "path": "."}}}'
        if str(role) == "reviewer":
            return '{"reflection": "Consegui entender o contexto", "should_continue": false}'
        return "Resposta final com base no histórico."


class StubToolExecutor:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def execute(self, *, tool_name: str, arguments: dict) -> dict:
        self.calls.append({"tool": tool_name, "arguments": arguments})
        return {"success": True, "tool": tool_name, "result": "ok", "error": None, "duration_ms": 1.0}


def test_agent_runtime_builds_structured_history() -> None:
    router = StubRouter()
    executor = StubToolExecutor()
    runtime = AgentRuntime(router=router, tool_executor=executor, max_iterations=2)

    result = runtime.run("Analise este projeto")

    assert result["used_tools"] is True
    assert result["iterations"] >= 1
    assert result["history"][0]["plan"]
    assert result["history"][0]["tools_used"]
    assert result["history"][0]["tool_results"]
    assert "answer" in result
