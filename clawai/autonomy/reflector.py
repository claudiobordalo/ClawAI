from __future__ import annotations

import json
import re
from typing import Any, Optional

from clawai.cognition.reflection_engine import ReflectionEngine, ReflectionEntry
from clawai.cognition.failure_analysis import FailureAnalysis

class Reflector:
    def __init__(self, *, router: Any, reflection_engine: Optional[ReflectionEngine] = None) -> None:
        self.router = router
        self.reflection_engine = reflection_engine

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
        
        # Determine error type from tool results
        error_type = "none"
        if tool_results:
            last_error = next((r.get("error") for r in tool_results if r.get("error")), None)
            if last_error:
                error_type = str(FailureAnalysis.classify(last_error))

        # Get repeated errors from engine
        repeated_errors_str = ""
        if self.reflection_engine:
            repeated = self.reflection_engine.repeated_errors(min_count=2)
            if repeated:
                repeated_errors_str = f"\nERROS REPETIDOS DETECTADOS:\n{json.dumps(repeated, ensure_ascii=False)}"

        payload = (
            f"Objetivo: {objective}\n\n"
            f"Contexto: {context}\n\n"
            f"Decisão: {json.dumps(decision, ensure_ascii=False, default=str)}\n\n"
            f"Resultados: {json.dumps(tool_results, ensure_ascii=False, default=str)}\n\n"
            f"Estado resumido: {json.dumps(state, ensure_ascii=False, default=str)}\n\n"
            f"Iteração: {iteration}"
            f"{repeated_errors_str}\n"
        )
        
        try:
            raw = self.router.ask(
                prompt=payload,
                role="reviewer",
                system_prompt=system_prompt,
            )
        except Exception as e:
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
        
        result = {
            "reflection": str(parsed.get("reflection") or ""),
            "should_continue": bool(parsed.get("should_continue", False)),
            "error_type": str(parsed.get("error_type") or error_type),
            "needs_retry": bool(parsed.get("needs_retry", False)),
        }

        # Record the entry in the engine
        if self.reflection_engine:
            try:
                from datetime import datetime, timezone
                from typing import List, Dict, Any
                
                # Try to find what failed from tool results
                failed_msgs = [r.get("error") for r in tool_results if r.get("error")]
                
                entry = ReflectionEntry(
                    goal_id=objective,
                    goal_title=objective,
                    success=result["should_continue"] or result["needs_retry"],
                    # Map reflection text to what_failed if possible
                    what_failed=failed_msgs if failed_msgs else [],
                    risks=[],
                    opportunities=[],
                    decisions=[str(decision.get("reasoning")) if decision.get("reasoning") else ""],
                    duration=0.0, # Could be improved if we track time
                    metadata={"iteration": iteration}
                )
                self.reflection_engine.record(entry)
            except Exception:
                pass

        return result

    def _parse_json(self, raw: str, *, default: dict[str, Any]) -> dict[str, Any]:
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else default
        except Exception:
            return default
