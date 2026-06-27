from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from .engineering_record import EngineeringRecord
from .memory_query import MemoryQuery
from .memory_result import MemoryResult


class AbstractMemory(ABC):
    @abstractmethod
    def add(self, record: EngineeringRecord) -> None: ...

    @abstractmethod
    def query(self, query: MemoryQuery) -> MemoryResult: ...

    @abstractmethod
    def last(self, n: int) -> Tuple[EngineeringRecord, ...]: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def size(self) -> int: ...
