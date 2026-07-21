from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clawai.mission.mission import Mission
from clawai.resources.manager import ResourceManager
from clawai.ai.router import ModelRouter
from clawai.dispatcher.agent_registry import AgentRegistry


@dataclass(slots=True)
class AgentContext:
    mission: Mission
    resource_manager: ResourceManager
    model_router: ModelRouter
    registry: AgentRegistry

    # extensível para futuras políticas/telemetria
    extra: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.extra is None:
            self.extra = {}
