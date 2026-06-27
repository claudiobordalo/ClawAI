from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from .goal import Goal


@dataclass(frozen=True)
class GoalBacklog:
    goals: Tuple[Goal, ...] = tuple()
    created_at: Optional[datetime] = None
    summary: str = ""

    def __post_init__(self) -> None:
        if self.created_at is not None:
            object.__setattr__(self, "created_at", self.created_at.replace(microsecond=0))
