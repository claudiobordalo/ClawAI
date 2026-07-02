from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
            "current_plan": self.current_plan,
            "subtasks": self.subtasks,
            "iterations": self.iterations,
            "opened_files": self.opened_files,
            "modified_files": self.modified_files,
            "tool_results": self.tool_results,
            "searches": self.searches,
            "hypotheses": self.hypotheses,
            "decisions": self.decisions,
            "errors": self.errors,
            "pending_actions": self.pending_actions,
            "completed_actions": self.completed_actions,
            "artifacts": self.artifacts,
            "temporary_memory": self.temporary_memory,
        }

    def set_plan(self, plan: list[dict[str, Any]]) -> None:
        self.current_plan = list(plan)
        self.subtasks = [str(action.get("tool") or "") for action in plan if isinstance(action, dict)]

    def add_tool_result(self, tool_result: dict[str, Any]) -> None:
        self.tool_results.append(tool_result)

    def mark_action_completed(self, action: dict[str, Any]) -> None:
        self.completed_actions.append(action)
        if action in self.pending_actions:
            self.pending_actions.remove(action)

    def add_hypothesis(self, hypothesis: str) -> None:
        self.hypotheses.append(hypothesis)

    def register_error(self, error: str) -> None:
        self.errors.append(error)
