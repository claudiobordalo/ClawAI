from __future__ import annotations

from typing import Any

from clawai.autonomy.execution_state import ExecutionState


class ContextManager:
    def __init__(self, *, max_recent_actions: int = 5, max_recent_results: int = 5) -> None:
        self.max_recent_actions = max_recent_actions
        self.max_recent_results = max_recent_results

    def build_prompt(self, *, state: ExecutionState, objective: str) -> str:
        recent_actions = state.current_plan[-self.max_recent_actions :]
        recent_results = state.tool_results[-self.max_recent_results :]
        recent_decisions = state.decisions[-3:]
        recent_errors = state.errors[-3:]

        parts = [f"Objetivo: {objective}"]
        if recent_actions:
            parts.append("Plano atual: " + "; ".join(str(action.get("id")) for action in recent_actions if isinstance(action, dict)))
        if recent_results:
            parts.append("Resultados recentes: " + "; ".join(str(item.get("tool")) for item in recent_results if isinstance(item, dict)))
        if recent_decisions:
            parts.append("Decisões recentes: " + " | ".join(recent_decisions))
        if recent_errors:
            parts.append("Erros recentes: " + " | ".join(recent_errors))
        return "\n".join(parts)
