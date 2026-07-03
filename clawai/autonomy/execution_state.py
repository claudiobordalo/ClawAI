from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_JSON_SCALARS = (str, int, float, bool, type(None))


def _safe_copy(value: Any, seen: set[int] | None = None) -> Any:
    if seen is None:
        seen = set()

    if isinstance(value, _JSON_SCALARS):
        return value

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, bytearray):
        return bytes(value).decode("utf-8", errors="replace")

    if isinstance(value, Path):
        return str(value)

    obj_id = id(value)
    if obj_id in seen:
        return "<circular-reference>"

    if isinstance(value, dict):
        seen.add(obj_id)
        return {str(key): _safe_copy(item, seen) for key, item in value.items()}

    if isinstance(value, list):
        seen.add(obj_id)
        return [_safe_copy(item, seen) for item in value]

    if isinstance(value, tuple):
        seen.add(obj_id)
        return tuple(_safe_copy(item, seen) for item in value)

    if isinstance(value, set):
        seen.add(obj_id)
        return [_safe_copy(item, seen) for item in sorted(value, key=lambda item: repr(item))]

    to_llm = getattr(value, "to_llm", None)
    if callable(to_llm):
        try:
            return _safe_copy(to_llm(), seen)
        except Exception:
            return str(value)

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            return _safe_copy(to_dict(), seen)
        except Exception:
            return str(value)

    if hasattr(value, "__dict__"):
        try:
            return _safe_copy(vars(value), seen)
        except Exception:
            return str(value)

    return str(value)


def _tail(items: list[Any], size: int) -> list[Any]:
    if size <= 0:
        return []
    return _safe_copy(items[-size:])


def _sanitize_iteration(item: Any) -> Any:
    cloned = _safe_copy(item)
    if isinstance(cloned, dict):
        cloned.pop("state", None)
        cloned.pop("execution_state", None)
        cloned.pop("tool_context", None)
        cloned.pop("provider_manager", None)
        cloned.pop("runtime", None)
    return cloned


@dataclass(slots=True)
class ExecutionState:
    objective: str = ""
    current_plan: list[dict[str, Any]] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)
    iterations: list[dict[str, Any]] = field(default_factory=list)
    opened_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    searches: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    pending_actions: list[dict[str, Any]] = field(default_factory=list)
    completed_actions: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    temporary_memory: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "current_plan": _safe_copy(self.current_plan),
            "subtasks": _safe_copy(self.subtasks),
            "iterations": [_sanitize_iteration(item) for item in self.iterations],
            "opened_files": _safe_copy(self.opened_files),
            "modified_files": _safe_copy(self.modified_files),
            "tool_results": _safe_copy(self.tool_results),
            "searches": _safe_copy(self.searches),
            "hypotheses": _safe_copy(self.hypotheses),
            "decisions": _safe_copy(self.decisions),
            "errors": _safe_copy(self.errors),
            "pending_actions": _safe_copy(self.pending_actions),
            "completed_actions": _safe_copy(self.completed_actions),
            "artifacts": _safe_copy(self.artifacts),
            "temporary_memory": _safe_copy(self.temporary_memory),
        }

    def to_llm(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "current_plan": _safe_copy(self.current_plan),
            "subtasks": _tail(self.subtasks, 10),
            "pending_actions": _tail(self.pending_actions, 10),
            "completed_actions": _tail(self.completed_actions, 10),
            "tool_results": _tail(self.tool_results, 8),
            "decisions": _tail(self.decisions, 5),
            "errors": _tail(self.errors, 5),
            "hypotheses": _tail(self.hypotheses, 5),
            "opened_files": _tail(self.opened_files, 10),
            "modified_files": _tail(self.modified_files, 10),
            "artifacts": _tail(self.artifacts, 10),
            "temporary_memory": _tail(self.temporary_memory, 5),
            "iteration_count": len(self.iterations),
        }

    def to_summary(self) -> dict[str, Any]:
        llm_view = self.to_llm()
        llm_view["recent_iterations"] = _safe_copy(self.iterations[-3:])
        llm_view["searches"] = _tail(self.searches, 5)
        return llm_view

    def set_plan(self, plan: list[dict[str, Any]]) -> None:
        self.current_plan = [_safe_copy(action) for action in plan if isinstance(action, dict)]
        self.subtasks = [str(action.get("tool") or "") for action in plan if isinstance(action, dict)]

    def set_pending_actions(self, actions: list[dict[str, Any]]) -> None:
        self.pending_actions = [_safe_copy(action) for action in actions if isinstance(action, dict)]

    def add_tool_result(self, tool_result: dict[str, Any]) -> None:
        self.tool_results.append(_safe_copy(tool_result))

    def mark_action_completed(self, action: dict[str, Any]) -> None:
        action_copy = _safe_copy(action)
        self.completed_actions.append(action_copy)

        action_id = action_copy.get("id") if isinstance(action_copy, dict) else None
        if action_id is not None:
            self.pending_actions = [
                pending
                for pending in self.pending_actions
                if not (isinstance(pending, dict) and pending.get("id") == action_id)
            ]
        else:
            self.pending_actions = [pending for pending in self.pending_actions if pending != action_copy]

    def add_decision(self, decision: str) -> None:
        self.decisions.append(str(decision))

    def add_memory(self, text: str) -> None:
        self.temporary_memory.append(str(text))

    def add_hypothesis(self, hypothesis: str) -> None:
        self.hypotheses.append(str(hypothesis))

    def register_error(self, error: str) -> None:
        self.errors.append(str(error))

    def mark_opened_file(self, path: str) -> None:
        self.opened_files.append(str(path))

    def mark_modified_file(self, path: str) -> None:
        self.modified_files.append(str(path))

    def add_search(self, query: str) -> None:
        self.searches.append(str(query))

    def add_artifact(self, artifact: str) -> None:
        self.artifacts.append(str(artifact))

    def add_iteration(self, iteration: dict[str, Any]) -> None:
        self.iterations.append(_sanitize_iteration(iteration))
