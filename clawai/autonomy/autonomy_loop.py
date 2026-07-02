from __future__ import annotations

import re
from typing import Any


class AutonomyLoop:
    def __init__(self, *, router: Any | None = None, executor: Any | None = None) -> None:
        self.router = router
        self.executor = executor

    def run(self, prompt: str) -> dict[str, Any]:
        if self.router is None:
            return {
                "answer": prompt,
                "used_tools": False,
                "tool_calls": [],
                "steps": [],
            }

        plan_text = self._ask_planner(prompt)
        steps = self._parse_steps(plan_text)
        decision = self._ask_decision(prompt, plan_text)

        tool_calls: list[dict[str, Any]] = []
        used_tools = False

        if decision.lower().strip() == "continue" and self.executor is not None:
            for step in steps:
                if not self._looks_like_tool_use(step):
                    continue

                action = self._infer_tool_action(step)
                if action is None:
                    continue

                result = self.executor.execute(tool_name="filesystem", arguments={"action": action, "path": "."})
                tool_calls.append({"step": step, "result": result})
                used_tools = True
                break

        synthesis = self._ask_synthesizer(prompt, plan_text, tool_calls, decision)
        return {
            "answer": synthesis,
            "used_tools": used_tools,
            "tool_calls": tool_calls,
            "steps": steps,
        }

    def _ask_planner(self, prompt: str) -> str:
        return self.router.ask(
            prompt=prompt,
            role="planner",
            system_prompt="Planeje uma pequena sequência de ações para responder melhor à solicitação.",
        )

    def _ask_decision(self, prompt: str, plan_text: str) -> str:
        return self.router.ask(
            prompt=f"Solicitação:\n{prompt}\n\nPlano:\n{plan_text}",
            role="planner",
            system_prompt="Responda apenas com continue ou stop para indicar se o fluxo deve prosseguir para uso de ferramentas.",
        )

    def _ask_synthesizer(self, prompt: str, plan_text: str, tool_calls: list[dict[str, Any]], decision: str) -> str:
        context = f"Solicitação:\n{prompt}\n\nPlano:\n{plan_text}\n\nDecisão:\n{decision}"
        if tool_calls:
            context += f"\n\nFerramentas usadas:\n{tool_calls}"
        return self.router.ask(
            prompt=context,
            role="default",
            system_prompt="Resuma a resposta final em português, incorporando os resultados das ferramentas quando houver.",
        )

    def _parse_steps(self, plan_text: str) -> list[str]:
        steps = [line.strip() for line in plan_text.splitlines() if line.strip()]
        return [step for step in steps if re.match(r"^\d+\.", step)] or steps

    def _looks_like_tool_use(self, step: str) -> bool:
        lowered = step.lower()
        return any(token in lowered for token in ("inspecione", "analise", "liste", "revele", "procure", "explore", "estrutura", "arquivo"))

    def _infer_tool_action(self, step: str) -> str | None:
        lowered = step.lower()
        if "arquivo" in lowered or "estrutura" in lowered or "projeto" in lowered:
            return "list_dir"
        if "conteúdo" in lowered or "ler" in lowered or "read" in lowered:
            return "read_file"
        return None
