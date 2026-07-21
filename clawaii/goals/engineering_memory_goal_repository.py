from __future__ import annotations

from typing import Dict, Optional, Tuple

from clawai.engineering import AbstractMemory

from .goal import Goal
from .goal_repository import GoalRepository


class EngineeringMemoryGoalRepository(GoalRepository):
    def __init__(self, memory: AbstractMemory) -> None:
        self._engineering_memory = memory
        self._store: Dict[str, Goal] = {}

    def load(self, goal_id: str) -> Optional[Goal]:
        return self._store.get(goal_id)

    def save(self, goal: Goal) -> None:
        self._store[goal.id] = goal

    def update(self, goal: Goal) -> None:
        if goal.id not in self._store:
            raise KeyError(f"Goal not found: {goal.id}")
        self._store[goal.id] = goal

    def delete(self, goal_id: str) -> None:
        self._store.pop(goal_id, None)

    def list(self) -> Tuple[Goal, ...]:
        return tuple(
            sorted(
                self._store.values(),
                key=lambda g: (
                    g.priority.value if hasattr(g.priority, "value") else g.priority,
                    g.title.lower(),
                    g.id,
                ),
            )
        )
