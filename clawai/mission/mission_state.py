from __future__ import annotations

from enum import Enum


class MissionStatus(str, Enum):
    created = "created"
    planning = "planning"
    running = "running"
    waiting = "waiting"
    reviewing = "reviewing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class MissionStepStatus(str, Enum):
    created = "created"
    planning = "planning"
    running = "running"
    waiting = "waiting"
    reviewing = "reviewing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
