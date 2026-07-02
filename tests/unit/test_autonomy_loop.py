from __future__ import annotations

from clawai.autonomy.autonomy_loop import AutonomyLoop


class StubRouter:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def ask(self, *, prompt: str, role, system_prompt: str) -> str:
        self.calls.append((role.value if hasattr(role, "value") else str(role), system_prompt))
        if not self._responses:
            return "Resposta padrão"
        return self._responses.pop(0)

    def model_for(self, role):
        return "stub-model"


class StubExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def execute(self, *, tool_name: str, arguments: dict) -> dict:
        self.calls.append((tool_name, arguments))
        return {
            "success": True,
            "tool": tool_name,
            "result": f"resultado para {arguments.get('path', '.')}",
            "error": None,
            "duration_ms": 1.0,
        }


def test_autonomy_loop_uses_tool_and_synthesizes() -> None:
    router = StubRouter([
        "1. Inspecione a estrutura do projeto.\n2. Resuma os achados.",
        "continue",
        "Resumo final com os resultados da inspeção.",
    ])
    executor = StubExecutor()

    loop = AutonomyLoop(router=router, executor=executor)
    result = loop.run("Analise a estrutura do projeto")

    assert result["used_tools"] is True
    assert executor.calls
    assert "estrutura" in result["answer"].lower() or "resultado" in result["answer"].lower()
