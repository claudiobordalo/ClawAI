import json

from clawai.autonomy.agent_runtime import AgentRuntime


class FakeRouter:
    def __init__(self, responses: dict[str, str]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def ask(self, *, prompt: str, role, system_prompt: str | None = None) -> str:
        role_name = str(role)
        self.calls.append(
            {
                "role": role_name,
                "prompt": prompt,
                "system_prompt": system_prompt,
            }
        )
        return self.responses.get(role_name, self.responses.get("default", ""))

    def model_for(self, role) -> str:
        return "mock-model"


class FakeToolExecutor:
    def execute(self, *, tool_name: str, arguments: dict[str, object]):
        return {
            "success": True,
            "tool": tool_name,
            "result": {"tool": tool_name, "arguments": arguments},
            "error": None,
            "duration_ms": 1.0,
        }


def test_agent_runtime_executes_actions_and_synthesizes():
    router = FakeRouter(
        {
            "planner": json.dumps(
                {
                    "goal": "testar execução",
                    "reasoning": "precisa ler arquivo",
                    "expected_result": "resultado final",
                    "continue": False,
                    "actions": [
                        {
                            "id": "read_1",
                            "tool": "filesystem",
                            "args": {"action": "list_dir", "path": "."},
                        }
                    ],
                }
            ),
            "reviewer": json.dumps(
                {
                    "reflection": "ok",
                    "should_continue": False,
                    "error_type": "none",
                    "needs_retry": False,
                }
            ),
            "default": "resposta final",
        }
    )

    runtime = AgentRuntime(router=router, tool_executor=FakeToolExecutor(), max_iterations=2)
    result = runtime.run("implemente algo")

    assert result["answer"] == "resposta final"
    assert result["iterations"] == 1
    assert result["used_tools"] is True
    assert result["abort_reason"] is None
    assert len(router.calls) == 3
    assert router.calls[0]["role"] == "planner"
    assert router.calls[1]["role"] == "reviewer"
    assert router.calls[2]["role"] == "default"
    assert result["state"]["completed_actions"]


def test_agent_runtime_stops_before_synthesis_when_llm_budget_is_exhausted():
    router = FakeRouter(
        {
            "planner": json.dumps(
                {
                    "goal": "testar limite",
                    "reasoning": "uma iteração",
                    "expected_result": "fim",
                    "continue": False,
                    "actions": [],
                }
            ),
            "reviewer": json.dumps(
                {
                    "reflection": "sem continuidade",
                    "should_continue": False,
                    "error_type": "none",
                    "needs_retry": False,
                }
            ),
            "default": "nao deve ser usado",
        }
    )

    runtime = AgentRuntime(router=router, tool_executor=FakeToolExecutor(), max_iterations=3)
    runtime.llm_metrics.max_calls = 2

    result = runtime.run("corrija o bug")

    assert result["abort_reason"] == "Maximum LLM calls reached."
    assert result["llm_metrics"]["total_calls"] == 2
    assert [call["role"] for call in router.calls] == ["planner", "reviewer"]
    assert result["answer"].startswith("Execução interrompida")