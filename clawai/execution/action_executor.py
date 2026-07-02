from __future__ import annotations

import time
from typing import Any, Callable

from clawai.autonomy.execution_state import ExecutionState
from clawai.autonomy.tool_context import ToolContext
from clawai.tools.tool_executor import ToolExecutor

RuntimeContract = dict[str, Any]
Action = dict[str, Any]


class ActionExecutor:
    """Executor orquestrador de Actions com validação, provider resolution e registro de estado."""

    def __init__(
        self,
        *,
        tool_executor: ToolExecutor | None = None,
        provider_registry: dict[str, Any] | None = None,
        execution_state: ExecutionState | None = None,
        tool_context: ToolContext | None = None,
    ) -> None:
        self._tool_executor = tool_executor
        self._provider_registry = provider_registry or {}
        self._execution_state = execution_state
        self._tool_context = tool_context

        self._handlers: dict[str, Callable[[Action], RuntimeContract]] = {
            "tool": self._execute_tool_action,
        }

    def execute(self, action: Action) -> RuntimeContract:
        start = time.perf_counter()
        try:
            if not isinstance(action, dict):
                return self._error(tool=None, error="Invalid action: expected dict.", start=start, result=None)

            action_type = action.get("type") or "tool"
            if action_type == "tool":
                required = ("tool",)
                missing = [k for k in required if k not in action]
                if missing:
                    return self._error(
                        tool=None,
                        error=f'Invalid action: missing required field(s) {missing}.',
                        start=start,
                        result=None,
                    )
                if "args" not in action and "arguments" not in action:
                    return self._error(
                        tool=None,
                        error="Invalid action: missing required field(s) ['args'].",
                        start=start,
                        result=None,
                    )

            handler = self._handlers.get(action_type)
            if handler is None:
                return self._error(tool=None, error=f'Unsupported action type: "{action_type}".', start=start, result=None)

            return handler(action)
        except Exception as e:
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
        arguments = action.get("args") or action.get("arguments", {})
        provider_name = action.get("provider") or "local"

        try:
            if self._execution_state is not None:
                self._execution_state.pending_actions.append(action)

            provider = self._provider_registry.get(provider_name)
            if provider is not None:
                tool = provider.get_tool(tool_name)
                if tool is None:
                    return self._error(tool=tool_name, error=f"Tool not found in provider '{provider_name}'.", start=start, result=None)
                res = tool.execute(**arguments)
                self._register_result(action=action, execution=res)
                return self._normalize_result(tool_name=tool_name, execution=res)

            if self._tool_executor is not None:
                res = self._tool_executor.execute(tool_name=tool_name, arguments=arguments)
                self._register_result(action=action, execution=res)
                return res

            return self._error(tool=tool_name, error="No tool executor or provider available.", start=start, result=None)
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "result": None,
                "error": str(e),
                "duration_ms": (time.perf_counter() - start) * 1000,
            }

    def _normalize_result(self, *, tool_name: str, execution: Any) -> RuntimeContract:
        if isinstance(execution, dict) and {"success", "result", "error", "duration_ms"} <= set(execution.keys()):
            return {
                "success": bool(execution.get("success")),
                "tool": tool_name,
                "result": execution.get("result"),
                "error": execution.get("error"),
                "duration_ms": execution.get("duration_ms"),
            }
        return {
            "success": True,
            "tool": tool_name,
            "result": execution,
            "error": None,
            "duration_ms": None,
        }

    def _register_result(self, *, action: Action, execution: Any) -> None:
        if self._execution_state is None:
            return
        payload = execution
        if isinstance(execution, dict) and {"success", "result", "error", "duration_ms"} <= set(execution.keys()):
            payload = execution.get("result")
        self._execution_state.add_tool_result({"tool": action.get("tool"), "result": payload})
        self._execution_state.mark_action_completed({
            "id": action.get("id"),
            "tool": action.get("tool"),
            "arguments": action.get("args") or action.get("arguments", {}),
        })
        if self._tool_context is not None and self._tool_context.execution_state is None:
            self._tool_context.execution_state = self._execution_state

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
