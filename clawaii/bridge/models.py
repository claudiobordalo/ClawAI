from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class BridgeParticipantConfig:
    role: str
    provider: str
    model: str = ""


@dataclass(slots=True, frozen=True)
class BridgeParticipantResult:
    role: str
    provider: str
    model: str
    content: str
    elapsed_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error: str = ""


@dataclass(slots=True, frozen=True)
class BridgeToolDecision:
    recommended_tool: str
    reason: str
    confidence: float = 0.0
    winner_role: str = ""
    source: str = "heuristic"


@dataclass(slots=True, frozen=True)
class BridgeConsultResult:
    prompt: str
    system_prompt: str
    heuristic_tool: str
    heuristic_reason: str
    decision: BridgeToolDecision
    winner_role: str
    final_answer: str
    participants: list[BridgeParticipantResult] = field(default_factory=list)
    elapsed_ms: float = 0.0
    parallel_roles: list[str] = field(default_factory=list)
    judge_model: str = ""
    judge_provider: str = ""
    judge_raw: str = ""
