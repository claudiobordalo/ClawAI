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


class LocalToolProvider(BaseToolProvider):
    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools = {tool.name: tool for tool in (tools or [])}

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)


class ComposioToolProvider(BaseToolProvider):
    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def list_tools(self) -> list[str]:
        return []

    def get_tool(self, name: str) -> Tool | None:
        return None


class MCPToolProvider(BaseToolProvider):
    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def list_tools(self) -> list[str]:
        return []

    def get_tool(self, name: str) -> Tool | None:
        return None
