from __future__ import annotations

from enum import Enum


class ExecutionState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value
