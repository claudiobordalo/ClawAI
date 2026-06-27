from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .execution_session import ExecutionSession
from .metrics import AgentMetrics


class AbstractAgentLoop(ABC):
    @staticmethod
    def create_default(context) -> AbstractAgentLoop:
        from .agent_loop import AgentLoop
        return AgentLoop(context)

    @abstractmethod
    def run(self, objective: str) -> ExecutionSession: ...

    @abstractmethod
    def cancel(self) -> None: ...

    @abstractmethod
    def pause(self) -> None: ...

    @abstractmethod
    def resume(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @property
    @abstractmethod
    def is_cancelled(self) -> bool: ...

    @property
    @abstractmethod
    def metrics(self) -> AgentMetrics: ...
