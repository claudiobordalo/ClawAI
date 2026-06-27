from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from clawai.planning.planner import ExecutionPlan, Planner
from clawai.providers.base.provider import BaseProvider
from clawai.providers.base.response import ProviderResponse


@dataclass(frozen=True)
class PlanningResult:
    success: bool
    plan: ExecutionPlan | None = None
    error: str | None = None


class LLMPlanner:
    """
    Responsável por gerar planos estruturados a partir de um objetivo usando um Provider.

    Regras:
    - Não executa ferramentas.
    - Não acessa AgentLoop, AgentEngine, ToolExecutor, Workspace.
    - Não altera o Planner existente (que permanece responsável por operações determinísticas).
    - Não lança exceções para o chamador: sempre retorna PlanningResult.
    """

    def __init__(
        self,
        *,
        prompt_engine: Any,  # Injetado para futura personalização do prompt (não utilizado nesta sprint)
        provider: BaseProvider,
    ) -> None:
        if provider is None:
            raise ValueError("LLMPlanner: 'provider' é obrigatório.")
        # prompt_engine é aceito por injeção, mas não é obrigatório usá-lo nesta sprint
        self._prompt_engine = prompt_engine
        self._provider = provider
        self._planner = Planner()

    def create_plan(self, objective: str) -> PlanningResult:
        """
        Cria um plano usando o Provider, interpretando um JSON no formato esperado:
        {
            "objective": "...",
            "steps": ["Primeiro passo", "Segundo passo", ...]
        }
        """
        try:
            if not objective or not isinstance(objective, str) or not objective.strip():
                return PlanningResult(success=False, plan=None, error="LLMPlanner: 'objective' não pode ser vazio.")

            prompt = self._build_planning_prompt(objective.strip())
            response: ProviderResponse = self._provider.generate(prompt=prompt, system_prompt=None)

            content = response.content if response is not None else ""
            if not content or not isinstance(content, str) or not content.strip():
                return PlanningResult(success=False, plan=None, error="LLMPlanner: resposta vazia do provider.")

            # Espera JSON puro conforme contrato desta sprint
            try:
                data = json.loads(content.strip())
            except json.JSONDecodeError:
                return PlanningResult(success=False, plan=None, error="LLMPlanner: JSON inválido retornado pelo provider.")

            if not isinstance(data, dict):
                return PlanningResult(success=False, plan=None, error="LLMPlanner: JSON deve ser um objeto.")

            obj = data.get("objective")
            steps = data.get("steps")

            if not isinstance(obj, str) or not obj.strip():
                return PlanningResult(success=False, plan=None, error="LLMPlanner: campo 'objective' inválido no JSON.")

            if not isinstance(steps, list) or len(steps) == 0:
                return PlanningResult(success=False, plan=None, error="LLMPlanner: campo 'steps' deve ser uma lista não vazia de strings.")

            normalized_steps: list[str] = []
            for idx, s in enumerate(steps):
                if not isinstance(s, str):
                    return PlanningResult(success=False, plan=None, error=f"LLMPlanner: passo #{idx+1} deve ser string.")
                s_norm = s.strip()
                if not s_norm:
                    return PlanningResult(success=False, plan=None, error=f"LLMPlanner: passo #{idx+1} não pode ser vazio.")
                normalized_steps.append(s_norm)

            # Construir o ExecutionPlan reutilizando o Planner determinístico
            plan = self._planner.create_plan(obj.strip(), steps=tuple(normalized_steps))
            return PlanningResult(success=True, plan=plan, error=None)
        except Exception as ex:  # Nunca propaga exceções
            return PlanningResult(success=False, plan=None, error=f"LLMPlanner: erro inesperado: {ex}")

    def _build_planning_prompt(self, objective: str) -> str:
        """Monta um prompt determinístico para solicitação de plano ao Provider."""
        lines = [
            "Você é um planejador de tarefas.",
            "Gere um plano objetivo e claro a partir do objetivo fornecido.",
            "Responda APENAS com JSON válido neste formato:",
            '{"objective": "...", "steps": ["Primeiro passo", "Segundo passo"]}',
            "",
            f"Objective: {objective}",
        ]
        return "\n".join(lines)
