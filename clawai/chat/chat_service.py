from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

from clawai.ai.router import AIRouter, ModelRole
from clawai.documents.reader import documents
from clawai.memory.memory import memory
from clawai.search.search_engine import SearchResult, SearchTimings, search
from clawai.cognition.pipeline import CognitionPipeline


BASE_SYSTEM_PROMPT = """
Você é o ClawAI, um agente de desenvolvimento dentro do próprio projeto.

Responda como o ClawAI, não como o provider subjacente.
Se o pedido envolver interface, backend, arquivos, workspace, automação, correção de bugs
ou refatoração, trate como uma tarefa do repositório atual e seja direto.

Quando for apropriado, diga quais arquivos serão alterados, qual é a estratégia e qual
será o próximo passo. Não diga que você não pode alterar o projeto.
Se houver erro técnico, explique a causa real e a correção provável.
""".strip()

ROLE_SYSTEM_PROMPTS: dict[ModelRole, str] = {
    ModelRole.DEFAULT: BASE_SYSTEM_PROMPT,
    ModelRole.PLANNER: (
        BASE_SYSTEM_PROMPT
        + "\n\nAtue como Planner do ClawAI. Priorize objetivos, quebre em subtarefas e proponha a sequência de execução."
    ),
    ModelRole.CODER: (
        BASE_SYSTEM_PROMPT
        + "\n\nAtue como Coder do ClawAI. Foque em mudanças concretas de código, arquivos afetados e patch direto."
    ),
    ModelRole.REVIEWER: (
        BASE_SYSTEM_PROMPT
        + "\n\nAtue como Reviewer do ClawAI. Revise o plano ou o código, aponte riscos e sugira correções objetivas."
    ),
    ModelRole.VISION: (
        BASE_SYSTEM_PROMPT
        + "\n\nAtue como Vision do ClawAI. Analise imagens, telas e layouts com precisão e descreva problemas visuais."
    ),
    ModelRole.EMBEDDING: BASE_SYSTEM_PROMPT,
}

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


class ChatService:
    def __init__(self) -> None:
        self.router = AIRouter()
        self.provider_name = getattr(self.router, "_provider", "ollama")

    def _resolve_role(
        self,
        prompt: str,
        file: str | None = None,
    ) -> ModelRole:
        pieces = [prompt.lower()]

        if file:
            path = Path(file)
            pieces.append(path.name.lower())

            if path.suffix.lower() in VISION_SUFFIXES:
                return ModelRole.VISION

        text = " \n".join(pieces)

        if any(hint in text for hint in REVIEWER_HINTS):
            return ModelRole.REVIEWER

        if any(hint in text for hint in PLANNER_HINTS):
            return ModelRole.PLANNER

        if any(hint in text for hint in CODER_HINTS):
            return ModelRole.CODER

        return ModelRole.DEFAULT

    def _build_system_prompt(self, role: ModelRole) -> str:
        return ROLE_SYSTEM_PROMPTS.get(role, BASE_SYSTEM_PROMPT)

    def _prepare_prompt(
        self,
        prompt: str,
        file: str | None = None,
    ) -> tuple[ModelRole, str, str, SearchResult]:
        if file:
            path = Path(file)

            if not path.exists():
                raise FileNotFoundError(path)

            content = documents.read(path)

            prompt = (
                "Arquivo enviado:\n\n"
                f"Nome:\n{path.name}\n\n"
                "Conteúdo:\n\n"
                f"{content}\n\n"
                "Pergunta do usuário:\n\n"
                f"{prompt}"
            )

        role = self._resolve_role(prompt, file)
        search_result = search.build_prompt(prompt)
        system_prompt = self._build_system_prompt(role)
        model_prompt = search_result.prompt

        return role, system_prompt, model_prompt, search_result

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

    def _fallback_response(
        self,
        error: Exception,
        search_result: SearchResult,
        role: ModelRole,
    ) -> ChatResponse:
        text = str(error)
        lower = text.lower()

        if "out-of-memory" in lower or "unable to allocate" in lower or "failed to allocate" in lower:
            answer = (
                "O modelo local não conseguiu iniciar por falta de memória. "
                "Troque para um modelo menor ou libere RAM/VRAM e tente novamente."
            )
        else:
            answer = (
                "A resposta falhou no backend. Verifique o provider local e tente novamente."
            )

        return ChatResponse(
            answer=answer,
            used_memory=search_result.used_memory,
            used_knowledge=search_result.used_knowledge,
            requires_web=search_result.requires_web,
            provider=self.provider_name,
            model=self.router.model_for(role),
            memory_saved=False,
            timings=ChatTimings(
                search=search_result.timings,
                model_ms=0.0,
                postprocess_ms=0.0,
                total_ms=0.0,
            ),
        )

    def ask(
        self,
        prompt: str,
        file: str | None = None,
    ) -> ChatResponse:
        started = time.perf_counter()

        role, system_prompt, model_prompt, search_result = self._prepare_prompt(prompt, file)

        model_started = time.perf_counter()
        try:
            raw_answer = self.router.ask(
                model_prompt,
                role=role,
                system_prompt=system_prompt,
            )
        except Exception as exc:
            return self._fallback_response(exc, search_result, role)
        model_ms = (time.perf_counter() - model_started) * 1000

        postprocess_started = time.perf_counter()
        answer, memory_saved = self._finalize_answer(raw_answer)
        postprocess_ms = (time.perf_counter() - postprocess_started) * 1000

        total_ms = (time.perf_counter() - started) * 1000

        return ChatResponse(
            answer=answer,
            used_memory=search_result.used_memory,
            used_knowledge=search_result.used_knowledge,
            requires_web=search_result.requires_web,
            provider=self.provider_name,
            model=self.router.model_for(role),
            memory_saved=memory_saved,
            timings=ChatTimings(
                search=search_result.timings,
                model_ms=model_ms,
                postprocess_ms=postprocess_ms,
                total_ms=total_ms,
            ),
        )

    def ask_stream(
        self,
        prompt: str,
        file: str | None = None,
    ) -> Iterator[dict[str, object]]:
        started = time.perf_counter()

        role, system_prompt, model_prompt, search_result = self._prepare_prompt(prompt, file)

        model_started = time.perf_counter()
        chunks: list[str] = []
        emitted = ""

        try:
            for chunk in self.router.stream(
                model_prompt,
                role=role,
                system_prompt=system_prompt,
            ):
                chunks.append(chunk)
                combined = "".join(chunks)

                if "<MEMORY>" in combined:
                    visible = combined.split("<MEMORY>", 1)[0]
                else:
                    visible = combined

                delta = visible[len(emitted):]
                if delta:
                    yield {
                        "type": "delta",
                        "text": delta,
                    }
                    emitted = visible

                if "<MEMORY>" in combined:
                    break
        except Exception as exc:
            response = self._fallback_response(exc, search_result, role)
            yield {
                "type": "final",
                "reply": asdict(response),
            }
            return

        model_ms = (time.perf_counter() - model_started) * 1000

        raw_answer = "".join(chunks)

        postprocess_started = time.perf_counter()
        answer, memory_saved = self._finalize_answer(raw_answer)
        postprocess_ms = (time.perf_counter() - postprocess_started) * 1000

        total_ms = (time.perf_counter() - started) * 1000

        response = ChatResponse(
            answer=answer,
            used_memory=search_result.used_memory,
            used_knowledge=search_result.used_knowledge,
            requires_web=search_result.requires_web,
            provider=self.provider_name,
            model=self.router.model_for(role),
            memory_saved=memory_saved,
            timings=ChatTimings(
                search=search_result.timings,
                model_ms=model_ms,
                postprocess_ms=postprocess_ms,
                total_ms=total_ms,
            ),
        )

        yield {
            "type": "final",
            "reply": asdict(response),
        }


chat = ChatService()
