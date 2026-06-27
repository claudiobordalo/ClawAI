import time
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from threading import Lock
from datetime import datetime, timezone

@dataclass(frozen=True)
class TraceEvent:
    """
    Immutable representation of a single execution event.
    """
    timestamp: datetime
    component: str
    operation: str
    status: str
    duration_ms: float
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

@dataclass(frozen=True)
class ExecutionTrace:
    """
    Immutable snapshot of the execution history.
    """
    events: List[TraceEvent] = field(default_factory=list)

class ExecutionTraceManager:
    """
    Responsible for recording execution events in a thread-safe manner.
    
    This class follows a decoupled approach, storing events that can be 
    exported to various observability systems in the future.
    """
    def __init__(self):
        self._events: List[TraceEvent] = []
        self._pending_operations: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def start(self, component: str, operation: str) -> str:
        """
        Starts tracking an operation.
        Returns a unique token to be used when finishing the operation.
        """
        token = str(uuid.uuid4())
        with self._lock:
            self._pending_operations[token] = {
                "component": component,
                "operation": operation,
                "start_time": time.perf_counter(),
                "start_timestamp": datetime.now(timezone.utc)
            }
        return token

    def finish(self, token: str, status: str = "success", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Finishes tracking an operation and records the event.
        """
        end_time = time.perf_counter()
        end_timestamp = datetime.now(timezone.utc)

        with self._lock:
            op_data = self._pending_operations.pop(token, None)
            if op_data is None:
                # If token is not found, we record a failure event for the missing token
                self._events.append(TraceEvent(
                    timestamp=end_timestamp,
                    component="TracingManager",
                    operation="finish_missing_token",
                    status="error",
                    duration_ms=0.0,
                    metadata={"token": token, "error": "Token not found"}
                ))
                return

            duration_ms = (end_time - op_data["start_time"]) * 1000
            
            event = TraceEvent(
                timestamp=end_timestamp,
                component=op_data["component"],
                operation=op_data["operation"],
                status=status,
                duration_ms=duration_ms,
                metadata=metadata or {}
            )
            self._events.append(event)

    def events(self) -> List[TraceEvent]:
        """
        Returns a copy of the recorded events.
        """
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        """
        Clears all recorded events and pending operations.
        """
        with self._lock:
            self._events.clear()
            self._pending_operations.clear()

    def size(self) -> int:
        """
        Returns the number of recorded events.
        """
        with self._lock:
            return len(self._events)
