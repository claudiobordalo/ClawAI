from __future__ import annotations

import time

from clawai.ai.router import AIRouter, ModelRole
from clawai.search.search_engine import SearchResult

from .prompts import SYNTH_PROMPT
from .types import DebateResult, PlannerResult, SynthesisResult, SupervisorResult
from .utils import limit_text


class JudgeEngine:
    def __init__(self, router: AIRouter) -> None:
        self.router = router

    def synthesize(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        planner: PlannerResult,
        debate: DebateResult,
        search_result: SearchResult,
    ) -> SynthesisResult:
        started = time.perf_counter()
        context = (
            f"Solicitação:\n{prompt}\n\n"
            f"Supervisor:\n{supervisor}\n\n"
            f"Plano:\n{planner.raw or planner.summary}\n\n"
            f"Coder:\n{debate.coder}\n\n"
            f"Reviewer:\n{debate.reviewer}\n\n"
            f"Contexto:\n{limit_text(search_result.prompt, 5000)}"
        )

        try:
            raw = self.router.ask(
                context,
                role=ModelRole.REVIEWER,
                system_prompt=SYNTH_PROMPT,
            )
        except Exception as exc:
            raw = (
                f"Tive uma falha ao sintetizar a resposta final ({exc}).\n\n"
                f"Pedido: {prompt}\n\n"
                f"Plano resumido: {planner.summary}\n\n"
                f"Próximo passo recomendado: {planner.subtasks[0] if planner.subtasks else supervisor.rationale}\n\n"
                f"Discussão técnica:\n{debate.merged}"
            )

        duration_ms = (time.perf_counter() - started) * 1000
        return SynthesisResult(
            answer=raw.strip(),
            raw=raw,
            model=self.router.model_for(ModelRole.REVIEWER),
            duration_ms=duration_ms,
        )