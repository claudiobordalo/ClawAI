from __future__ import annotations

from enum import IntEnum


class GoalPriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    OPTIONAL = 4

    def __str__(self) -> str:
        return self.name.lower()


GOAL_PRIORITY_CRITICAL = GoalPriority.CRITICAL
GOAL_PRIORITY_HIGH = GoalPriority.HIGH
GOAL_PRIORITY_MEDIUM = GoalPriority.MEDIUM
GOAL_PRIORITY_LOW = GoalPriority.LOW
GOAL_PRIORITY_OPTIONAL = GoalPriority.OPTIONAL
