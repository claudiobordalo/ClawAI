from __future__ import annotations

from typing import Any

from clawai.tools.registry.registry import ToolRegistry


class ToolManager:

    def __init__(
        self,
        registry: ToolRegistry,
    ) -> None:

        self._registry = registry

    def execute(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> Any:

        tool = self._registry.get(tool_name)

        return tool.execute(**kwargs)
