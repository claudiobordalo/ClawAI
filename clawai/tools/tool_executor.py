from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from clawai.tools.tool_registry import ToolRegistry

RuntimeContract = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    tool: str
    arguments: dict[str, Any]


class ToolExecutor:
    """
    ToolExecutor (sprint 2):
    - depende APENAS de ToolRegistry
    - nunca lança exceções para o chamador
    - sempre retorna o contrato padronizado
    """

    def __init__(self, *, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> RuntimeContract:
        start = time.perf_counter()
        try:
            reg = self._registry.get(tool_name)
            if not reg.get("success"):
                return {
                    "success": False,
                    "tool": tool_name,
                    "result": None,
                    "error": reg.get("error") or "Tool not found",
                    "duration_ms": (time.perf_counter() - start) * 1000,
                }

            tool = reg.get("result")
            res = tool.execute(**arguments)

            # Mantém compatibilidade: se a tool retornar o contrato, passa.
            if isinstance(res, dict) and {"success", "result", "error", "duration_ms"} <= set(res.keys()):
                # tool pode ter retornado duration_ms próprio; recalculamos para contrato consistente.
                return {
                    "success": bool(res.get("success")),
                    "tool": tool_name,
                    "result": res.get("result"),
                    "error": res.get("error"),
                    "duration_ms": (time.perf_counter() - start) * 1000,
                }

            # Se a tool não seguir contrato, encapsulamos.
            return {
                "success": True,
                "tool": tool_name,
                "result": res,
                "error": None,
                "duration_ms": (time.perf_counter() - start) * 1000,
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    def execute_tool_call(self, call: ToolCall) -> RuntimeContract:
        return self.execute(tool_name=call.tool, arguments=call.arguments)

    def execute_json(self, json_text: str) -> RuntimeContract:
        start = time.perf_counter()
        try:
            data = json.loads(json_text)
            tool_name = data["tool"]
            arguments = data.get("arguments", {})
            return self.execute(tool_name=tool_name, arguments=arguments)
        except Exception as e:
            return {
                "success": False,
                "tool": None,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }


# Compat: mantém um singleton, mas sem depender de FilesystemTool.
tool_executor = ToolExecutor(registry=ToolRegistry())
