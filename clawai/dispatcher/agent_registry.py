from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from clawai.mission.mission import Mission
else:
    Mission = Any  # type: ignore[misc]


class Agent(Protocol):
    def can_execute(self, mission: Mission) -> bool: ...
    def estimate_cost(self, mission: Mission) -> float: ...
    def estimate_tokens(self, mission: Mission) -> int: ...
    def priority(self, mission: Mission) -> int: ...
    def execute(self, mission: Mission) -> dict[str, Any]: ...
    def health(self) -> bool: ...


@dataclass
class AgentEntry:
    name: str
    agent: Agent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: list[AgentEntry] = []

    def register(self, *, name: str, agent: Agent) -> None:
        self._agents.append(AgentEntry(name=name, agent=agent))

    def list_agents(self) -> list[AgentEntry]:
        return list(self._agents)


# ---- Concrete + Stubs ----

class _UnavailableAgent:
    def can_execute(self, mission: Mission) -> bool:
        return False

    def estimate_cost(self, mission: Mission) -> float:
        return float("inf")

    def estimate_tokens(self, mission: Mission) -> int:
        return 1_000_000

    def priority(self, mission: Mission) -> int:
        return 0

    def execute(self, mission: Mission) -> dict[str, Any]:
        raise RuntimeError("Agent indisponível.")

    def health(self) -> bool:
        return False


class PatchAgentAdapter:
    """
    Adapter de PatchAgent para a interface Agent.
    Espera mission.context["project"] preenchido.
    """

    def __init__(self, patch_agent: Any) -> None:
        self._patch_agent = patch_agent

    def can_execute(self, mission: Mission) -> bool:
        return hasattr(mission, "objective") and mission.objective is not None

    def estimate_cost(self, mission: Mission) -> float:
        return 1.0

    def estimate_tokens(self, mission: Mission) -> int:
        return 120_000

    def priority(self, mission: Mission) -> int:
        # patch é prioridade padrão quando disponível
        return 10 + int(getattr(mission, "priority", 0))

    def execute(self, mission: Mission) -> dict[str, Any]:
        project = mission.context.get("project")
        if not project:
            raise RuntimeError("mission.context['project'] não definido para PatchAgentAdapter.")

        # Evita recursão circular: não chama PatchAgent.generate()
        operations = self._patch_agent._execute_patch(project=project, objective=mission.objective)  # type: ignore[attr-defined]
        return {"operations": operations}

    def health(self) -> bool:
        return True
