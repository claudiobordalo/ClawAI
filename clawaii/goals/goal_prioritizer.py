from __future__ import annotations

from typing import Dict, Tuple

from .goal import Goal
from .goal_dependency_graph import GoalDependencyGraph

_COMPLEXITY_ORDER: Dict[str, int] = {
    "XS": 0,
    "S": 1,
    "M": 2,
    "L": 3,
    "XL": 4,
}


def _complexity_rank(c: str) -> int:
    return _COMPLEXITY_ORDER.get(c.upper(), 2)


class GoalPrioritizer:
    def __init__(self, graph: GoalDependencyGraph) -> None:
        self._graph = graph

    def prioritize(self, goals: Tuple[Goal, ...]) -> Tuple[Goal, ...]:
        scored: list[tuple[int, int, int, int, int, Goal]] = []

        for idx, g in enumerate(goals):
            priority_val = int(g.priority)
            depth = self._graph.dependency_depth(g.id)
            complexity = _complexity_rank(g.estimated_complexity)
            risk = complexity
            impact = len(self._graph.get_dependents(g.id))

            scored.append(
                (
                    priority_val,
                    -depth,
                    -impact,
                    -risk,
                    idx,
                    g,
                )
            )

        scored.sort(key=lambda x: (x[0], x[1], x[2], x[3], x[4]))
        return tuple(s[5] for s in scored)
