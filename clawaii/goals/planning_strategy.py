from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from .goal_backlog import GoalBacklog
from .goal_decomposer import GoalDecomposer
from .goal_dependency_graph import GoalDependencyGraph
from .goal_prioritizer import GoalPrioritizer
from .planning_context import PlanningContext


class PlanningStrategy(ABC):
    @abstractmethod
    def plan(self, context: PlanningContext) -> GoalBacklog: ...


class RuleBasedPlanningStrategy(PlanningStrategy):
    def __init__(
        self,
        decomposer: GoalDecomposer,
    ) -> None:
        self._decomposer = decomposer

    def plan(self, context: PlanningContext) -> GoalBacklog:
        goals = self._decomposer.decompose(context.objective)
        if not goals:
            now = datetime.now(timezone.utc)
            return GoalBacklog(goals=(), created_at=now, summary="No goals to plan")

        graph = GoalDependencyGraph(goals)
        if graph.has_cycle():
            cycle = graph.find_cycle()
            now = datetime.now(timezone.utc)
            return GoalBacklog(
                goals=(),
                created_at=now,
                summary=f"Planning failed: cycle detected among goals: {' -> '.join(cycle)}",
            )

        prioritizer = GoalPrioritizer(graph)
        ordered = prioritizer.prioritize(goals)

        now = datetime.now(timezone.utc)
        return GoalBacklog(
            goals=ordered,
            created_at=now,
            summary=f"Planned {len(ordered)} goals",
        )
