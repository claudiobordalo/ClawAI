from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from clawai.mission.mission_state import MissionStatus


@dataclass(slots=True)
class Mission:
    id: str
    objective: str
    priority: int = 0

    status: MissionStatus = MissionStatus.created

    steps: list[Any] = field(default_factory=list)
    current_step: int = 0

    history: list[dict[str, Any]] = field(default_factory=list)

    # contexto e resultado do mission
    context: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
