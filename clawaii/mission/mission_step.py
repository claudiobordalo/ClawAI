from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MissionStep:
    description: str
    status: str = "created"
    estimated_cost: float | None = None
    estimated_tokens: int | None = None
    dependencies: list[str] = field(default_factory=list)

    # extensível para regras futuras
    meta: dict[str, Any] = field(default_factory=dict)
