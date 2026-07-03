from __future__ import annotations

import json
import re
from typing import Any


class Reflector:
    def __init__(self, *, router: Any) -> None:
        self.router = router

    def reflect(
        self,
        *,
        objective: str,
        context: str,
        decision: dict[str, Any],
        tool_results: list[dict[str, Any]],
        iteration: int,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        system_prompt = (
            "Você é o agente de reflexão. "
            "Responda apenas com JSON válido contendo reflection, should_continue, error_type, needs_retry."
        )
        payload = (
            f"Objetivo: {objective}\n\n"
            f"Contexto: {context}\n\n"
            f"Decisão: {json.dumps(decision, ensure_ascii=False, default=str)}\n\n"
            f"Resultados: {json.dumps(tool_results, ensure_ascii=False, default=str)}\n\n"
            f"Estado resumido: {json.dumps(state, ensure_ascii=False, default=str)}\n\n"
            f"Iteração: {iteration}"
        )
        try:
            raw = self.router.ask(
                prompt=payload,
                role="reviewer",
                system_prompt=system_prompt,
            )
        except Exception:
            return {
                "reflection": f"Reflection unavailable ({e}).",
                "should_continue": False,
                "error_type": "provider_error",
                "needs_retry": False,
            }
        parsed = self._parse_json(
            raw,
            default={
                "reflection": "",
                "should_continue": False,
                "error_type": "none",
                "needs_retry": False,
            },
        )
        return {
            "reflection": str(parsed.get("reflection") or ""),
            "should_continue": bool(parsed.get("should_continue", False)),
            "error_type": str(parsed.get("error_type") or "none"),
            "needs_retry": bool(parsed.get("needs_retry", False)),
        }

    def _parse_json(self, raw: str, *, default: dict[str, Any]) -> dict[str, Any]:
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else default
        except Exception:
            return default