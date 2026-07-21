from __future__ import annotations

import time
from typing import Any, Protocol

from clawai.tools.tool import Tool

RuntimeResult = dict[str, Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> RuntimeResult:
        start = time.perf_counter()
        try:
            name = tool.name
            self._tools[name] = tool
            return {
                "success": True,
                "result": {"name": name},
                "error": None,
                "duration_ms": (time.perf_counter() - start) * 1000,
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    def unregister(self, name: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            existed = name in self._tools
            if existed:
                del self._tools[name]
            return {
                "success": True,
                "result": {"name": name, "existed": existed},
                "error": None,
                "duration_ms": (time.perf_counter() - start) * 1000,
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    def get(self, name: str) -> RuntimeResult:
        start = time.perf_counter()
        try:
            tool = self._tools.get(name)
            if tool is None:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Tool not found: {name}",
                    "duration_ms": (time.perf_counter() - start) * 1000,
                }
            return {
                "success": True,
                "result": tool,
                "error": None,
                "duration_ms": (time.perf_counter() - start) * 1000,
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    def list_tools(self) -> RuntimeResult:
        start = time.perf_counter()
        try:
            return {
                "success": True,
                "result": sorted(self._tools.keys()),
                "error": None,
                "duration_ms": (time.perf_counter() - start) * 1000,
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    def health(self) -> RuntimeResult:
        start = time.perf_counter()
        try:
            return {
                "success": True,
                "result": {"registered_tools": len(self._tools)},
                "error": None,
                "duration_ms": (time.perf_counter() - start) * 1000,
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }
