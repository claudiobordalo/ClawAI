from __future__ import annotations

import json
from typing import Any

from clawai.autonomy.execution_state import _safe_copy


class Synthesizer:
    def __init__(self, *, router: Any) -> None:
        self.router = router

    def synthesize(self, *, objective: str, history: list[dict[str, Any]]) -> str:
        if not history:
            return "Nenhuma ação foi executada."

        compact_history = self._compact_history(history)
        if not any(item.get("tool_results") for item in compact_history if isinstance(item, dict)):
            last = compact_history[-1]
            reflection = str(last.get("reflection") or "").strip()
            if reflection:
                return reflection
            return "Nenhuma ferramenta foi utilizada."

        system_prompt = (
            "Você é o sintetizador do runtime. "
            "Resuma a resposta final em português com base no histórico compacto e estrutural."
        )
        payload = (
            f"Objetivo: {objective}\n\n"
            f"Histórico: {json.dumps(compact_history, ensure_ascii=False, default=str)}"
        )
        return self.router.ask(prompt=payload, role="default", system_prompt=system_prompt)

    def _compact_history(self, history: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
        compact: list[dict[str, Any]] = []
        for item in history[-limit:]:
            if not isinstance(item, dict):
                compact.append({"value": _safe_copy(item)})
                continue

            compact.append(
                {
                    "iteration": item.get("iteration"),
                    "reflection": _safe_copy(item.get("reflection", "")),
                    "plan": _safe_copy(item.get("plan", [])),
                    "tool_calls": _safe_copy(item.get("tool_calls", [])),
                    "tool_results": _safe_copy(item.get("tool_results", [])),
                }
            )
        return compact
