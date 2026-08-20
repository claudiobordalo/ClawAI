from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .goal import Goal
from .goal_backlog import GoalBacklog


@dataclass
class PlanningContext:
    objective: str
    engineering_memory: Any = None
    repository_state: Sequence[Goal] = field(default_factory=list)
    active_branch: str = ""
    available_tools: List[str] = field(default_factory=list)
    previous_attempts: int = 0
    current_backlog: Optional[GoalBacklog] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
