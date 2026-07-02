from __future__ import annotations

import json
from typing import Any


class Reflector:
    def __init__(self, *, router: Any) -> None:
        self.router = router

    def reflect(self, *, objective: str, context: str, decision: dict[str, Any], tool_results: list[dict[str, Any]], iteration: int, state: Any) -> dict[str, Any]:
        system_prompt = (
            "Você é o agente de reflexão. "
            "Responda apenas com JSON válido contendo reflection, should_continue, error_type, needs_retry."
        )
        payload = (
            f"Objetivo: {objective}\n\n"
            f"Contexto: {context}\n\n"
            f"Decisão: {json.dumps(decision, ensure_ascii=False)}\n\n"
            f"Resultados: {json.dumps(tool_results, ensure_ascii=False)}\n\n"
            f"Estado: {json.dumps(state.to_dict(), ensure_ascii=False)}\n\n"
            f"Iteração: {iteration}"
        )
        raw = self.router.ask(prompt=payload, role="reviewer", system_prompt=system_prompt)
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"reflection": "", "should_continue": False, "error_type": "none", "needs_retry": False}
        return {
            "reflection": str(parsed.get("reflection") or ""),
            "should_continue": bool(parsed.get("should_continue", False)),
            "error_type": str(parsed.get("error_type") or "none"),
            "needs_retry": bool(parsed.get("needs_retry", False)),
        }
