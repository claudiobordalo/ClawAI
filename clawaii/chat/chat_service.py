from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Iterator

from clawai.ai.router import AIRouter, ModelRole
from clawai.autonomy.agent_runtime import AgentRuntime
from clawai.cognition.pipeline import CognitionPipeline
from clawai.cognition.types import PipelineResult
from clawai.search.search_engine import SearchTimings
from clawai.workspaces.manager import workspace_manager
from clawai.chat.intent_classifier import IntentClassifier
from clawai.chat.prompt_builder import PromptBuilder

BASE_SYSTEM_PROMPT = (
    "Você é o ClawAI, um agente de desenvolvimento dentro do próprio projeto. "
    "Responda como o ClawAI e seja direto."
)


@dataclass(slots=True, frozen=True)
class ChatTimings:
    search: SearchTimings = field(default_factory=SearchTimings)
    model_ms: float = 0.0
    postprocess_ms: float = 0.0
    total_ms: float = 0.0


@dataclass(slots=True, frozen=True)
class ChatStageTiming:
    name: str
    ms: float


@dataclass(slots=True, frozen=True)
class ChatResponse:
    answer: str
    used_memory: bool
    used_knowledge: bool
    requires_web: bool
    provider: str
    model: str
    memory_saved: bool = False
    timings: ChatTimings = field(default_factory=ChatTimings)
    stage_timings: list[ChatStageTiming] = field(default_factory=list)

    @classmethod
    def from_pipeline(cls, result: PipelineResult) -> "ChatResponse":
        return cls(
            answer=result.answer,
            used_memory=result.used_memory,
            used_knowledge=result.used_knowledge,
            requires_web=result.requires_web,
            provider=result.provider,
            model=result.model,
            memory_saved=result.memory_saved,
            timings=ChatTimings(
                search=result.timings.search,
                model_ms=result.synthesis.duration_ms,
                postprocess_ms=result.timings.postprocess_ms,
                total_ms=result.timings.total_ms,
            ),
        )


class ChatService:
    def __init__(self, router: AIRouter | None = None, pipeline: CognitionPipeline | None = None) -> None:
        self.router = router or AIRouter()
        self.pipeline = pipeline or CognitionPipeline(router=self.router)

    def ask(self, prompt: str, file: str | None = None) -> ChatResponse:
        # A CognitionPipeline já trata a classificação de intenção e o building do prompt
        return self.pipeline.execute(prompt, file)

    def ask_stream(self, prompt: str, file: str | None = None) -> Iterator[dict[str, object]]:
        yield from self.pipeline.stream(prompt, file)


# Instância padrão
# Nota: No contexto do bootstrap.py, isso será substituído pela injeção do container
chat = ChatService()
