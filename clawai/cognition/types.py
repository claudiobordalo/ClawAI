from __future__ import annotations

from dataclasses import dataclass, field

from clawai.ai.router import ModelRole
from clawai.search.search_engine import SearchTimings


@dataclass(slots=True, frozen=True)
class SupervisorResult:
    intent: str
    primary_role: ModelRole
    strategy: str
    should_parallel: bool
    confidence: float
    rationale: str


@dataclass(slots=True, frozen=True)
class PlannerResult:
    summary: str
    subtasks: list[str] = field(default_factory=list)
    raw: str = ""
    model: str = ""
    duration_ms: float = 0.0


@dataclass(slots=True, frozen=True)
class DebateResult:
    coder: str
    reviewer: str
    merged: str = ""
    coder_model: str = ""
    reviewer_model: str = ""
    duration_ms: float = 0.0


@dataclass(slots=True, frozen=True)
class SynthesisResult:
    answer: str
    raw: str = ""
    model: str = ""
    duration_ms: float = 0.0


@dataclass(slots=True, frozen=True)
class PipelineTimings:
    search: SearchTimings = field(default_factory=SearchTimings)
    supervisor_ms: float = 0.0
    planner_ms: float = 0.0
    debate_ms: float = 0.0
    synthesis_ms: float = 0.0
    postprocess_ms: float = 0.0
    total_ms: float = 0.0


@dataclass(slots=True, frozen=True)
class PipelineResult:
    answer: str
    provider: str
    model: str
    primary_role: ModelRole
    final_role: ModelRole
    used_memory: bool
    used_knowledge: bool
    requires_web: bool
    memory_saved: bool
    supervisor: SupervisorResult
    planner: PlannerResult
    debate: DebateResult
    synthesis: SynthesisResult
    timings: PipelineTimings