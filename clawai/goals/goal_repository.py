from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from .goal import Goal


class GoalRepository(ABC):
    @abstractmethod
    def load(self, goal_id: str) -> Optional[Goal]: ...

    @abstractmethod
    def save(self, goal: Goal) -> None: ...

    @abstractmethod
    def update(self, goal: Goal) -> None: ...

    @abstractmethod
    def delete(self, goal_id: str) -> None: ...

    @abstractmethod
    def list(self) -> Tuple[Goal, ...]: ...
