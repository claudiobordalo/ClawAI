from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

from clawai.ai.router import AIRouter, ModelRole
from clawai.documents.reader import documents
from clawai.memory.memory import memory
from clawai.search.search_engine import SearchResult, SearchTimings, search


BASE_SYSTEM_PROMPT = """
Você é o ClawAI, um agente de desenvolvimento dentro do próprio projeto.

Responda como o ClawAI, não como o provider subjacente.
Se o pedido envolver interface, backend, arquivos, workspace, automação, correção de bugs
ou refatoração, trate como uma tarefa do repositório atual e seja direto.

Quando for apropriado, diga quais arquivos serão alterados, qual é a estratégia e qual
será o próximo passo. Não diga que você não pode alterar o projeto.
Se houver erro técnico, explique a causa real e a correção provável.
""".strip()

SUPERVISOR_SYSTEM_PROMPT = """
Você é o Supervisor do ClawAI.
Classifique a solicitação e defina a melhor estratégia.

Responda em JSON puro, sem markdown, com estas chaves:
- intent: curto, por exemplo "code", "plan", "review", "vision", "qa" ou "general"
- primary_role: um de "default", "planner", "coder", "reviewer", "vision"
- strategy: "direct" ou "parallel"
- should_parallel: true ou false
- confidence: número entre 0 e 1
- rationale: explicação curta
""".strip()

PLANNER_SYSTEM_PROMPT = """
Você é o Planner do ClawAI.
Produza um plano curto, claro e executável.

Estrutura esperada:
1. Objetivo
2. Subtarefas numeradas
3. Riscos
4. Critério de pronto
""".strip()

CODER_SYSTEM_PROMPT = """
Você é o Coder do ClawAI.
Converta o plano em uma proposta concreta de implementação.

Regras:
- diga arquivos prováveis de alteração
- descreva a mudança de forma objetiva
- não explique teoria desnecessária
- se algo estiver bloqueado, diga o bloqueio e o próximo passo
""".strip()

REVIEWER_SYSTEM_PROMPT = """
Você é o Reviewer do ClawAI.
Revise a proposta e aponte falhas, riscos e melhorias.

Regras:
- seja objetivo
- destaque regressões possíveis
- sugira correções práticas
""".strip()

JUDGE_SYSTEM_PROMPT = """
Você é o Judge do ClawAI.
Considere a classificação do supervisor, o plano, a saída do coder e a revisão.

Sua resposta final deve:
- ser direta
- falar como o ClawAI, não como o provider
- priorizar a melhor solução para o usuário
- evitar citar nomes de modelos ou etapas internas
- indicar próximos passos concretos quando apropriado
""".strip()

CODER_HINTS = (
    "implemente",
    "corrija",
    "conserte",
    "refatore",
    "ajuste",
    "alterar",
    "modifique",
    "código",
    "codigo",
    "arquivo",
    "frontend",
    "backend",
    "react",
    "tsx",
    "py",
    "python",
    "fastapi",
    "layout",
    "ui",
    "interface",
    "git",
    "commit",
    "merge",
)

PLANNER_HINTS = (
    "planeje",
    "plano",
    "backlog",
    "roadmap",
    "priorize",
    "priorizar",
    "estratégia",
    "estrategia",
    "arquitetura",
    "organize",
    "organizar",
)

REVIEWER_HINTS = (
    "revise",
    "revisar",
    "review",
    "avaliar",
    "avalie",
    "comparar",
    "compare",
    "audite",
    "auditar",
    "analisar o código",
    "analisar o codigo",
)

VISION_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}


@dataclass(slots=True, frozen=True)
class ChatTimings:
    search: SearchTimings = field(default_factory=SearchTimings)
    model_ms: float = 0.0
    postprocess_ms: float = 0.0
    total_ms: float = 0.0


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
class JudgeResult:
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
    judge_ms: float = 0.0
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
    memory_saved: bool = False
    supervisor: SupervisorResult = field(default=None)  # type: ignore[assignment]
    planner: PlannerResult = field(default=None)  # type: ignore[assignment]
    debate: DebateResult = field(default=None)  # type: ignore[assignment]
    judge: JudgeResult = field(default=None)  # type: ignore[assignment]
    timings: PipelineTimings = field(default_factory=PipelineTimings)


class SupervisorEngine:
    def __init__(self, router: AIRouter) -> None:
        self.router = router

    def analyze(
        self,
        prompt: str,
        file: str | None,
        search_result: SearchResult,
    ) -> SupervisorResult:
        file_suffix = Path(file).suffix.lower() if file else ""
        if file_suffix in VISION_SUFFIXES:
            return SupervisorResult(
                intent="vision",
                primary_role=ModelRole.VISION,
                strategy="direct",
                should_parallel=False,
                confidence=0.95,
                rationale="Arquivo visual detectado; usar visão diretamente.",
            )

        raw = ""
        try:
            raw = self.router.ask(
                self._build_prompt(prompt, file, search_result),
                role=ModelRole.DEFAULT,
                system_prompt=SUPERVISOR_SYSTEM_PROMPT,
            )
            parsed = self._parse_model_result(raw)
            if parsed is not None:
                return parsed
        except Exception:
            pass

        return self._heuristic_result(prompt, file, search_result)

    def _build_prompt(
        self,
        prompt: str,
        file: str | None,
        search_result: SearchResult,
    ) -> str:
        path_line = f"Arquivo: {Path(file).name}\n" if file else ""
        return (
            f"{path_line}Solicitação do usuário:\n{prompt}\n\n"
            f"Contexto recuperado:\n{_limit_text(search_result.prompt, 5000)}\n"
        )

    def _parse_model_result(self, raw: str) -> SupervisorResult | None:
        data = _extract_json(raw)
        if not isinstance(data, dict):
            return None

        intent = str(data.get("intent", "general")).strip().lower() or "general"
        strategy = str(data.get("strategy", "parallel")).strip().lower() or "parallel"
        primary_role_raw = str(data.get("primary_role", "default")).strip().lower() or "default"
        should_parallel = bool(data.get("should_parallel", strategy == "parallel"))
        confidence = _clamp_float(data.get("confidence", 0.6), 0.0, 1.0)
        rationale = str(data.get("rationale", "")).strip()

        primary_role = _role_from_name(primary_role_raw, default=ModelRole.DEFAULT)

        return SupervisorResult(
            intent=intent,
            primary_role=primary_role,
            strategy="parallel" if should_parallel else "direct",
            should_parallel=should_parallel,
            confidence=confidence,
            rationale=rationale,
        )

    def _heuristic_result(
        self,
        prompt: str,
        file: str | None,
        search_result: SearchResult,
    ) -> SupervisorResult:
        text = f"{prompt} {Path(file).name if file else ''}".lower()

        if any(hint in text for hint in REVIEWER_HINTS):
            return SupervisorResult(
                intent="review",
                primary_role=ModelRole.REVIEWER,
                strategy="parallel",
                should_parallel=True,
                confidence=0.82,
                rationale="Pedido de revisão ou análise crítica detectado.",
            )

        if any(hint in text for hint in PLANNER_HINTS):
            return SupervisorResult(
                intent="plan",
                primary_role=ModelRole.PLANNER,
                strategy="parallel",
                should_parallel=True,
                confidence=0.84,
                rationale="Pedido de planejamento ou arquitetura detectado.",
            )

        if any(hint in text for hint in CODER_HINTS):
            return SupervisorResult(
                intent="code",
                primary_role=ModelRole.CODER,
                strategy="parallel",
                should_parallel=True,
                confidence=0.88,
                rationale="Pedido de implementação ou alteração de código detectado.",
            )

        if search_result.requires_web:
            return SupervisorResult(
                intent="qa",
                primary_role=ModelRole.DEFAULT,
                strategy="parallel",
                should_parallel=True,
                confidence=0.55,
                rationale="Sem base local suficiente; a resposta deve ser cautelosa.",
            )

        return SupervisorResult(
            intent="general",
            primary_role=ModelRole.DEFAULT,
            strategy="parallel",
            should_parallel=True,
            confidence=0.7,
            rationale="Fluxo geral do assistente com debate e síntese.",
        )


class PlannerEngine:
    def __init__(self, router: AIRouter) -> None:
        self.router = router

    def plan(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        search_result: SearchResult,
    ) -> PlannerResult:
        started = time.perf_counter()
        raw = ""

        try:
            raw = self.router.ask(
                self._build_prompt(prompt, supervisor, search_result),
                role=ModelRole.PLANNER,
                system_prompt=PLANNER_SYSTEM_PROMPT,
            )
        except Exception as exc:
            raw = self._fallback_plan(prompt, supervisor, exc)

        subtasks = _parse_subtasks(raw)
        summary = _first_nonempty_line(raw) or _limit_text(raw.strip(), 400)
        duration_ms = (time.perf_counter() - started) * 1000

        return PlannerResult(
            summary=summary,
            subtasks=subtasks,
            raw=raw.strip(),
            model=self.router.model_for(ModelRole.PLANNER),
            duration_ms=duration_ms,
        )

    def _build_prompt(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        search_result: SearchResult,
    ) -> str:
        return (
            f"Solicitação:\n{prompt}\n\n"
            f"Classificação do supervisor:\n"
            f"- intent: {supervisor.intent}\n"
            f"- primary_role: {supervisor.primary_role.value}\n"
            f"- strategy: {supervisor.strategy}\n"
            f"- should_parallel: {supervisor.should_parallel}\n"
            f"- rationale: {supervisor.rationale}\n\n"
            f"Contexto recuperado:\n{_limit_text(search_result.prompt, 5000)}\n\n"
            "Escreva um plano curto e objetivo, em português, com subtarefas executáveis."
        )

    def _fallback_plan(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        error: Exception,
    ) -> str:
        return (
            f"Objetivo: {prompt}\n"
            f"Risco: execução do Planner indisponível ({error}).\n"
            f"Subtarefas:\n"
            f"1. Entender a solicitação ({supervisor.intent}).\n"
            f"2. Propor mudança mínima e segura.\n"
            f"3. Validar o resultado com verify.\n"
            f"Critério de pronto: resposta clara e aplicável."
        )


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

        coder_prompt = self._build_coder_prompt(prompt, supervisor, planner, search_result)
        reviewer_prompt = self._build_reviewer_prompt(prompt, supervisor, planner, search_result)

        with ThreadPoolExecutor(max_workers=2) as executor:
            coder_future = executor.submit(self._ask, coder_prompt, ModelRole.CODER, CODER_SYSTEM_PROMPT)
            reviewer_future = executor.submit(self._ask, reviewer_prompt, ModelRole.REVIEWER, REVIEWER_SYSTEM_PROMPT)

            coder = coder_future.result()
            reviewer = reviewer_future.result()

        merged = (
            f"CODER:\n{coder}\n\n"
            f"REVIEWER:\n{reviewer}"
        )

        duration_ms = (time.perf_counter() - started) * 1000

        return DebateResult(
            coder=coder,
            reviewer=reviewer,
            merged=merged,
            coder_model=self.router.model_for(ModelRole.CODER),
            reviewer_model=self.router.model_for(ModelRole.REVIEWER),
            duration_ms=duration_ms,
        )

    def _ask(self, prompt: str, role: ModelRole, system_prompt: str) -> str:
        try:
            return self.router.ask(prompt, role=role, system_prompt=system_prompt)
        except Exception as exc:
            return f"Falha ao consultar {role.value}: {exc}"

    def _build_coder_prompt(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        planner: PlannerResult,
        search_result: SearchResult,
    ) -> str:
        return (
            f"Solicitação original:\n{prompt}\n\n"
            f"Classificação do supervisor:\n{supervisor}\n\n"
            f"Plano:\n{planner.raw or planner.summary}\n\n"
            f"Contexto recuperado:\n{_limit_text(search_result.prompt, 5000)}\n\n"
            "Responda como Coder: proponha a implementação concreta, arquivos prováveis e passos diretos."
        )

    def _build_reviewer_prompt(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        planner: PlannerResult,
        search_result: SearchResult,
    ) -> str:
        return (
            f"Solicitação original:\n{prompt}\n\n"
            f"Classificação do supervisor:\n{supervisor}\n\n"
            f"Plano:\n{planner.raw or planner.summary}\n\n"
            f"Contexto recuperado:\n{_limit_text(search_result.prompt, 5000)}\n\n"
            "Responda como Reviewer: critique o plano, aponte lacunas, riscos e melhorias objetivas."
        )


class JudgeEngine:
    def __init__(self, router: AIRouter) -> None:
        self.router = router

    def judge(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        planner: PlannerResult,
        debate: DebateResult,
        search_result: SearchResult,
    ) -> JudgeResult:
        started = time.perf_counter()
        raw = ""

        try:
            raw = self.router.ask(
                self._build_prompt(prompt, supervisor, planner, debate, search_result),
                role=ModelRole.JUDGE,
                system_prompt=JUDGE_SYSTEM_PROMPT,
            )
        except Exception as exc:
            raw = self._fallback_answer(prompt, supervisor, planner, debate, exc)

        duration_ms = (time.perf_counter() - started) * 1000
        answer = raw.strip()
        return JudgeResult(
            answer=answer,
            raw=raw,
            model=self.router.model_for(ModelRole.JUDGE),
            duration_ms=duration_ms,
        )

    def _build_prompt(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        planner: PlannerResult,
        debate: DebateResult,
        search_result: SearchResult,
    ) -> str:
        return (
            f"Solicitação original:\n{prompt}\n\n"
            f"Supervisor:\n{supervisor}\n\n"
            f"Plano:\n{planner.raw or planner.summary}\n\n"
            f"Coder:\n{debate.coder}\n\n"
            f"Reviewer:\n{debate.reviewer}\n\n"
            f"Contexto recuperado:\n{_limit_text(search_result.prompt, 5000)}\n\n"
            "Produza a melhor resposta final ao usuário, em português, sem mencionar etapas internas."
        )

    def _fallback_answer(
        self,
        prompt: str,
        supervisor: SupervisorResult,
        planner: PlannerResult,
        debate: DebateResult,
        error: Exception,
    ) -> str:
        return (
            f"Tive uma falha ao sintetizar a resposta final ({error}).\n\n"
            f"Pedido: {prompt}\n\n"
            f"Plano resumido: {planner.summary}\n\n"
            f"Próximo passo recomendado: {planner.subtasks[0] if planner.subtasks else supervisor.rationale}\n\n"
            f"Discussão técnica:\n{debate.merged}"
        )


class CognitionPipeline:
    def __init__(
        self,
        router: AIRouter | None = None,
        provider_name: str | None = None,
    ) -> None:
        self.router = router or AIRouter()
        self.provider_name = provider_name or getattr(self.router, "_provider", "ollama")
        self.supervisor = SupervisorEngine(self.router)
        self.planner = PlannerEngine(self.router)
        self.debate_engine = DebateEngine(self.router)
        self.judge = JudgeEngine(self.router)

    def _prepare_prompt(
        self,
        prompt: str,
        file: str | None = None,
    ) -> str:
        if not file:
            return prompt

        path = Path(file)
        if not path.exists():
            raise FileNotFoundError(path)

        content = documents.read(path)
        return (
            "Arquivo enviado:\n\n"
            f"Nome:\n{path.name}\n\n"
            "Conteúdo:\n\n"
            f"{content}\n\n"
            "Pergunta do usuário:\n\n"
            f"{prompt}"
        )

    def _finalize_answer(self, answer: str) -> tuple[str, bool]:
        memory_saved = False

        if "<MEMORY>" in answer and "</MEMORY>" in answer:
            try:
                block = answer.split("<MEMORY>", 1)[1].split("</MEMORY>", 1)[0]
                title = ""
                content = ""

                for line in block.splitlines():
                    if line.lower().startswith("titulo:"):
                        title = line.split(":", 1)[1].strip()
                    if line.lower().startswith("conteudo:"):
                        content = line.split(":", 1)[1].strip()

                if title and content:
                    memory.add(
                        category="general",
                        title=title,
                        content=content,
                        source="chat",
                    )
                    memory_saved = True

                answer = answer.split("<MEMORY>", 1)[0].strip()
            except Exception:
                pass

        return answer, memory_saved

    def execute(
        self,
        prompt: str,
        file: str | None = None,
    ) -> PipelineResult:
        started = time.perf_counter()
        prepared_prompt = self._prepare_prompt(prompt, file)

        search_result = search.build_prompt(prepared_prompt)

        supervisor_started = time.perf_counter()
        supervisor = self.supervisor.analyze(prepared_prompt, file, search_result)
        supervisor_ms = (time.perf_counter() - supervisor_started) * 1000

        planner_started = time.perf_counter()
        planner = self.planner.plan(prepared_prompt, supervisor, search_result)
        planner_ms = (time.perf_counter() - planner_started) * 1000

        debate_started = time.perf_counter()
        debate = self.debate_engine.debate(prepared_prompt, supervisor, planner, search_result)
        debate_ms = (time.perf_counter() - debate_started) * 1000

        judge_started = time.perf_counter()
        judge = self.judge.judge(prepared_prompt, supervisor, planner, debate, search_result)
        judge_ms = (time.perf_counter() - judge_started) * 1000

        postprocess_started = time.perf_counter()
        answer, memory_saved = self._finalize_answer(judge.answer)
        postprocess_ms = (time.perf_counter() - postprocess_started) * 1000

        total_ms = (time.perf_counter() - started) * 1000

        return PipelineResult(
            answer=answer,
            provider=self.provider_name,
            model=self.router.model_for(ModelRole.JUDGE),
            primary_role=supervisor.primary_role,
            final_role=ModelRole.JUDGE,
            used_memory=search_result.used_memory,
            used_knowledge=search_result.used_knowledge,
            requires_web=search_result.requires_web,
            memory_saved=memory_saved,
            supervisor=supervisor,
            planner=planner,
            debate=debate,
            judge=judge,
            timings=PipelineTimings(
                search=search_result.timings,
                supervisor_ms=supervisor_ms,
                planner_ms=planner_ms,
                debate_ms=debate_ms,
                judge_ms=judge_ms,
                postprocess_ms=postprocess_ms,
                total_ms=total_ms,
            ),
        )

    def stream(
        self,
        prompt: str,
        file: str | None = None,
        chunk_size: int = 120,
    ) -> Iterator[dict[str, object]]:
        result = self.execute(prompt, file)
        answer = result.answer

        if not answer:
            yield {
                "type": "final",
                "reply": asdict(result),
            }
            return

        for start in range(0, len(answer), chunk_size):
            yield {
                "type": "delta",
                "text": answer[start:start + chunk_size],
            }

        yield {
            "type": "final",
            "reply": asdict(result),
        }


class ChatService:
    def __init__(self) -> None:
        self.router = AIRouter()
        self.provider_name = getattr(self.router, "_provider", "ollama")
        self.pipeline = CognitionPipeline(router=self.router, provider_name=self.provider_name)

    def _to_chat_response(self, result: PipelineResult) -> ChatResponse:
        return ChatResponse(
            answer=result.answer,
            used_memory=result.used_memory,
            used_knowledge=result.used_knowledge,
            requires_web=result.requires_web,
            provider=result.provider,
            model=result.model,
            memory_saved=result.memory_saved,
            timings=ChatTimings(
                search=result.timings.search,
                model_ms=result.judge.duration_ms,
                postprocess_ms=result.timings.postprocess_ms,
                total_ms=result.timings.total_ms,
            ),
        )

    def ask(
        self,
        prompt: str,
        file: str | None = None,
    ) -> ChatResponse:
        result = self.pipeline.execute(prompt, file)
        return self._to_chat_response(result)

    def ask_stream(
        self,
        prompt: str,
        file: str | None = None,
    ) -> Iterator[dict[str, object]]:
        yield from self.pipeline.stream(prompt, file)


# -------------------- helpers --------------------


def _limit_text(text: str, limit: int = 6000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n..."


def _clamp_float(value: object, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except Exception:
        return minimum
    return max(minimum, min(maximum, number))


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_json(text: str) -> dict[str, object] | None:
    cleaned = _strip_code_fences(text)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
    else:
        candidate = cleaned

    try:
        data = json.loads(candidate)
    except Exception:
        return None

    return data if isinstance(data, dict) else None


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        value = line.strip()
        if value:
            return value
    return ""


def _parse_subtasks(text: str) -> list[str]:
    subtasks: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^(\d+[\.)]|[-*•])\s+", stripped):
            subtasks.append(re.sub(r"^(\d+[\.)]|[-*•])\s+", "", stripped).strip())
    if not subtasks:
        first = _first_nonempty_line(text)
        if first:
            subtasks.append(first)
    return subtasks


def _role_from_name(value: str, default: ModelRole) -> ModelRole:
    normalized = value.strip().lower()
    mapping = {
        "default": ModelRole.DEFAULT,
        "planner": ModelRole.PLANNER,
        "coder": ModelRole.CODER,
        "reviewer": ModelRole.REVIEWER,
        "vision": ModelRole.VISION,
        "judge": ModelRole.JUDGE,
        "embedding": ModelRole.EMBEDDING,
    }
    return mapping.get(normalized, default)


chat = ChatService()
