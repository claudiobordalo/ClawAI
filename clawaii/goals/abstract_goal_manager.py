from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .goal import Goal
from .goal_backlog import GoalBacklog
from .goal_priority import GoalPriority
from .goal_progress import GoalProgress


class AbstractGoalManager(ABC):
    @abstractmethod
    def create_backlog(self) -> GoalBacklog: ...

    @abstractmethod
    def next_goal(self) -> Optional[Goal]: ...

    @abstractmethod
    def add_goal(self, goal: Goal) -> Goal: ...

    @abstractmethod
    def complete_goal(self, goal_id: str) -> Optional[Goal]: ...

    @abstractmethod
    def fail_goal(self, goal_id: str) -> Optional[Goal]: ...

    @abstractmethod
    def reprioritize(
        self, goal_id: str, new_priority: GoalPriority | int
    ) -> Optional[Goal]: ...

    @abstractmethod
    def find_goal(self, goal_id: str) -> Optional[Goal]: ...

    @abstractmethod
    def remove_goal(self, goal_id: str) -> bool: ...

    @abstractmethod
    def update_progress(
        self, goal_id: str, completion: float
    ) -> Optional[GoalProgress]: ...

    @abstractmethod
    def progress(self) -> GoalProgress: ...
