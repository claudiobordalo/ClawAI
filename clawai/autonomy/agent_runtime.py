from __future__ import annotations

import json
import re
from typing import Any, Protocol

from clawai.tools.filesystem_tool import FilesystemTool
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

    def run(self, prompt: str, *, file: str | None = None) -> dict[str, Any]:
        history: list[dict[str, Any]] = []
        context = self._build_context(prompt, file)

        for iteration in range(1, self.max_iterations + 1):
            decision = self._plan_iteration(prompt, context, iteration)
            parsed = self._parse_decision(decision)
            tool_calls: list[dict[str, Any]] = []
            tool_results: list[dict[str, Any]] = []

            next_action = parsed.get("next_action") or {}
            tool_name = next_action.get("tool")
            arguments = next_action.get("arguments") or {}

            if tool_name and self.tool_executor is not None:
                execution = self.tool_executor.execute(tool_name=tool_name, arguments=arguments)
                tool_calls.append({"tool": tool_name, "arguments": arguments})
                tool_results.append({"tool": tool_name, "result": execution})

            reflection = self._reflect_iteration(prompt, context, parsed, tool_results, iteration)
            history.append(
                {
                    "iteration": iteration,
                    "plan": parsed.get("plan", []),
                    "tools_used": tool_calls,
                    "tool_results": tool_results,
                    "next_decision_reason": parsed.get("reason") or "",
                    "reflection": reflection.get("reflection") or "",
                }
            )

            context = self._update_context(context, parsed, tool_results, reflection)

            if not parsed.get("should_continue", False):
                break

        answer = self._synthesize_answer(prompt, history)
        return {
            "answer": answer,
            "history": history,
            "used_tools": any(item["tools_used"] for item in history),
            "iterations": len(history),
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
