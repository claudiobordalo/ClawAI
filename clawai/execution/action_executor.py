from __future__ import annotations

import time
from typing import Any, Callable

from clawai.tools.tool_executor import ToolExecutor

RuntimeContract = dict[str, Any]
Action = dict[str, Any]


class ActionExecutor:
    """
    Executor orquestrador de Actions.

    Responsabilidade única:
    - Validar e encaminhar a Action para o executor apropriado.
    - Não conhece implementações concretas de ferramentas.
    - Não acessa ToolRegistry.
    """

    def __init__(self, *, tool_executor: ToolExecutor) -> None:
        self._tool_executor = tool_executor

        self._handlers: dict[str, Callable[[Action], RuntimeContract]] = {
            "tool": self._execute_tool_action,
        }

    def execute(self, action: Action) -> RuntimeContract:
        start = time.perf_counter()
        try:
            if not isinstance(action, dict):
                return self._error(
                    tool=None,
                    error="Invalid action: expected dict.",
                    start=start,
                    result=None,
                )

            # Campos obrigatórios para Actions estruturadas
            action_type = action.get("type")
            if not action_type:
                return self._error(
                    tool=None,
                    error='Invalid action: missing required field "type".',
                    start=start,
                    result=None,
                )

            if action_type == "tool":
                required = ("tool", "arguments")
                missing = [k for k in required if k not in action]
                if missing:
                    return self._error(
                        tool=None,
                        error=f'Invalid action: missing required field(s) {missing}.',
                        start=start,
                        result=None,
                    )

            handler = self._handlers.get(action_type)
            if handler is None:
                return self._error(
                    tool=None,
                    error=f'Unsupported action type: "{action_type}".',
                    start=start,
                    result=None,
                )

            return handler(action)
        except Exception as e:
            # Nunca lançar exceções para o chamador.
            return {
                "success": False,
                "tool": None,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    def _execute_tool_action(self, action: Action) -> RuntimeContract:
        start = time.perf_counter()
        tool_name = action.get("tool")
        arguments = action.get("arguments", {})

        try:
            # ToolExecutor cuida da padronização do contrato.
            res = self._tool_executor.execute(
                tool_name=tool_name,
                arguments=arguments,
            )

            # Mantém compatibilidade total: retorna o contrato do ToolExecutor.
            return res
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    def _error(
        self,
        *,
        tool: str | None,
        error: str,
        start: float,
        result: Any,
    ) -> RuntimeContract:
        return {
            "success": False,
            "tool": tool,
            "result": result,
            "error": error,
            "duration_ms": (time.perf_counter() - start) * 1000,
        }
