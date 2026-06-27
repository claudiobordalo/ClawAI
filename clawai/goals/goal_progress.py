from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from .goal import Goal


@dataclass(frozen=True)
class GoalProgress:
    goal: Optional[Goal]
    completion: float
    completed_items: tuple[str, ...] = tuple()
    remaining_items: tuple[str, ...] = tuple()
    summary: str = ""

    def __post_init__(self) -> None:
        self._validate_completion()

    def _validate_completion(self) -> None:
        if math.isnan(self.completion):
            raise ValueError("completion must not be NaN")
        if math.isinf(self.completion):
            raise ValueError("completion must not be infinite")
        if self.completion < 0.0:
            raise ValueError(f"completion must be >= 0.0, got {self.completion}")
        if self.completion > 100.0:
            raise ValueError(f"completion must be <= 100.0, got {self.completion}")

    @property
    def is_completed(self) -> bool:
        return self.completion >= 100.0

    @property
    def remaining_percentage(self) -> float:
        return max(0.0, 100.0 - self.completion)

    @property
    def completed_percentage(self) -> float:
        return self.completion
