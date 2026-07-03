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
        system_prompt = """
        Você é o planejador do runtime.

        Responda SOMENTE com JSON válido.

        Cada item de "actions" DEVE possuir exatamente este formato:

        {
        "tool": "<nome da ferramenta>",
        "args": {
            ...
        }
        }

        Nunca utilize o campo "name".

        Nunca utilize o campo "arguments".

        Para acessar arquivos utilize SEMPRE:

        {
        "tool": "filesystem",
        "args": {
            "action": "list_dir",
            "path": "..."
        }
        }

        A ferramenta "filesystem" aceita apenas estas ações:

        - list_dir
        - read_file
        - write_file
        - append_file
        - delete_file
        - exists
        - mkdir
        - copy
        - move
        - search
        - read_text

        Nunca invente nomes de ferramentas.

        Nunca invente nomes de ações.

        Nunca utilize "list_files".

        Nunca utilize "open_file".

        Nunca utilize "read".

        Sempre utilize exatamente os nomes acima.
        """
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
        print("\nRAW PLANNER RESPONSE")
        print(raw)
        print("\nPARSED")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))

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
            if "tool" not in normalized_action:
                if "name" in normalized_action:

                    mapping = {
                        "list_files": ("filesystem", "list_dir"),
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

                    tool_name, filesystem_action = mapping.get(
                        normalized_action["name"],
                        (None, None),
                    )

                    if tool_name is not None:
                        normalized_action["tool"] = tool_name

                        args = (
                            normalized_action.get("args")
                            or normalized_action.get("arguments")
                            or {}
                        )

                        args["action"] = filesystem_action

                        normalized_action["args"] = args
            # Compatibilidade com modelos que retornam "name" em vez de "tool"
            if "tool" not in normalized_action and "name" in normalized_action:
                name = normalized_action.pop("name")

                mapping = {
                    "list_files": ("filesystem", "list_dir"),
                    "read_file": ("filesystem", "read_file"),
                    "write_file": ("filesystem", "write_file"),
                    "append_file": ("filesystem", "append_file"),
                    "delete_file": ("filesystem", "delete_file"),
                    "mkdir": ("filesystem", "mkdir"),
                    "copy": ("filesystem", "copy"),
                    "move": ("filesystem", "move"),
                    "search": ("filesystem", "search"),
                    "exists": ("filesystem", "exists"),
                }

                tool, filesystem_action = mapping.get(name, (None, None))

                if tool:
                    normalized_action["tool"] = tool

                    args = normalized_action.get("arguments") or normalized_action.get("args") or {}
                    args["action"] = filesystem_action
                    normalized_action["args"] = args
            normalized_action.pop("state", None)
            normalized_action.pop("execution_state", None)
            if not normalized_action.get("id"):
                normalized_action["id"] = f"action_{iteration}_{index + 1}"
            if "args" not in normalized_action and "arguments" in normalized_action:
                normalized_action["args"] = normalized_action.pop("arguments")
            if not isinstance(normalized_action.get("args"), dict):
                normalized_action["args"] = {}
            tool = normalized_action.get("tool")
            args = normalized_action.setdefault("args", {})
            if tool == "filesystem":
                args.setdefault("action", "list_dir")  
            tool = normalized_action.get("tool")
            args = normalized_action.get("args", {})
            if tool is None:
                continue
            if tool == "filesystem" and "action" not in args:
                continue 
            normalized_actions.append(normalized_action)

        return {
            "goal": str(parsed.get("goal") or objective),
            "reasoning": str(parsed.get("reasoning") or ""),
            "expected_result": str(parsed.get("expected_result") or objective),
            "continue": bool(parsed.get("continue", False)) or bool(normalized_actions),
            "actions": normalized_actions,
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