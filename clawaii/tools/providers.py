from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from clawai.tools.tool import Tool


class BaseToolProvider(ABC):
    @abstractmethod
    def list_tools(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def get_tool(self, name: str) -> Tool | None:
        raise NotImplementedError

    def execute(self, name: str, **kwargs: Any) -> dict[str, Any]:
        tool = self.get_tool(name)
        if tool is None:
            return {
                "success": False,
                "tool": name,
                "result": None,
                "error": f"Tool not found: {name}",
                "duration_ms": 0.0,
            }
        return tool.execute(**kwargs)


class LocalToolProvider(BaseToolProvider):
    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools = {tool.name: tool for tool in (tools or [])}

    def register_tool(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)


class ComposioToolProvider(BaseToolProvider):
    def __init__(self, client: Any | None = None, tools: list[Tool] | None = None) -> None:
        self._client = client
        self._tools = {tool.name: tool for tool in (tools or [])}

    def register_tool(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def execute(self, name: str, **kwargs: Any) -> dict[str, Any]:
        tool = self.get_tool(name)
        if tool is not None:
            return tool.execute(**kwargs)
        return {
            "success": False,
            "tool": name,
            "result": None,
            "error": f"Tool not found in Composio provider: {name}",
            "duration_ms": 0.0,
        }


class MCPToolProvider(BaseToolProvider):
    def __init__(self, client: Any | None = None, tools: list[Tool] | None = None) -> None:
        self._client = client
        self._tools = {tool.name: tool for tool in (tools or [])}

    def register_tool(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def execute(self, name: str, **kwargs: Any) -> dict[str, Any]:
        tool = self.get_tool(name)
        if tool is not None:
            return tool.execute(**kwargs)
        return {
            "success": False,
            "tool": name,
            "result": None,
            "error": f"Tool not found in MCP provider: {name}",
            "duration_ms": 0.0,
        }
