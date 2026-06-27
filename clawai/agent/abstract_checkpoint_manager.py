from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from clawai.goals import GoalBacklog

from .execution_session import ExecutionSession


class AbstractCheckpointManager(ABC):
    @abstractmethod
    def save(
        self,
        session: ExecutionSession,
        backlog: Optional[GoalBacklog] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str: ...

    @abstractmethod
    def load(self, session_id: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def delete(self, session_id: str) -> bool: ...
