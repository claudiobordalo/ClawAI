from __future__ import annotations

from typing import Tuple

from .goal import Goal
from .goal_backlog import GoalBacklog
from .planning_context import PlanningContext
from .planning_strategy import PlanningStrategy


from .abstract_planner import AbstractPlanner


class GoalPlanner(AbstractPlanner):
    def __init__(self, strategy: str | PlanningStrategy = "rule_based") -> None:
        if isinstance(strategy, PlanningStrategy):
            self._strategy = strategy
        else:
            from .planner_factory import PlannerFactory

            self._strategy = PlannerFactory.create(strategy)

    def plan(
        self, objective: str, context: PlanningContext | None = None
    ) -> GoalBacklog:
        ctx = context or PlanningContext(objective=objective)
        return self._strategy.plan(ctx)

    def plan_to_goals(self, objective: str) -> Tuple[Goal, ...]:
        backlog = self.plan(objective)
        return backlog.goals
