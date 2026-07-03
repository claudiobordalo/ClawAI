from __future__ import annotations

import json
import re
from typing import Any
from pathlib import Path

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
        Você é exclusivamente o PLANNER do ClawAI.

        Sua única função é decidir quais ferramentas executar.

        NUNCA responda ao usuário.

        NUNCA explique.

        NUNCA resuma.

        NUNCA copie o contexto recebido.

        Você deve retornar SOMENTE JSON válido.

        Formato obrigatório:

        {
            "goal": "...",
            "reasoning": "...",
            "expected_result": "...",
            "continue": false,
            "actions": [
                {
                    "tool": "<tool>",
                    "args": { ... }
                }
            ]
        }

        Nunca utilize:

        - name
        - arguments

        Sempre utilize:

        tool
        args

        Quando precisar acessar arquivos utilize SEMPRE:

        {
            "tool":"filesystem",
            "args":{
                "action":"..."
            }
        }

        Se houver uma ferramenta apropriada para resolver o objetivo,
        actions NUNCA pode ficar vazio.
        """
        user_objective = self._extract_user_objective(objective)
        workspace_path = (
            self._extract_workspace_path(objective)
            or self._extract_workspace_path(context)
            or self._extract_workspace_path_from_state(state)
        )
        payload = (
            f"Pergunta do usuário: {user_objective}\n\n"
            f"Contexto resumido:\n{context}\n\n"
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
        parsed = self._apply_fallback_actions(
            parsed=parsed,
            objective=objective,
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
        if not normalized_actions:
            normalized_actions = self._infer_actions(
                user_objective=user_objective,
                workspace_path=workspace_path,
                available_tools=available_tools,
            )
        return {
            "goal": str(parsed.get("goal") or objective),
            "reasoning": str(parsed.get("reasoning") or ""),
            "expected_result": str(parsed.get("expected_result") or objective),
            "continue": bool(continue_flag),
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
        

def _extract_user_objective(self, text: str) -> str:
    if not text:
        return ""

    markers = (
        "Pergunta do usuário:",
        "Pergunta do usuario:",
        "Pergunta:",
    )

    lower = text.lower()

    for marker in markers:
        idx = lower.rfind(marker.lower())
        if idx != -1:
            value = text[idx + len(marker):].strip()
            if value:
                return value

    return text.strip()

def _extract_workspace_path(self, text: str) -> str | None:
    if not text:
        return None

    m = re.search(r"(?im)^Caminho:\s*(.+)$", text)
    if m:
        return m.group(1).strip()

    m = re.search(r"[A-Za-z]:\\[^\n\r]+", text)
    if m:
        return m.group(0)

    return None

def _extract_workspace_path_from_state(
    self,
    state: dict[str, Any],
) -> str | None:

    for key in (
        "workspace_path",
        "workspace",
        "path",
        "root",
    ):
        value = state.get(key)

        if isinstance(value, str) and value.strip():
            return value

    return None

def _infer_actions(
    self,
    *,
    user_objective: str,
    workspace_path: str | None,
    available_tools: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not self._tool_available(available_tools, "filesystem"):
        return []

    text = user_objective.lower()
    path = workspace_path or "."

    if re.search(r"\b(list|liste|listar|mostre|mostrar)\b", text) and (
        "arquivo" in text or "files" in text or "pasta" in text or "diret" in text
    ):
        limit = 10 if re.search(r"\b10\b", text) else 50
        return [{
            "tool": "filesystem",
            "args": {"action": "list_dir", "path": path, "limit": limit},
        }]

    path_match = self._extract_workspace_path(user_objective)
    if path_match and any(k in text for k in ("acessar", "abrir", "listar", "ver", "explorar")):
        limit = 10 if re.search(r"\b10\b", text) else 50
        return [{
            "tool": "filesystem",
            "args": {"action": "list_dir", "path": path_match, "limit": limit},
        }]

    file_matches = list(dict.fromkeys(
        re.findall(r"\b[\w.\-]+\.(?:md|py|json|txt|toml|yml|yaml|ini|cfg|csv)\b", user_objective, flags=re.I)
    ))
    if file_matches and any(k in text for k in ("leia", "ler", "abra", "abrir", "analise", "analisar", "mostre", "mostrar", "read")):
        return [{
            "tool": "filesystem",
            "args": {"action": "read_text", "path": self._resolve_path(file_matches[0], path)},
        }]

    if file_matches and any(k in text for k in ("procure", "buscar", "encontre", "localize", "search")):
        return [{
            "tool": "filesystem",
            "args": {"action": "search", "root": path, "pattern": file_matches[0]},
        }]

    return []

def _tool_available(self, available_tools: list[dict[str, Any]], tool_name: str) -> bool:
    for tool in available_tools:
        if isinstance(tool, dict) and tool.get("name") == tool_name:
            return True
    return False

def _resolve_path(self, name: str, base: str) -> str:
    if re.match(r"^[A-Za-z]:\\", name) or name.startswith("\\\\"):
        return name
    if base in ("", "."):
        return name
    return str(Path(base) / name)