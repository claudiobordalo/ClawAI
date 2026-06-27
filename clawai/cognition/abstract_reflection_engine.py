from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Tuple


class AbstractReflectionEngine(ABC):
    @abstractmethod
    def record(self, entry: "ReflectionEntry") -> None: ...  # noqa: F821 — forward reference

    @abstractmethod
    def entries(self) -> Tuple["ReflectionEntry", ...]: ...  # noqa: F821

    @abstractmethod
    def clear(self) -> None: ...

    @property
    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def recent_failures(self, limit: int = 5) -> Tuple["ReflectionEntry", ...]: ...  # noqa: F821

    @abstractmethod
    def repeated_errors(self, min_count: int = 2) -> Dict[str, int]: ...
