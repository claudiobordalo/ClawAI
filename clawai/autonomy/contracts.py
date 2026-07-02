from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class Action:
    id: str
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timeout: int | None = None
    retry_policy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tool": self.tool,
            "args": self.args,
            "priority": self.priority,
            "timeout": self.timeout,
            "retry_policy": self.retry_policy,
        }


@dataclass(slots=True)
class ActionResult:
    action_id: str
    success: bool
    tool: str
    result: Any = None
    error: str | None = None
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "success": self.success,
            "tool": self.tool,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass(slots=True)
class PlannerResult:
    objective: str
    reasoning: str
    expected_result: str
    continue_: bool
    actions: list[Action]

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "reasoning": self.reasoning,
            "expected_result": self.expected_result,
            "continue": self.continue_,
            "actions": [action.to_dict() for action in self.actions],
        }

    def __getitem__(self, key: str) -> Any:
        if key == "actions":
            return self.actions
        return self.to_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        if key == "actions":
            return self.actions
        return self.to_dict().get(key, default)


@dataclass(slots=True)
class ReflectionResult:
    reflection: str
    should_continue: bool
    error_type: str | None = None
    needs_retry: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "reflection": self.reflection,
            "should_continue": self.should_continue,
            "error_type": self.error_type,
            "needs_retry": self.needs_retry,
        }


@dataclass(slots=True)
class Permission:
    name: str
    allowed: bool
    reason: str | None = None


@dataclass(slots=True)
class ToolMetadata:
    name: str
    description: str
    provider: str = "local"
    version: str = "1.0.0"


@dataclass(slots=True)
class ProviderResult:
    provider: str
    success: bool
    tools: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True)
class ToolContext:
    workspace: str | None = None
    execution_state: Any | None = None
    permissions: dict[str, Permission] = field(default_factory=dict)
    logger: Any | None = None
    config: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    current_iteration: int = 0
    cancellation_token: Any | None = None
