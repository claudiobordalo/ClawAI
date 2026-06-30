from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from clawai.ai.router import AIRouter, ModelRole
from clawai.search.search_engine import SearchResult

from .prompts import CODER_PROMPT, REVIEWER_PROMPT
from .types import DebateResult, PlannerResult, SupervisorResult
from .utils import limit_text


class DebateEngine:
    def __init__(self, router: AIRouter) -> None:
        self.router = router

    def debate(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        planner: PlannerResult,
        search_result: SearchResult,
    ) -> DebateResult:
        started = time.perf_counter()
        context = (
            f"Solicitação:\n{prompt}\n\n"
            f"Supervisor:\n{supervisor}\n\n"
            f"Plano:\n{planner.raw or planner.summary}\n\n"
            f"Contexto:\n{limit_text(search_result.prompt, 5000)}"
        )

        with ThreadPoolExecutor(max_workers=2) as executor:
            coder_future = executor.submit(
                self._ask,
                ModelRole.CODER,
                CODER_PROMPT,
                context,
            )
            reviewer_future = executor.submit(
                self._ask,
                ModelRole.REVIEWER,
                REVIEWER_PROMPT,
                context,
            )

            coder = coder_future.result()
            reviewer = reviewer_future.result()

        merged = f"CODER:\n{coder}\n\nREVIEWER:\n{reviewer}"
        duration_ms = (time.perf_counter() - started) * 1000

        return DebateResult(
            coder=coder,
            reviewer=reviewer,
            merged=merged,
            coder_model=self.router.model_for(ModelRole.CODER),
            reviewer_model=self.router.model_for(ModelRole.REVIEWER),
            duration_ms=duration_ms,
        )

    def _ask(self, role: ModelRole, system_prompt: str, prompt: str) -> str:
        try:
            return self.router.ask(prompt, role=role, system_prompt=system_prompt)
        except Exception as exc:
            return f"Falha ao consultar {role.value}: {exc}"