from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .engineering_record import EngineeringRecord


@dataclass(frozen=True)
class MemoryResult:
    """Immutable result of a memory query."""

    records: Tuple[EngineeringRecord, ...] = field(default_factory=tuple)
    count: int = 0

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError("count must be >= 0")
        if self.count != len(self.records):
            # keep strict consistency for deterministic behavior
            raise ValueError("count must equal len(records)")
