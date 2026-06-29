from __future__ import annotations

from clawai.tools.base.tool import Tool

class ToolRegistry:

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        tool: Tool,
    ) -> None:

        self._tools[tool.name] = tool

    def unregister(
        self,
        name: str,
    ) -> None:

        self._tools.pop(name, None)

    def get(
        self,
        name: str,
    ) -> Tool:

        return self._tools[name]

    def exists(
        self,
        name: str,
    ) -> bool:

        return name in self._tools

    def all(
        self,
    ) -> list[Tool]:

        return list(self._tools.values())

tool_registry = ToolRegistry()