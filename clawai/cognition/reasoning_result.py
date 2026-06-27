from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .failure_analysis import FailureCategory
from .review_result import ReviewResult


@dataclass
class ReasoningResult:
    assessment: ReviewResult
    confidence: float = 1.0
    reason: str = ""
    recommendation: str = ""
    next_action: str = "continue"
    should_retry: bool = False
    requires_replan: bool = False
    requires_cancel: bool = False
    review_result: str = ""
    failure_category: Optional[str] = None
    reflection_id: Optional[str] = None
    review_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
