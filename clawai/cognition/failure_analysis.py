from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict


class FailureCategory(Enum):
    TOOL_FAILURE = "tool_failure"
    VALIDATION_FAILURE = "validation_failure"
    PLANNING_FAILURE = "planning_failure"
    EXECUTION_FAILURE = "execution_failure"
    TIMEOUT = "timeout"
    DEPENDENCY_FAILURE = "dependency_failure"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "name": self.name}


class AbstractFailureAnalysis(ABC):
    @abstractmethod
    def classify(self, error_message: str, duration: float = 0.0) -> FailureCategory: ...


class FailureAnalysis(AbstractFailureAnalysis):
    _TIMEOUT_KEYWORDS = frozenset({"timeout", "timed out", "time out", "deadline"})
    _TOOL_KEYWORDS = frozenset({"tool", "editor", "apply", "patch", "operation"})
    _VALIDATION_KEYWORDS = frozenset(
        {"validation", "invalid", "malformed", "schema", "type error"}
    )
    _PLANNING_KEYWORDS = frozenset({"plan", "objective", "ambiguous", "incomplete"})
    _DEPENDENCY_KEYWORDS = frozenset(
        {"dependency", "import", "module", "not found", "missing"}
    )

    @classmethod
    def classify(cls, error_message: str, duration: float = 0.0) -> FailureCategory:
        lower = error_message.lower()

        if any(kw in lower for kw in cls._TIMEOUT_KEYWORDS):
            return FailureCategory.TIMEOUT
        if any(kw in lower for kw in cls._TOOL_KEYWORDS):
            return FailureCategory.TOOL_FAILURE
        if any(kw in lower for kw in cls._VALIDATION_KEYWORDS):
            return FailureCategory.VALIDATION_FAILURE
        if any(kw in lower for kw in cls._PLANNING_KEYWORDS):
            return FailureCategory.PLANNING_FAILURE
        if any(kw in lower for kw in cls._DEPENDENCY_KEYWORDS):
            return FailureCategory.DEPENDENCY_FAILURE
        return FailureCategory.EXECUTION_FAILURE


