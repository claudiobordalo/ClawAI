from __future__ import annotations

from enum import Enum


class GoalStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value


GOAL_STATUS_TODO = GoalStatus.TODO
GOAL_STATUS_IN_PROGRESS = GoalStatus.IN_PROGRESS
GOAL_STATUS_BLOCKED = GoalStatus.BLOCKED
GOAL_STATUS_DONE = GoalStatus.DONE
GOAL_STATUS_CANCELLED = GoalStatus.CANCELLED

_LEGACY_STATUS_MAP: dict[str, GoalStatus] = {
    "pending": GoalStatus.TODO,
    "running": GoalStatus.IN_PROGRESS,
    "completed": GoalStatus.DONE,
    "failed": GoalStatus.BLOCKED,
    "cancelled": GoalStatus.CANCELLED,
}


def normalize_status(raw: str | GoalStatus) -> GoalStatus:
    if isinstance(raw, GoalStatus):
        return raw
    mapped = _LEGACY_STATUS_MAP.get(raw)
    if mapped is not None:
        return mapped
    try:
        return GoalStatus(raw)
    except ValueError:
        pass
    try:
        return GoalStatus[raw.upper()]
    except KeyError:
        raise ValueError(
            f"Invalid status: {raw!r}. " f"Allowed: {[s.value for s in GoalStatus]}"
        )
