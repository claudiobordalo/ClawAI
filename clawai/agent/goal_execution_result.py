from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from clawai.goals import Goal


@dataclass
class GoalExecutionResult:
    goal: Goal
    success: bool
    output: str = ""
    duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_replan: bool = False
    attempts: int = 1
    review_result: str = ""
    failure_category: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""
    reflection: str = ""
    decision: str = ""
    next_action: str = ""
