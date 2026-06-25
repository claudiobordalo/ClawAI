from __future__ import annotations

from typing import Any

from clawai.dispatcher.agent_context import AgentContext
from clawai.dispatcher.agent_registry import AgentRegistry
from clawai.dispatcher.routing_policy import RoutingPolicy
from clawai.mission.mission import Mission


class Dispatcher:
    def __init__(
        self,
        *,
        registry: AgentRegistry,
        routing_policy: RoutingPolicy | None = None,
    ) -> None:
        self._registry = registry
        self._routing_policy = routing_policy or RoutingPolicy()

    def dispatch(
        self,
        *,
        mission: Mission,
        resource_manager: Any,
        model_router: Any,
    ) -> dict[str, Any]:
        ctx = AgentContext(
            mission=mission,
            resource_manager=resource_manager,
            model_router=model_router,
            registry=self._registry,
        )

        entries = ctx.registry.list_agents()

        capable = [e for e in entries if e.agent.can_execute(mission)]
        if not capable:
            raise RuntimeError("Nenhum agente disponível para executar esta missão.")

        ranked = self._routing_policy.rank_agents(
            mission=mission,
            resource_manager=ctx.resource_manager,
            candidates=capable,
            model_available=True,
        )

        best = ranked[0].agent_name
        selected = next(e for e in capable if e.name == best)

        result = selected.agent.execute(mission)
        return result
