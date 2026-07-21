from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class ComposioToolInfo:
    name: str
    provider: str = "composio"
    category: str = "integration"
    description: str = ""
    connected: bool = False
    actions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ComposioConnection:
    toolkit: str
    status: str = "unknown"
    user_id: str = ""
    external_user_id: str = ""
    provider: str = "composio"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ComposioExecutionRequest:
    tool_name: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    provider: str = "composio"
    workspace_id: str = ""


@dataclass(slots=True, frozen=True)
class ComposioExecutionResult:
    success: bool
    tool_name: str
    action: str
    provider: str
    output: Any = None
    error: str = ""
    elapsed_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ToolBrokerDecision:
    recommended_tool: str
    provider: str
    reason: str
    confidence: float
    parallel_agents: list[str] = field(default_factory=list)
    memory_hits: int = 0
    source: str = "heuristic"


@dataclass(slots=True, frozen=True)
class ToolDescriptor:
    name: str
    provider: str
    category: str
    description: str = ""
    connected: bool = False
    actions: list[str] = field(default_factory=list)
    source: str = "native"
    metadata: dict[str, Any] = field(default_factory=dict)
