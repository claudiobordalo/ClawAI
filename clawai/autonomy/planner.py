from __future__ import annotations

import json
from typing import Any


class Planner:
    def __init__(self, *, router: Any) -> None:
        self.router = router

    def plan(self, *, objective: str, context: str, iteration: int, available_tools: list[dict[str, Any]], state: Any) -> dict[str, Any]:
        system_prompt = (
            "Você é o planejador do runtime. "
            "Responda apenas com JSON válido. "
            "Sempre retorne um plano estruturado com goal, reasoning, expected_result, continue, actions."
        )
        payload = (
            f"Objetivo: {objective}\n\n"
            f"Contexto da iteração {iteration}:\n{context}\n\n"
            f"Estado estruturado: {json.dumps(state.to_dict(), ensure_ascii=False)}\n\n"
            f"Ferramentas disponíveis: {json.dumps(available_tools, ensure_ascii=False)}"
        )
        raw = self.router.ask(prompt=payload, role="planner", system_prompt=system_prompt)
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {
                "goal": objective,
                "reasoning": "Fallback simples",
                "expected_result": objective,
                "continue": False,
                "actions": [],
            }
        actions = parsed.get("actions") if isinstance(parsed.get("actions"), list) else []
        if not actions:
            next_action = parsed.get("next_action")
            if isinstance(next_action, dict):
                actions = [
                    {
                        "tool": next_action.get("tool"),
                        "args": next_action.get("arguments") or next_action.get("args") or {},
                    }
                ]
        normalized_actions: list[dict[str, Any]] = []
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                continue
            normalized_action = dict(action)
            if not normalized_action.get("id"):
                normalized_action["id"] = f"action_{iteration}_{index + 1}"
            normalized_actions.append(normalized_action)

        return {
            "goal": str(parsed.get("goal") or objective),
            "reasoning": str(parsed.get("reasoning") or ""),
            "expected_result": str(parsed.get("expected_result") or objective),
            "continue": bool(parsed.get("continue", False)) or bool(normalized_actions),
            "actions": normalized_actions,
        }
