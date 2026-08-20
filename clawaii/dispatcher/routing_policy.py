from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clawai.dispatcher.agent_registry import AgentEntry
from clawai.mission.mission import Mission
from clawai.resources.manager import ResourceManager


@dataclass(slots=True)
class RoutingDecision:
    agent_name: str
    score: float
    reason: str
    diagnostics: dict[str, Any]


class RoutingPolicy:
    """
    Seleciona o melhor agente com base em:
    - tipo da missão (heurística por objetivo)
    - complexidade (heurística por tamanho do objetivo)
    - recursos disponíveis (ResourceManager.decide)
    - prioridade da missão
    - modelo disponível (heurística: sempre assume disponível para PatchAgent stubs)
    """

    def rank_agents(
        self,
        *,
        mission: Mission,
        resource_manager: ResourceManager,
        candidates: list[AgentEntry],
        model_available: bool = True,
    ) -> list[RoutingDecision]:
        decision = resource_manager.decide(
            objective=mission.objective,
            expected_files=0,
        )

        complexity = min(5, max(0, len(mission.objective) // 800))
        mission_priority = getattr(mission, "priority", 0)

        ranked: list[RoutingDecision] = []

        for entry in candidates:
            agent = entry.agent
            agent_priority = int(getattr(agent, "priority")(mission))

            base = agent_priority + mission_priority
            complexity_bonus = (5 - complexity) * 0.2
            model_bonus = 0.3 if model_available else -1.0

            resource_penalty = 0.0
            if decision.action == "reduce":
                # se recursos estão apertados, penaliza agentes "pesados" por custo estimado
                cost = float(agent.estimate_cost(mission))
                if cost > 2.0:
                    resource_penalty = (cost - 2.0) * 0.5
            elif decision.action == "defer":
                resource_penalty = 10.0

            # can_execute já garante compatibilidade
            score = base + complexity_bonus + model_bonus - resource_penalty

            ranked.append(
                RoutingDecision(
                    agent_name=entry.name,
                    score=float(score),
                    reason=decision.action,
                    diagnostics={
                        "mission_priority": mission_priority,
                        "agent_priority": agent_priority,
                        "complexity": complexity,
                        "resource_action": decision.action,
                        "step_estimated_tokens": agent.estimate_tokens(mission),
                    },
                )
            )

        ranked.sort(key=lambda d: d.score, reverse=True)
        return ranked
