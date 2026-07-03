from __future__ import annotations

import json
import re
from typing import Any


class Planner:
    def __init__(self, *, router: Any) -> None:
        self.router = router

    def plan(
        self,
        *,
        objective: str,
        context: str,
        iteration: int,
        available_tools: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        system_prompt = (
            "Você é o planejador do runtime. Responda SOMENTE com JSON válido. "
            "Cada item de actions deve ter tool e args. "
            "Nunca utilize name nem arguments. "
            "Para filesystem use sempre action=list_dir quando a intenção for listar arquivos."
        )
        payload = (
            f"Objetivo: {objective}\n\n"
            f"Contexto da iteração {iteration}:\n{context}\n\n"
            f"Estado resumido: {json.dumps(state, ensure_ascii=False, default=str)}\n\n"
            f"Ferramentas disponíveis: {json.dumps(available_tools, ensure_ascii=False, default=str)}"
        )
        raw = self.router.ask(prompt=payload, role="planner", system_prompt=system_prompt)
        parsed = self._parse_json(
            raw,
            default={
                "goal": objective,
                "reasoning": "Fallback simples",
                "expected_result": objective,
                "continue": False,
                "actions": [],
            },
        )

        if isinstance(parsed, list):
            parsed = {
                "goal": objective,
                "reasoning": "",
                "expected_result": objective,
                "continue": True,
                "actions": parsed,
            }
        elif not isinstance(parsed, dict):
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
            normalized_action = self._normalize_action(action, iteration, index)
            if normalized_action is not None:
                normalized_actions.append(normalized_action)

        continue_flag = parsed.get("continue", False)
        if isinstance(continue_flag, str):
            continue_flag = continue_flag.strip().lower() in {"true", "1", "yes", "sim"}

        return {
            "goal": str(parsed.get("goal") or objective),
            "reasoning": str(parsed.get("reasoning") or ""),
            "expected_result": str(parsed.get("expected_result") or objective),
            "continue": bool(continue_flag) or bool(normalized_actions),
            "actions": normalized_actions,
        }

    def _normalize_action(self, action: Any, iteration: int, index: int) -> dict[str, Any] | None:
        if not isinstance(action, dict):
            return None

        normalized_action = dict(action)
        normalized_action.pop("state", None)
        normalized_action.pop("execution_state", None)

        raw_name = normalized_action.pop("name", None)
        tool = normalized_action.get("tool")
        if not tool and raw_name:
            tool, filesystem_action = self._map_legacy_name(str(raw_name))
            if tool:
                normalized_action["tool"] = tool
                args = normalized_action.get("args") or normalized_action.get("arguments") or {}
                if not isinstance(args, dict):
                    args = {}
                if filesystem_action:
                    args["action"] = filesystem_action
                normalized_action["args"] = args

        if "args" not in normalized_action and "arguments" in normalized_action:
            normalized_action["args"] = normalized_action.pop("arguments")
        if not isinstance(normalized_action.get("args"), dict):
            normalized_action["args"] = {}

        if normalized_action.get("tool") == "filesystem":
            args = normalized_action.setdefault("args", {})
            if not isinstance(args, dict):
                args = {}
                normalized_action["args"] = args
            args.setdefault("action", "list_dir")

        if not normalized_action.get("tool"):
            return None

        if not normalized_action.get("id"):
            normalized_action["id"] = f"action_{iteration}_{index + 1}"

        return normalized_action

    def _map_legacy_name(self, name: str) -> tuple[str | None, str | None]:
        mapping = {
            "list_files": ("filesystem", "list_dir"),
            "list_dir": ("filesystem", "list_dir"),
            "read_file": ("filesystem", "read_file"),
            "write_file": ("filesystem", "write_file"),
            "append_file": ("filesystem", "append_file"),
            "delete_file": ("filesystem", "delete_file"),
            "exists": ("filesystem", "exists"),
            "mkdir": ("filesystem", "mkdir"),
            "copy": ("filesystem", "copy"),
            "move": ("filesystem", "move"),
            "search": ("filesystem", "search"),
            "read_text": ("filesystem", "read_text"),
        }
        return mapping.get(name, (None, None))

    def _parse_json(self, raw: str, *, default: Any) -> Any:
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
            return json.loads(text)
        except Exception:
            return default
