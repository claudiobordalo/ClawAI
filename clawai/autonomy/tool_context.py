from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolContext:
    workspace: str | None = None
    execution_state: Any | None = None
    permissions: dict[str, Any] = field(default_factory=dict)
    logger: Any | None = None
    config: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    current_iteration: int = 0
    cancellation_token: Any | None = None
