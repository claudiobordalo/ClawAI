from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Iterator

from clawai.ai.router import AIRouter, ModelRole
from clawai.autonomy.agent_runtime import AgentRuntime
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


class CognitionPipeline:
    def __init__(
        self,
        router: AIRouter,
        provider_name: str,
        *,
        agent_max_iterations: int = 3,
        max_direct_prompt_chars: int = 8_000,
        max_workspace_items: int = 30,
    ) -> None:
        self.router = router
        self.provider_name = provider_name
        self.runtime = AgentRuntime(router=self.router, max_iterations=agent_max_iterations)
        self.intent_classifier = IntentClassifier()
        self.prompt_builder = PromptBuilder(
            max_prompt_chars=max_direct_prompt_chars,
            max_workspace_items=max_workspace_items,
        )

    def execute(self, prompt: str, file: str | None = None) -> ChatResponse:
        started = time.perf_counter()
        stage_timings: list[ChatStageTiming] = []

        decision = self.intent_classifier.classify(prompt, file)
        prepared = self.prompt_builder.build(prompt, file)

        if decision.use_agent:
            t0 = time.perf_counter()
            runtime_result = self.runtime.run(prepared.text)
            stage_timings.append(ChatStageTiming(name="agent_runtime", ms=(time.perf_counter() - t0) * 1000))

            answer, memory_saved = self._finalize_answer(str(runtime_result.get("answer") or ""))
            return ChatResponse(
                answer=answer,
                used_memory=False,
                used_knowledge=bool(runtime_result.get("used_tools")),
                requires_web=False,
                provider=self.provider_name,
                model=self.router.model_for(ModelRole.DEFAULT),
                memory_saved=memory_saved,
                timings=ChatTimings(
                    search=SearchTimings(),
                    model_ms=0.0,
                    postprocess_ms=0.0,
                    total_ms=(time.perf_counter() - started) * 1000,
                ),
                stage_timings=stage_timings,
            )

        t0 = time.perf_counter()
        answer = self.router.ask(
            prompt=prepared.text,
            role=prepared.role,
            system_prompt=BASE_SYSTEM_PROMPT,
        )
        stage_timings.append(ChatStageTiming(name="direct_model", ms=(time.perf_counter() - t0) * 1000))

        t1 = time.perf_counter()
        answer, memory_saved = self._finalize_answer(answer)
        stage_timings.append(ChatStageTiming(name="postprocess", ms=(time.perf_counter() - t1) * 1000))

        return ChatResponse(
            answer=answer,
            used_memory=False,
            used_knowledge=False,
            requires_web=False,
            provider=self.provider_name,
            model=self.router.model_for(ModelRole.DEFAULT),
            memory_saved=memory_saved,
            timings=ChatTimings(
                search=SearchTimings(),
                model_ms=0.0,
                postprocess_ms=0.0,
                total_ms=(time.perf_counter() - started) * 1000,
            ),
            stage_timings=stage_timings,
        )

    def stream(self, prompt: str, file: str | None = None, chunk_size: int = 120) -> Iterator[dict[str, object]]:
        result = self.execute(prompt, file)
        for start in range(0, len(result.answer), chunk_size):
            yield {"type": "delta", "text": result.answer[start:start + chunk_size]}
        yield {"type": "final", "reply": asdict(result)}

    def _finalize_answer(self, answer: str) -> tuple[str, bool]:
        from clawai.memory.memory import memory

        if "<MEMORY>" not in answer or "</MEMORY>" not in answer:
            return answer, False

        block = answer.split("<MEMORY>", 1)[1].split("</MEMORY>", 1)[0]
        title = ""
        content = ""
        for line in block.splitlines():
            lower = line.lower()
            if lower.startswith("titulo:"):
                title = line.split(":", 1)[1].strip()
            elif lower.startswith("conteudo:"):
                content = line.split(":", 1)[1].strip()

        if title and content:
            memory.add(category="general", title=title, content=content, source="chat")

        return answer.split("<MEMORY>", 1)[0].strip(), bool(title and content)


class ChatService:
    def __init__(self) -> None:
        self.router = AIRouter()
        self.provider_name = getattr(self.router, "_provider", "ollama")
        self.pipeline = CognitionPipeline(self.router, self.provider_name)

    def ask(self, prompt: str, file: str | None = None) -> ChatResponse:
        return self.pipeline.execute(prompt, file)

    def ask_stream(self, prompt: str, file: str | None = None) -> Iterator[dict[str, object]]:
        yield from self.pipeline.stream(prompt, file)


chat = ChatService()