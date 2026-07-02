from __future__ import annotations

import json
import re
from typing import Any, Protocol

from clawai.autonomy.context_manager import ContextManager
from clawai.autonomy.execution_state import ExecutionState
from clawai.autonomy.llm_metrics import LLMCallMetrics
from clawai.autonomy.planner import Planner
from clawai.autonomy.reflector import Reflector
from clawai.autonomy.synthesizer import Synthesizer
from clawai.tools.filesystem_tool import FilesystemTool
from clawai.tools.provider_manager import ProviderManager
from clawai.tools.tool_executor import ToolExecutor
from clawai.tools.tool_registry import ToolRegistry


class RouterProtocol(Protocol):
    def ask(self, *, prompt: str, role: Any, system_prompt: str | None = None) -> str: ...


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
        self.provider_manager = ProviderManager().build_default()
        self.context_manager = ContextManager()
        self.llm_metrics = LLMCallMetrics(max_calls=10)

    def run(self, prompt: str, *, file: str | None = None) -> dict[str, Any]:
        state = ExecutionState(objective=prompt)
        history: list[dict[str, Any]] = []
        context = self._build_context(prompt, file)
        planner = Planner(router=self.router)
        reflector = Reflector(router=self.router)
        synthesizer = Synthesizer(router=self.router)

        for iteration in range(1, self.max_iterations + 1):
            self.llm_metrics.record("planner")
            decision = planner.plan(
                objective=prompt,
                context=context,
                iteration=iteration,
                available_tools=self._available_tools_summary(),
                state=state,
            )
            state.set_plan(decision.get("actions", []))
            state.decisions.append(decision.get("reasoning") or "")
            state.pending_actions = decision.get("actions", [])

            tool_calls: list[dict[str, Any]] = []
            tool_results: list[dict[str, Any]] = []

            for action in decision.get("actions", []):
                if not isinstance(action, dict):
                    continue
                tool_name = action.get("tool")
                arguments = action.get("args") or action.get("arguments") or {}
                if tool_name and self.tool_executor is not None:
                    execution = self.tool_executor.execute(tool_name=tool_name, arguments=arguments)
                    tool_calls.append({"tool": tool_name, "arguments": arguments})
                    tool_results.append({"tool": tool_name, "result": execution})
                    state.add_tool_result({"tool": tool_name, "result": execution})
                    state.mark_action_completed({"id": action.get("id"), "tool": tool_name, "arguments": arguments})

            self.llm_metrics.record("reflection")
            reflection = reflector.reflect(
                objective=prompt,
                context=context,
                decision=decision,
                tool_results=tool_results,
                iteration=iteration,
                state=state,
            )
            if reflection.get("error_type"):
                state.register_error(str(reflection.get("error_type")))
            if reflection.get("reflection"):
                state.temporary_memory.append(str(reflection.get("reflection")))
            history.append(
                {
                    "iteration": iteration,
                    "plan": decision.get("actions", []),
                    "tools_used": tool_calls,
                    "tool_results": tool_results,
                    "next_decision_reason": decision.get("reasoning") or "",
                    "reflection": reflection.get("reflection") or "",
                    "state": state.to_dict(),
                }
            )

            context = self._update_context(context, decision, tool_results, reflection)

            if not reflection.get("should_continue", False) and not decision.get("continue", False):
                break

        self.llm_metrics.record("synthesis")
        answer = synthesizer.synthesize(objective=prompt, history=history)
        return {
            "answer": answer,
            "history": history,
            "used_tools": any(item["tools_used"] for item in history),
            "iterations": len(history),
            "state": state.to_dict(),
            "llm_metrics": self.llm_metrics.snapshot(),
            "abort_reason": "Maximum LLM calls exceeded." if self.llm_metrics.should_abort else None,
        }

    def _build_default_tool_executor(self) -> ToolExecutor:
        registry = ToolRegistry()
        registry.register(FilesystemTool())
        return ToolExecutor(registry=registry)

    def _build_context(self, prompt: str, file: str | None) -> str:
        base = [f"Solicitação: {prompt}"]
        if file:
            base.append(f"Arquivo: {file}")
        return "\n".join(base)

    def _plan_iteration(self, prompt: str, context: str, iteration: int) -> str:
        tools = self._available_tools_summary()
        system_prompt = (
            "Você é o planejador de um runtime de agentes. "
            "Responda apenas com JSON válido. "
            "Escolha um plano, um motivo para a próxima decisão e, se necessário, uma ferramenta. "
            "Não use heurísticas baseadas em palavras-chave; use o contexto fornecido. "
            f"Ferramentas disponíveis: {json.dumps(tools, ensure_ascii=False)}"
        )
        payload = (
            f"Contexto da iteração {iteration}:\n{context}\n\n"
            "Retorne um JSON com as chaves: "
            "plan (lista de strings), reason (string), should_continue (boolean), "
            "next_action (objeto com tool e arguments ou null)."
        )
        return self.router.ask(prompt=payload, role="planner", system_prompt=system_prompt)

    def _reflect_iteration(
        self,
        prompt: str,
        context: str,
        decision: dict[str, Any],
        tool_results: list[dict[str, Any]],
        iteration: int,
    ) -> dict[str, Any]:
        system_prompt = (
            "Você é o agente de reflexão. "
            "Analise o plano, os resultados das ferramentas e diga se deve continuar. "
            "Responda apenas com JSON válido com as chaves reflection (string) e should_continue (boolean)."
        )
        payload = (
            f"Solicitação original: {prompt}\n\n"
            f"Contexto: {context}\n\n"
            f"Decisão atual: {json.dumps(decision, ensure_ascii=False)}\n\n"
            f"Resultados das ferramentas: {json.dumps(tool_results, ensure_ascii=False)}\n\n"
            f"Iteração: {iteration}"
        )
        raw = self.router.ask(prompt=payload, role="reviewer", system_prompt=system_prompt)
        return self._parse_json(raw, default={"reflection": "", "should_continue": False})

    def _synthesize_answer(self, prompt: str, history: list[dict[str, Any]]) -> str:
        system_prompt = (
            "Você é o sintetizador do runtime. "
            "Resuma a resposta final em português com base no histórico de execução."
        )
        payload = (
            f"Solicitação original: {prompt}\n\n"
            f"Histórico estruturado: {json.dumps(history, ensure_ascii=False)}"
        )
        return self.router.ask(prompt=payload, role="default", system_prompt=system_prompt)

    def _available_tools_summary(self) -> list[dict[str, Any]]:
        try:
            registry = getattr(self.tool_executor, "_registry", None)
            if registry is None:
                return []
            tools = registry.list_tools()
            names = tools.get("result", []) if isinstance(tools, dict) else []
            results: list[dict[str, Any]] = []
            for name in names:
                tool = registry.get(name)
                tool_obj = tool.get("result") if isinstance(tool, dict) else None
                description = getattr(tool_obj, "description", "") or ""
                results.append({"name": name, "description": description})
            return results
        except Exception:
            return []

    def _update_context(
        self,
        context: str,
        decision: dict[str, Any],
        tool_results: list[dict[str, Any]],
        reflection: dict[str, Any],
    ) -> str:
        parts = [context]
        if decision.get("plan"):
            parts.append("Plano atual: " + " | ".join(str(item) for item in decision.get("plan", [])))
        if tool_results:
            parts.append("Resultados: " + json.dumps(tool_results, ensure_ascii=False))
        if reflection.get("reflection"):
            parts.append("Reflexão: " + str(reflection.get("reflection")))
        return "\n".join(parts)

    def _parse_decision(self, raw: str) -> dict[str, Any]:
        parsed = self._parse_json(raw, default={
            "plan": [],
            "reason": "",
            "should_continue": False,
            "next_action": None,
        })
        if not isinstance(parsed, dict):
            return {
                "plan": [],
                "reason": "",
                "should_continue": False,
                "next_action": None,
            }
        plan = parsed.get("plan")
        if not isinstance(plan, list):
            plan = []
        next_action = parsed.get("next_action")
        if not isinstance(next_action, dict):
            next_action = None
        should_continue = bool(parsed.get("should_continue", False))
        return {
            "plan": [str(item) for item in plan],
            "reason": str(parsed.get("reason") or ""),
            "should_continue": should_continue or next_action is not None,
            "next_action": next_action,
        }

    def _parse_json(self, raw: str, *, default: dict[str, Any]) -> Any:
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
            return json.loads(text)
        except Exception:
            return default


class AutonomyLoop(AgentRuntime):
    pass
