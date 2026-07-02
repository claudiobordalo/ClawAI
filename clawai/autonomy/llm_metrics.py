from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LLMCallMetrics:
    max_calls: int = 10
    calls: list[dict[str, Any]] = field(default_factory=list)

    @property
    def should_abort(self) -> bool:
        return len(self.calls) > self.max_calls

    def record(self, role: str, *, metadata: dict[str, Any] | None = None) -> None:
        self.calls.append({"role": role, "metadata": metadata or {}})

    def snapshot(self) -> dict[str, Any]:
        return {
            "max_calls": self.max_calls,
            "total_calls": len(self.calls),
            "should_abort": self.should_abort,
            "calls": list(self.calls),
        }
