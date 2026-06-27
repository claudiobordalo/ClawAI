from __future__ import annotations

from typing import Optional

from clawai.engineering import AbstractMemory

from .cognitive_configuration import CognitiveConfiguration
from .decision_engine import AbstractDecisionEngine, DecisionEngine
from .failure_analysis import AbstractFailureAnalysis, FailureAnalysis
from .reasoning_engine import AbstractReasoningEngine, ReasoningEngine
from .reflection_engine import AbstractReflectionEngine, ReflectionEngine
from .reviewer import AbstractReviewer, Reviewer


class CognitiveFactory:
    def __init__(self, config: Optional[CognitiveConfiguration] = None) -> None:
        self._config = config or CognitiveConfiguration()

    @property
    def config(self) -> CognitiveConfiguration:
        return self._config

    def create_reviewer(self) -> AbstractReviewer:
        mode = self._config.review_mode
        if mode == "llm":
            msg = "LLM reviewer not implemented in Sprint 5.7"
            raise NotImplementedError(msg)
        return Reviewer()

    def create_decision_engine(self) -> AbstractDecisionEngine:
        mode = self._config.reasoning_mode
        if mode == "llm":
            msg = "LLM decision engine not implemented in Sprint 5.7"
            raise NotImplementedError(msg)
        return DecisionEngine()

    def create_reflection_engine(
        self, memory: Optional[AbstractMemory] = None
    ) -> AbstractReflectionEngine:
        return ReflectionEngine(memory=memory)

    def create_failure_analysis(self) -> AbstractFailureAnalysis:
        return FailureAnalysis()

    def create_reasoning_engine(
        self,
        reviewer: Optional[AbstractReviewer] = None,
        decision_engine: Optional[AbstractDecisionEngine] = None,
        reflection_engine: Optional[AbstractReflectionEngine] = None,
        failure_analysis: Optional[AbstractFailureAnalysis] = None,
        memory: Optional[AbstractMemory] = None,
    ) -> AbstractReasoningEngine:
        return ReasoningEngine(
            reviewer=reviewer or self.create_reviewer(),
            decision_engine=decision_engine or self.create_decision_engine(),
            reflection_engine=reflection_engine or self.create_reflection_engine(memory=memory),
            failure_analysis=failure_analysis or self.create_failure_analysis(),
        )

    @staticmethod
    def rule_based(
        memory: Optional[AbstractMemory] = None,
    ) -> AbstractReasoningEngine:
        return ReasoningEngine(
            reviewer=Reviewer(),
            decision_engine=DecisionEngine(),
            reflection_engine=ReflectionEngine(memory=memory),
            failure_analysis=FailureAnalysis(),
        )
