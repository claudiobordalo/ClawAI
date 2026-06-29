from __future__ import annotations

from dataclasses import asdict
from typing import Any

from clawai.tools.base import Tool
from clawai.tools.registry import tool_registry

from .executor import composio_executor
from .models import ComposioExecutionRequest, ComposioExecutionResult, ComposioToolInfo
from .tool_discovery import composio_tool_discovery


class ComposioRegistryTool(Tool):
    def __init__(self, service: "ComposioService") -> None:
        self._service = service

    @property
    def name(self) -> str:
        return "composio"

    def execute(self, **kwargs: Any) -> Any:
        action = str(kwargs.pop("action", kwargs.pop("tool_action", kwargs.pop("command", "discover"))))
        tool_name = str(kwargs.pop("tool_name", kwargs.pop("tool", "composio")))
        if action in {"discover", "tools", "list"}:
            return [asdict(tool) for tool in self._service.discover_tools(force_refresh=bool(kwargs.pop("force_refresh", False)))]
        if action in {"connections", "list_connections"}:
            return [asdict(connection) for connection in self._service.connections(force_refresh=bool(kwargs.pop("force_refresh", False)))]
        if action in {"summary", "status"}:
            return self._service.summary()
        return self._service.execute(
            ComposioExecutionRequest(
                tool_name=tool_name,
                action=action,
                parameters=kwargs,
            )
        )

    def connections(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        return [asdict(item) for item in self._service.connections(force_refresh=force_refresh)]


class ComposioService:
    def discover_tools(self, force_refresh: bool = False) -> list[ComposioToolInfo]:
        return composio_tool_discovery.discover_tools(force_refresh=force_refresh)

    def connections(self, force_refresh: bool = False) -> list[Any]:
        return composio_tool_discovery.discover_connections(force_refresh=force_refresh)

    def execute(self, request: ComposioExecutionRequest) -> ComposioExecutionResult:
        return composio_executor.execute(request)

    def summary(self) -> dict[str, Any]:
        return {
            "discovery": composio_tool_discovery.summary(),
            "tools": [asdict(tool) for tool in self.discover_tools()],
            "connections": [asdict(item) for item in self.connections()],
        }

    def register_tool(self) -> ComposioRegistryTool:
        existing = tool_registry._tools.get("composio") if hasattr(tool_registry, "_tools") else None
        if isinstance(existing, ComposioRegistryTool):
            return existing

        adapter = ComposioRegistryTool(self)
        tool_registry.register(adapter)
        return adapter


composio_service = ComposioService()


def register_composio_tool() -> ComposioRegistryTool:
    return composio_service.register_tool()
