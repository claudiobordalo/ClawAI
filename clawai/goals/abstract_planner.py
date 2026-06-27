from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from .goal import Goal
from .goal_backlog import GoalBacklog
from .planning_context import PlanningContext


class AbstractPlanner(ABC):
    @abstractmethod
    def plan(
        self, objective: str, context: PlanningContext | None = None
    ) -> GoalBacklog: ...

    @abstractmethod
    def plan_to_goals(self, objective: str) -> Tuple[Goal, ...]: ...
