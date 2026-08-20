from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

from clawai.ai.router import AIRouter, ModelRole
from clawai.documents.reader import documents
from clawai.memory.memory import memory
from clawai.search.search_engine import search

from .debate import DebateEngine
from .judge import JudgeEngine
from .planner import PlannerEngine
from .response_post_processor import ResponsePostProcessor
from .supervisor import SupervisorEngine
from .types import PipelineResult, PipelineTimings
from .utils import limit_text

class CognitionPipeline:
    def __init__(
        self, 
        router: AIRouter | None = None, 
        provider_name: str | None = None,
        memory_manager: Any = None,
        search_engine: Any = None,
        document_reader: Any = None
    ) -> None:
        self.router = router or AIRouter()
        self.provider_name = provider_name or getattr(self.router, "_provider", "ollama")
        
        # Dependency Injection for core modules
        self.memory_manager = memory_manager or memory
        self.search_engine = search_engine or search
        self.document_reader = document_reader or documents

        self.supervisor = SupervisorEngine(self.router)
        self.planner = PlannerEngine(self.router)
        self.debate_engine = DebateEngine(self.router)
        self.judge = JudgeEngine(self.router)
        
        # Ensure post-processor uses the correct memory manager
        self._postprocessor = ResponsePostProcessor(self.memory_manager)

    def execute(self, prompt: str, file: str | None = None) -> PipelineResult:
        started = time.perf_counter()
        prepared = self._prepare_prompt(prompt, file)
        
        # Use the injected search engine
        search_result = self.search_engine.build_prompt(prepared)

        t = time.perf_counter()
        supervisor = self.supervisor.analyze(prepared, file, search_result)
        supervisor_ms = (time.perf_counter() - t) * 1000

        t = time.perf_counter()
        planner = self.planner.plan(prepared, supervisor, search_result)
        planner_ms = (time.perf_counter() - t) * 1000

        t = time.perf_counter()
        debate = self.debate_engine.debate(prepared, supervisor, planner, search_result)
        debate_ms = (time.perf_counter() - t) * 1000

        t = time.perf_counter()
        synthesis = self.judge.synthesize(prepared, supervisor, planner, debate, search_result)
        synthesis_ms = (time.perf_counter() - t) * 1000

        t = time.perf_counter()
        post = self._postprocessor.process(synthesis.answer)
        answer = post.answer
        memory_saved = post.memory_saved
        postprocess_ms = (time.perf_counter() - t) * 1000

        total_ms = (time.perf_counter() - started) * 1000

        return PipelineResult(
            answer=answer,
            provider=self.provider_name,
            model=self.router.model_for(ModelRole.REVIEWER),
            primary_role=supervisor.primary_role,
            final_role=ModelRole.REVIEWER,
            used_memory=search_result.used_memory,
            used_knowledge=search_result.used_knowledge,
            requires_web=search_result.requires_web,
            memory_saved=memory_saved,
            supervisor=supervisor,
            planner=planner,
            debate=debate,
            synthesis=synthesis,
            timings=PipelineTimings(
                search=search_result.timings,
                supervisor_ms=supervisor_ms,
                planner_ms=planner_ms,
                debate_ms=debate_ms,
                synthesis_ms=synthesis_ms,
                postprocess_ms=postprocess_ms,
                total_ms=total_ms,
            ),
        )

    def stream(self, prompt: str, file: str | None = None, chunk_size: int = 120) -> Iterator[dict[str, object]]:
        result = self.execute(prompt, file)
        for start in range(0, len(result.answer), chunk_size):
            yield {"type": "delta", "text": result.answer[start:start + chunk_size]}
        yield {"type": "final", "reply": asdict(result)}

    def _build_workspace_context(self, prompt: str) -> str:
        """Build a workspace context string for the given prompt."""
        # Check if there's a workspace path configured
        workspace_path = getattr(self, "workspace_path", None)
        if workspace_path:
            return f"Workspace ativo: {workspace_path}"
        # No workspace configured, return a neutral message
        return "Workspace: não configurado. Use operações padrão."

    def _prepare_prompt(self, prompt: str, file: str | None) -> str:
        if not file:
            return prompt

        path = Path(file)
        # Use the injected document reader
        content = self.document_reader.read(path)
        return (
            f"Arquivo enviado:\n{path.name}\n\n"
            f"Conteúdo:\n{content}\n\n"
            f"Pergunta do usuário:\n{prompt}"
        )
