from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .execution_state import ExecutionState
from .goal_execution_result import GoalExecutionResult


@dataclass
class ExecutionSession:
    id: str
    objective: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    state: ExecutionState = ExecutionState.PENDING
    current_goal: Optional[str] = None
    completed_goals: List[str] = field(default_factory=list)
    failed_goals: List[str] = field(default_factory=list)
    cancelled: bool = False
    results: List[GoalExecutionResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
