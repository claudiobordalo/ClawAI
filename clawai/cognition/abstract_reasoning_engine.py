from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .abstract_reflection_engine import AbstractReflectionEngine
from .cognitive_result import CognitiveResult
from .execution_assessment import ExecutionAssessment
from .reasoning_result import ReasoningResult


class AbstractReasoningEngine(ABC):
    @abstractmethod
    def analyze(
        self,
        *,
        goal_id: str,
        goal_title: str,
        success: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        output: str = "",
        duration: float = 0.0,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReasoningResult: ...

    @abstractmethod
    def review(
        self,
        *,
        success: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        output: str = "",
        duration: float = 0.0,
        retry_count: int = 0,
        metadata: Optional[dict] = None,
    ) -> CognitiveResult: ...

    @abstractmethod
    def reflect(self, assessment: ExecutionAssessment) -> CognitiveResult: ...

    @abstractmethod
    def decide(self, assessment: ExecutionAssessment) -> CognitiveResult: ...

    @property
    @abstractmethod
    def reflection_engine(
        self,
    ) -> AbstractReflectionEngine: ...
