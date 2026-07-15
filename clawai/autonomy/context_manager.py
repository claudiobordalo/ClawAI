from __future__ import annotations

from typing import Any


class ContextManager:
    def __init__(self, *, max_recent_actions: int = 5, max_recent_results: int = 5) -> None:
        self.max_recent_actions = max_recent_actions
        self.max_recent_results = max_recent_results

    def build_prompt(self, *, state: dict[str, Any], objective: str) -> str:
        workspace_path = self._state_value(state, ("workspace_path", "workspace", "path", "root"))
        current_plan = self._as_list(state.get("current_plan") if isinstance(state, dict) else getattr(state, "current_plan", None))
        pending_actions = self._as_list(state.get("pending_actions") if isinstance(state, dict) else getattr(state, "pending_actions", None))
        completed_actions = self._as_list(state.get("completed_actions") if isinstance(state, dict) else getattr(state, "completed_actions", None))
        tool_results = self._as_list(state.get("tool_results") if isinstance(state, dict) else getattr(state, "tool_results", None))
        decisions = self._as_list(state.get("decisions") if isinstance(state, dict) else getattr(state, "decisions", None))
        errors = self._as_list(state.get("errors") if isinstance(state, dict) else getattr(state, "errors", None))
        hypotheses = self._as_list(state.get("hypotheses") if isinstance(state, dict) else getattr(state, "hypotheses", None))
        opened_files = self._as_list(state.get("opened_files") if isinstance(state, dict) else getattr(state, "opened_files", None))
        modified_files = self._as_list(state.get("modified_files") if isinstance(state, dict) else getattr(state, "modified_files", None))
        temporary_memory = self._as_list(state.get("temporary_memory") if isinstance(state, dict) else getattr(state, "temporary_memory", None))
        subtasks = self._as_list(state.get("subtasks") if isinstance(state, dict) else getattr(state, "subtasks", None))

        parts: list[str] = [
            "INSTRUÇÕES:",
            "- Use o contexto como referência, não o repita.",
            "- Decida ações apenas quando houver ferramenta útil.",
            "- Não invente ferramentas nem ações.",
            "- Se houver um caminho de workspace informado, priorize-o para operações de filesystem.",
            "",
            f"OBJETIVO REAL: {self._short_text(objective, 800)}",
        ]

        if workspace_path:
            parts.append(f"WORKSPACE ATIVO: {self._short_text(workspace_path, 240)}")
        if current_plan:
            parts.append("PLANO ATUAL: " + self._summarize_actions(current_plan[-self.max_recent_actions :]))
        if pending_actions:
            parts.append("AÇÕES PENDENTES: " + self._summarize_actions(pending_actions[-self.max_recent_actions :]))
        if completed_actions:
            parts.append("AÇÕES CONCLUÍDAS: " + self._summarize_actions(completed_actions[-self.max_recent_actions :]))
        if tool_results:
            parts.append("RESULTADOS RECENTES: " + self._summarize_results(tool_results[-self.max_recent_results :]))
        if decisions:
            parts.append("DECISÕES RECENTES: " + " | ".join(self._short_text(str(item)) for item in decisions[-3:]))
        if errors:
            parts.append("ERROS RECENTES: " + " | ".join(self._short_text(str(item)) for item in errors[-3:]))
        if hypotheses:
            parts.append("HIPÓTESES RECENTES: " + " | ".join(self._short_text(str(item)) for item in hypotheses[-3:]))
        if opened_files:
            parts.append("ARQUIVOS ABERTOS: " + " | ".join(self._short_text(str(item)) for item in opened_files[-5:]))
        if modified_files:
            parts.append("ARQUIVOS MODIFICADOS: " + " | ".join(self._short_text(str(item)) for item in modified_files[-5:]))
        if subtasks:
            parts.append("SUBTAREFAS: " + " | ".join(self._short_text(str(item)) for item in subtasks[-5:]))
        if temporary_memory:
            parts.append("MEMÓRIA RECENTE: " + " | ".join(self._short_text(str(item)) for item in temporary_memory[-5:]))

        return self._clip("\n".join(parts), 5000)

    def _state_value(self, state: dict[str, Any], keys: tuple[str, ...]) -> str | None:
        for key in keys:
            # value = state.get(key)
            value = getattr(state, key, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _clip(self, text: str, limit: int) -> str:
        text = (text or "").strip()
        return text if len(text) <= limit else text[:limit] + "..."

    def _as_list(self, value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    def _summarize_actions(self, items: list[Any]) -> str:
        summaries: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                summaries.append(self._short_text(str(item)))
                continue
            tool = self._short_text(str(item.get("tool") or item.get("name") or "action"))
            action_id = self._short_text(str(item.get("id") or ""))
            if action_id:
                summaries.append(f"{action_id}:{tool}")
            else:
                summaries.append(tool)
        return "; ".join(summaries) if summaries else "(vazio)"

    def _summarize_results(self, items: list[Any]) -> str:
        summaries: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                summaries.append(self._short_text(str(item)))
                continue
            tool = self._short_text(str(item.get("tool") or "tool"))
            success = item.get("success")
            status = "ok" if success is True else "erro" if success is False else "?"
            result = item.get("result")
            result_text = self._short_text(str(result)) if result is not None else ""
            summaries.append(f"{tool}:{status}" + (f"={result_text}" if result_text else ""))
        return "; ".join(summaries) if summaries else "(vazio)"

    def _short_text(self, text: str, limit: int = 120) -> str:
        text = (text or "").strip().replace("\n", " ")
        return text if len(text) <= limit else text[:limit] + "..."
