from __future__ import annotations

from enum import IntEnum


class GoalComplexity(IntEnum):
    XS = 0
    S = 1
    M = 2
    L = 3
    XL = 4

    def __str__(self) -> str:
        return self.name
