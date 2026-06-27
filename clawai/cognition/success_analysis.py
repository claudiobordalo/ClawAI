from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SuccessAnalysis:
    duration: float = 0.0
    quality_score: float = 1.0
    tests_passed: int = 0
    tests_failed: int = 0
    files_modified: int = 0
    impact_score: float = 0.5
    tokens_used: int = 0
    cost_estimate: float = 0.0
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration": self.duration,
            "quality_score": self.quality_score,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "files_modified": self.files_modified,
            "impact_score": self.impact_score,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "summary": self.summary,
            "recommendations": list(self.recommendations),
        }
