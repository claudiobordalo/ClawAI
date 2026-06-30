from __future__ import annotations

from pathlib import Path

from clawai.ai.router import AIRouter, ModelRole
from clawai.search.search_engine import SearchResult

from .prompts import CODER_HINTS, PLANNER_HINTS, REVIEWER_HINTS, SUPERVISOR_PROMPT, VISION_SUFFIXES
from .types import SupervisorResult
from .utils import clamp_float, extract_json, role_from_name


class SupervisorEngine:
    def __init__(self, router: AIRouter) -> None:
        self.router = router

    def analyze(
        self,
        prompt: str,
        file: str | None,
        search_result: SearchResult,
    ) -> SupervisorResult:
        if file and Path(file).suffix.lower() in VISION_SUFFIXES:
            return SupervisorResult(
                intent="vision",
                primary_role=ModelRole.VISION,
                strategy="direct",
                should_parallel=False,
                confidence=0.95,
                rationale="arquivo visual detectado",
            )

        text = f"{prompt} {Path(file).name if file else ''}".lower()

        if any(hint in text for hint in REVIEWER_HINTS):
            return SupervisorResult(
                intent="review",
                primary_role=ModelRole.REVIEWER,
                strategy="parallel",
                should_parallel=True,
                confidence=0.82,
                rationale="pedido de revisão",
            )

        if any(hint in text for hint in PLANNER_HINTS):
            return SupervisorResult(
                intent="plan",
                primary_role=ModelRole.PLANNER,
                strategy="parallel",
                should_parallel=True,
                confidence=0.84,
                rationale="pedido de planejamento",
            )

        if any(hint in text for hint in CODER_HINTS):
            return SupervisorResult(
                intent="code",
                primary_role=ModelRole.CODER,
                strategy="parallel",
                should_parallel=True,
                confidence=0.88,
                rationale="pedido de implementação",
            )

        try:
            raw = self.router.ask(
                f"Solicitação:\n{prompt}\n\nContexto:\n{search_result.prompt}",
                role=ModelRole.DEFAULT,
                system_prompt=SUPERVISOR_PROMPT,
            )
            data = extract_json(raw)
            if isinstance(data, dict):
                return SupervisorResult(
                    intent=str(data.get("intent", "general")),
                    primary_role=role_from_name(str(data.get("primary_role", "default"))),
                    strategy=str(data.get("strategy", "parallel")),
                    should_parallel=bool(data.get("should_parallel", True)),
                    confidence=clamp_float(data.get("confidence", 0.6), 0.0, 1.0),
                    rationale=str(data.get("rationale", "")),
                )
        except Exception:
            pass

        return SupervisorResult(
            intent="general",
            primary_role=ModelRole.DEFAULT,
            strategy="parallel",
            should_parallel=True,
            confidence=0.7,
            rationale="fluxo geral",
        )