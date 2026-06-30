from __future__ import annotations

from clawai.ai.router import AIRouter, ModelRole
from clawai.search.search_engine import SearchResult

from .prompts import PLANNER_PROMPT
from .types import PlannerResult, SupervisorResult
from .utils import bullets, first_line, limit_text


class PlannerEngine:
    def __init__(self, router: AIRouter) -> None:
        self.router = router

    def plan(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        search_result: SearchResult,
    ) -> PlannerResult:
        raw = ""
        try:
            raw = self.router.ask(
                (
                    f"Solicitação:\n{prompt}\n\n"
                    f"Supervisor:\n{supervisor}\n\n"
                    f"Contexto:\n{limit_text(search_result.prompt, 5000)}"
                ),
                role=ModelRole.PLANNER,
                system_prompt=PLANNER_PROMPT,
            )
        except Exception as exc:
            raw = (
                f"Objetivo: {prompt}\n"
                f"Risco: Planner indisponível ({exc}).\n"
                "Subtarefas:\n"
                "1. Entender a solicitação.\n"
                "2. Propor a menor mudança segura.\n"
                "3. Validar o resultado.\n"
                "Critério de pronto: resposta clara e aplicável."
            )

        subtasks = bullets(raw)
        summary = first_line(raw) or raw.strip()[:400]

        return PlannerResult(
            summary=summary,
            subtasks=subtasks,
            raw=raw.strip(),
            model=self.router.model_for(ModelRole.PLANNER),
            duration_ms=0.0,
        )