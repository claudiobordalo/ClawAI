from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from clawai.engineering import AbstractMemory

from .abstract_reflection_engine import AbstractReflectionEngine
from .failure_analysis import FailureCategory
from .review_result import ReviewResult


@dataclass
class ReflectionEntry:
    goal_id: str
    goal_title: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = False
    review_result: Optional[ReviewResult] = None
    failure_category: Optional[FailureCategory] = None
    what_worked: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "goal_title": self.goal_title,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "review_result": self.review_result.value if self.review_result else None,
            "failure_category": self.failure_category.value if self.failure_category else None,
            "what_worked": list(self.what_worked),
            "what_failed": list(self.what_failed),
            "risks": list(self.risks),
            "opportunities": list(self.opportunities),
            "decisions": list(self.decisions),
            "duration": self.duration,
            "metadata": dict(self.metadata),
        }


class ReflectionEngine(AbstractReflectionEngine):
    def __init__(self, memory: Optional[AbstractMemory] = None) -> None:
        self._memory = memory
        self._entries: List[ReflectionEntry] = []

    def record(self, entry: ReflectionEntry) -> None:
        self._entries.append(entry)
        if self._memory:
            try:
                from clawai.engineering import EngineeringRecord

                record = EngineeringRecord(
                    timestamp=entry.timestamp,
                    objective=entry.goal_title,
                    target_query=entry.goal_id,
                    instructions="reflection",
                    diagnosis=(
                        "; ".join(entry.what_failed) if entry.what_failed else "success"
                    ),
                    strategy="reflection",
                    summary=entry.goal_title,
                    success=entry.success,
                    modified_files=(),
                    failed_tests=tuple(entry.what_failed),
                    duration=entry.duration,
                )
                self._memory.add(record)
            except Exception:
                pass

    def entries(self) -> tuple[ReflectionEntry, ...]:
        return tuple(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    @property
    def count(self) -> int:
        return len(self._entries)

    def recent_failures(self, limit: int = 5) -> tuple[ReflectionEntry, ...]:
        return tuple(e for e in self._entries if not e.success)[-limit:]

    def repeated_errors(self, min_count: int = 2) -> Dict[str, int]:
        freq: Dict[str, int] = {}
        for e in self._entries:
            for wf in e.what_failed:
                key = wf.lower().strip()
                freq[key] = freq.get(key, 0) + 1
        return {k: v for k, v in freq.items() if v >= min_count}
