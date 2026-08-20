from __future__ import annotations

from typing import Any

from clawai.tools.composio_tool import composio


class ToolRegistry:

    def __init__(self):

        self._tools = {
            "composio": composio,
        }

    def names(self):

        return sorted(
            self._tools.keys()
        )

    def get(
        self,
        name: str,
    ):

        return self._tools[name]

    def execute(
        self,
        tool: str,
        action: str,
        **kwargs: Any,
    ):

        instance = self.get(tool)

        method = getattr(
            instance,
            action,
        )

        return method(
            **kwargs,
        )


tool_registry = ToolRegistry()
