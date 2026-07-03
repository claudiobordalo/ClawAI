from __future__ import annotations

import json
from typing import Any, Protocol

from clawai.autonomy.context_manager import ContextManager
from clawai.autonomy.execution_state import ExecutionState
from clawai.autonomy.llm_metrics import LLMCallMetrics
from clawai.autonomy.planner import Planner
from clawai.autonomy.reflector import Reflector
from clawai.autonomy.synthesizer import Synthesizer
from clawai.autonomy.tool_context import ToolContext
from clawai.execution.action_executor import ActionExecutor
from clawai.tools.filesystem_tool import FilesystemTool
from clawai.tools.provider_manager import ProviderManager
from clawai.tools.providers import LocalToolProvider
from clawai.tools.tool_executor import ToolExecutor
from clawai.tools.tool_registry import ToolRegistry


class RouterProtocol(Protocol):
    def ask(self, *, prompt: str, role: Any, system_prompt: str | None = None) -> str: ...
    def model_for(self, role: Any) -> str: ...


class AgentRuntime:
    def __init__(
        self,
        *,
        router: RouterProtocol,
        tool_executor: ToolExecutor | None = None,
        max_iterations: int = 3,
    ) -> None:
        self.router = router
        self.tool_executor = tool_executor or self._build_default_tool_executor()
        self.max_iterations = max(1, int(max_iterations))
        self.provider_manager = self._build_default_provider_manager()
        self.context_manager = ContextManager()
        self.llm_metrics = LLMCallMetrics(max_calls=10)
        self.planner = Planner(router=self.router)
        self.reflector = Reflector(router=self.router)
        self.synthesizer = Synthesizer(router=self.router)

    def run(self, prompt: str, *, file: str | None = None) -> dict[str, Any]:
        _ = file  # mantido por compatibilidade com chamadas antigas
        state = ExecutionState(objective=prompt)
        history: list[dict[str, Any]] = []

        context = self.context_manager.build_prompt(state=state.to_llm(), objective=prompt)

        for iteration in range(1, self.max_iterations + 1):
            if self._llm_budget_reached():
                break

            self.llm_metrics.record("planner", metadata={"iteration": iteration})
            decision = self.planner.plan(
                objective=prompt,
                context=context,
                iteration=iteration,
                available_tools=self._available_tools_summary(),
                state=state.to_llm(),
            )

            actions = decision.get("actions") if isinstance(decision.get("actions"), list) else []
            state.set_plan(actions)
            state.decisions.append(str(decision.get("reasoning") or ""))
            state.pending_actions = [dict(action) for action in actions if isinstance(action, dict)]

            tool_context = ToolContext(
                execution_state=state,
                current_iteration=iteration,
            )
            action_executor = ActionExecutor(
                tool_executor=self.tool_executor,
                execution_state=state,
                tool_context=tool_context,
            )

            tool_calls: list[dict[str, Any]] = []
            tool_results: list[dict[str, Any]] = []

            for action in actions:
                if not isinstance(action, dict):
                    continue

                execution = action_executor.execute(action)
                tool_name = action.get("tool")
                arguments = action.get("args") or action.get("arguments") or {}

                tool_calls.append({"tool": tool_name, "arguments": arguments})
                tool_results.append(
                    {
                        "tool": tool_name,
                        "success": execution.get("success"),
                        "result": execution.get("result"),
                        "error": execution.get("error"),
                        "duration_ms": execution.get("duration_ms"),
                    }
                )

            context = self.context_manager.build_prompt(state=state.to_llm(), objective=prompt)

            snapshot = {
                "iteration": iteration,
                "plan": [dict(action) for action in actions if isinstance(action, dict)],
                "tool_calls": tool_calls,
                "tool_results": tool_results,
                "reflection": "",
            }

            if self._llm_budget_reached():
                history.append(snapshot)
                state.add_iteration(snapshot)
                break

            self.llm_metrics.record("reflection", metadata={"iteration": iteration})
            reflection = self.reflector.reflect(
                objective=prompt,
                context=context,
                decision=decision,
                tool_results=tool_results,
                iteration=iteration,
                state=state.to_llm(),
            )

            if reflection.get("error_type") and reflection.get("error_type") != "none":
                state.register_error(str(reflection.get("error_type")))
            if reflection.get("reflection"):
                state.temporary_memory.append(str(reflection.get("reflection")))

            snapshot["reflection"] = str(reflection.get("reflection") or "")
            history.append(snapshot)
            state.add_iteration(snapshot)

            context = self.context_manager.build_prompt(state=state.to_llm(), objective=prompt)

            if not reflection.get("should_continue", False) and not decision.get("continue", False):
                break

        if self._llm_budget_reached():
            return {
                "answer": self._fallback_answer(history, prompt),
                "history": history,
                "used_tools": any(item["tool_results"] for item in history),
                "iterations": len(history),
                "state": state.to_dict(),
                "llm_metrics": self.llm_metrics.snapshot(),
                "abort_reason": "Maximum LLM calls reached.",
            }

        self.llm_metrics.record("synthesis", metadata={"iterations": len(history)})
        answer = self.synthesizer.synthesize(
            objective=prompt,
            history=history,
        )

        return {
            "answer": answer,
            "history": history,
            "used_tools": any(item["tool_results"] for item in history),
            "iterations": len(history),
            "state": state.to_dict(),
            "llm_metrics": self.llm_metrics.snapshot(),
            "abort_reason": None,
        }

    def _build_default_tool_executor(self) -> ToolExecutor:
        registry = ToolRegistry()
        registry.register(FilesystemTool())
        return ToolExecutor(registry=registry)

    def _build_default_provider_manager(self) -> ProviderManager:
        manager = ProviderManager()
        manager.register("local", LocalToolProvider([FilesystemTool()]))
        return manager

    def _available_tools_summary(self) -> list[dict[str, Any]]:
        try:
            tools: list[dict[str, Any]] = []
            for tool_name in self.provider_manager.list_tools():
                resolved = self.provider_manager.get_tool(tool_name)
                if resolved is None:
                    continue
                provider_name, tool = resolved
                tools.append(
                    {
                        "name": tool_name,
                        "provider": provider_name,
                        "description": getattr(tool, "description", "") or "",
                    }
                )
            return tools
        except Exception:
            return []

    def _llm_budget_reached(self) -> bool:
        return len(self.llm_metrics.calls) >= self.llm_metrics.max_calls

    def _fallback_answer(self, history: list[dict[str, Any]], prompt: str) -> str:
        if history:
            last = history[-1]
            reflection = str(last.get("reflection") or "").strip()
            if reflection:
                return reflection

            tool_results = last.get("tool_results") or []
            if tool_results:
                return (
                    "Execução interrompida antes da síntese final por limite de chamadas ao LLM. "
                    f"Últimos resultados: {json.dumps(tool_results, ensure_ascii=False)}"
                )

        return (
            "Execução interrompida antes da síntese final por limite de chamadas ao LLM. "
            f"Objetivo: {prompt}"
        )


class AutonomyLoop(AgentRuntime):
    pass