from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .agent_context import AgentContext
from .agent_loop import AgentLoop
from .execution_session import ExecutionSession


class AbstractAutonomousAgent(ABC):
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
    def context(self) -> AgentContext: ...

    @property
    @abstractmethod
    def loop(self) -> Optional[AgentLoop]: ...
