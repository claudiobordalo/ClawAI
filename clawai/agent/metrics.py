from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AgentMetrics:
    goals_completed: int = 0
    goals_failed: int = 0
    goals_skipped: int = 0
    goals_retried: int = 0
    replan_count: int = 0
    total_duration: float = 0.0
    execution_durations: List[float] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)

    # Cognitive metrics
    cognitive_latency: float = 0.0
    reasoning_latency: float = 0.0
    review_latency: float = 0.0
    decision_latency: float = 0.0
    reflection_latency: float = 0.0
    cognitive_latencies: List[float] = field(default_factory=list)
    confidence_distribution: Dict[str, int] = field(default_factory=dict)

    @property
    def average_duration(self) -> float:
        if not self.execution_durations:
            return 0.0
        return sum(self.execution_durations) / len(self.execution_durations)

    @property
    def total_goals(self) -> int:
        return self.goals_completed + self.goals_failed + self.goals_skipped

    @property
    def average_cognitive_latency(self) -> float:
        if not self.cognitive_latencies:
            return 0.0
        return sum(self.cognitive_latencies) / len(self.cognitive_latencies)
