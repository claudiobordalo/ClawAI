from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

from .goal_complexity import GoalComplexity
from .goal_priority import GoalPriority
from .goal_status import GoalStatus, normalize_status as _norm_status

_VALID_COMPLEXITIES = frozenset({"XS", "S", "M", "L", "XL"})


@dataclass(frozen=True)
class Goal:
    id: str
    title: str
    description: str
    success_criteria: str
    priority: GoalPriority | int = GoalPriority.MEDIUM
    status: GoalStatus | str = GoalStatus.TODO
    depends_on: Tuple[str, ...] = tuple()
    estimated_complexity: str = "M"
    tags: Tuple[str, ...] = tuple()

    def __post_init__(self) -> None:
        norm_status = (
            _norm_status(self.status)
            if not isinstance(self.status, GoalStatus)
            else self.status
        )
        norm_priority = (
            self._normalize_priority(self.priority)
            if not isinstance(self.priority, GoalPriority)
            else self.priority
        )
        norm_complexity = self._normalize_complexity(self.estimated_complexity)
        object.__setattr__(self, "status", norm_status)
        object.__setattr__(self, "priority", norm_priority)
        object.__setattr__(self, "estimated_complexity", norm_complexity)
        self._validate_state()

    def _validate_state(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Goal id must not be empty")
        if not self.title or not self.title.strip():
            raise ValueError("Goal title must not be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Goal description must not be empty")
        if not self.success_criteria or not self.success_criteria.strip():
            raise ValueError("Goal success_criteria must not be empty")
        if not isinstance(self.status, GoalStatus):
            raise ValueError(f"Invalid status type: {type(self.status).__name__}")
        if not isinstance(self.priority, GoalPriority):
            raise ValueError(f"Invalid priority type: {type(self.priority).__name__}")
        if (
            not isinstance(self.estimated_complexity, str)
            or self.estimated_complexity not in _VALID_COMPLEXITIES
        ):
            raise ValueError(
                f"Invalid estimated_complexity: {self.estimated_complexity!r}. "
                f"Must be one of {sorted(_VALID_COMPLEXITIES)}"
            )

    @staticmethod
    def _normalize_priority(raw: Any) -> GoalPriority:
        try:
            if isinstance(raw, str) and raw.isdigit():
                return GoalPriority(int(raw))
            if isinstance(raw, bool):
                raise TypeError
            return GoalPriority(int(raw))
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid priority: {raw!r}. " f"Must be convertible to GoalPriority"
            )

    @staticmethod
    def _normalize_complexity(raw: str) -> str:
        upper = raw.strip().upper()
        if upper in _VALID_COMPLEXITIES:
            return upper
        try:
            return GoalComplexity(int(raw)).name
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid estimated_complexity: {raw!r}. "
                f"Must be one of {sorted(_VALID_COMPLEXITIES)}"
            )


# Backward-compatible aliases
GOAL_STATUS_PENDING = GoalStatus.TODO
GOAL_STATUS_RUNNING = GoalStatus.IN_PROGRESS
GOAL_STATUS_COMPLETED = GoalStatus.DONE
GOAL_STATUS_FAILED = GoalStatus.BLOCKED
GOAL_STATUS_CANCELLED = GoalStatus.CANCELLED
ALLOWED_STATUSES = frozenset(GoalStatus)
