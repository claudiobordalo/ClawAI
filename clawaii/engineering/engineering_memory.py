from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import List, Tuple

from .engineering_record import EngineeringRecord
from .memory_query import MemoryQuery
from .memory_result import MemoryResult


from .abstract_memory import AbstractMemory


@dataclass
class EngineeringMemory(AbstractMemory):
    """In-memory, deterministic engineering memory.

    - Stores EngineeringRecord instances in RAM only.
    - Preserves insertion order.
    - Query results preserve insertion order after filtering.
    - Thread-safe via a reentrant lock for simple concurrent use.
    - API prepared for future persistence backends by keeping a narrow interface.
    """

    def __init__(self) -> None:
        self._records: List[EngineeringRecord] = []
        self._lock = RLock()

    def add(self, record: EngineeringRecord) -> None:
        with self._lock:
            self._records.append(record)

    def query(self, query: MemoryQuery) -> MemoryResult:
        with self._lock:
            out: List[EngineeringRecord] = []
            for r in self._records:
                if query.objective is not None and r.objective != query.objective:
                    continue
                if query.target_query is not None and r.target_query != query.target_query:
                    continue
                if query.diagnosis is not None and r.diagnosis != query.diagnosis:
                    continue
                if query.success_only is True and not r.success:
                    continue
                # Note: success_only False or None does not filter to keep semantics simple and deterministic
                out.append(r)
            return MemoryResult(records=tuple(out), count=len(out))

    def last(self, n: int) -> Tuple[EngineeringRecord, ...]:
        if n < 0:
            raise ValueError("n must be >= 0")
        with self._lock:
            if n == 0:
                return tuple()
            return tuple(self._records[-n:])

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._records)
