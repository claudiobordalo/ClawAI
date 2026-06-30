from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

from clawai.ai.router import AIRouter, ModelRole
from clawai.documents.reader import documents
from clawai.memory.memory import memory
from clawai.search.search_engine import SearchResult, SearchTimings, search


SYSTEM_PROMPT = """
Você é o ClawAI, um agente de desenvolvimento dentro do próprio projeto.

Quando o pedido envolver a interface, backend, arquivos, workspace ou automação,
responda como agente de implementação: diga o que será alterado, em quais arquivos,
e qual será o próximo passo.

Não diga que “não pode alterar a interface” ou que “não tem controle” sobre o projeto.
Quando for um pedido de desenvolvimento, trate como tarefa do repositório atual.

Se houver erro técnico, explique o erro real e a correção provável.
Se a resposta exigir edição de código, seja direto e objetivo.
""".strip()


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
        self.model_name = self.router.model_for(ModelRole.DEFAULT)

    def _prepare_prompt(
        self,
        prompt: str,
        file: str | None = None,
    ) -> tuple[str, SearchResult]:
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

        search_result = search.build_prompt(prompt)

        model_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{search_result.prompt}"
        )

        return model_prompt, search_result

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

    def ask(
        self,
        prompt: str,
        file: str | None = None,
    ) -> ChatResponse:
        started = time.perf_counter()

        model_prompt, search_result = self._prepare_prompt(prompt, file)

        model_started = time.perf_counter()
        raw_answer = self.router.ask(model_prompt)
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
            model=self.model_name,
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

        model_prompt, search_result = self._prepare_prompt(prompt, file)

        model_started = time.perf_counter()
        chunks: list[str] = []
        emitted = ""

        for chunk in self.router.stream(model_prompt):
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
            model=self.model_name,
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