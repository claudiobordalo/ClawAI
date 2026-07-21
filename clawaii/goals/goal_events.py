from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any, Dict, List


@dataclass(frozen=True)
class GoalEvent:
    timestamp: datetime
    event_type: str
    goal_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


GOAL_CREATED = "goal.created"
GOAL_COMPLETED = "goal.completed"
GOAL_FAILED = "goal.failed"
GOAL_CANCELLED = "goal.cancelled"
GOAL_PROGRESS_UPDATED = "goal.progress_updated"


class GoalEventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, list] = {}
        self._history: List[GoalEvent] = []

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: GoalEvent) -> None:
        self._history.append(event)
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)

    def history(self) -> tuple[GoalEvent, ...]:
        return tuple(self._history)

    def clear(self) -> None:
        self._history.clear()

    def emit(
        self,
        event_type: str,
        goal_id: str,
        **metadata: Any,
    ) -> GoalEvent:
        event = GoalEvent(
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            goal_id=goal_id,
            metadata=metadata,
        )
        self.publish(event)
        return event
