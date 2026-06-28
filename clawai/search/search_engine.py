from __future__ import annotations

import time
from dataclasses import dataclass, field

from clawai.ai.router import AIRouter
from clawai.knowledge.knowledge import knowledge
from clawai.memory.memory import memory


@dataclass(slots=True, frozen=True)
class SearchTimings:
    memory_ms: float = 0.0
    knowledge_ms: float = 0.0
    prompt_ms: float = 0.0
    total_ms: float = 0.0


@dataclass(slots=True, frozen=True)
class SearchResult:
    prompt: str = ""
    answer: str = ""
    used_memory: bool = False
    used_knowledge: bool = False
    requires_web: bool = False
    timings: SearchTimings = field(default_factory=SearchTimings)


class SearchEngine:
    def __init__(self) -> None:
        self.router = AIRouter()

    def build_prompt(
        self,
        question: str,
        category: str = "general",
    ) -> SearchResult:
        started = time.perf_counter()

        memory_started = time.perf_counter()
        memories = memory.search(
            category=category,
            query=question,
            limit=5,
        )
        memory_ms = (time.perf_counter() - memory_started) * 1000

        knowledge_started = time.perf_counter()
        docs = knowledge.search(question)
        knowledge_ms = (time.perf_counter() - knowledge_started) * 1000

        requires_web = (
            len(memories) == 0
            and len(docs) == 0
        )

        prompt_started = time.perf_counter()
        parts: list[str] = []

        if memories:
            parts.append("MEMÓRIA:\n\n")

            for item in memories:
                parts.append(
                    f"- {item['title']}: {item['content']}\n"
                )

            parts.append("\n")

        if docs:
            parts.append("BASE DE CONHECIMENTO:\n\n")

            for doc in docs[:3]:
                parts.append(
                    f"Tópico: {doc['topic']}\n\n"
                    f"{doc['content'][:4000]}\n\n"
                )

        if requires_web:
            parts.append(
                """
Não existe conhecimento suficiente para responder.

Explique que será necessária uma pesquisa na internet.
Não invente informações.
"""
            )

        parts.append(f"\nPergunta:\n\n{question}\n")

        prompt = "".join(parts)
        prompt_ms = (time.perf_counter() - prompt_started) * 1000
        total_ms = (time.perf_counter() - started) * 1000

        return SearchResult(
            prompt=prompt,
            used_memory=bool(memories),
            used_knowledge=bool(docs),
            requires_web=requires_web,
            timings=SearchTimings(
                memory_ms=memory_ms,
                knowledge_ms=knowledge_ms,
                prompt_ms=prompt_ms,
                total_ms=total_ms,
            ),
        )

    def ask(
        self,
        question: str,
        category: str = "general",
    ) -> SearchResult:
        build = self.build_prompt(question, category)

        started = time.perf_counter()
        answer = self.router.ask(build.prompt)
        model_ms = (time.perf_counter() - started) * 1000

        return SearchResult(
            prompt=build.prompt,
            answer=answer,
            used_memory=build.used_memory,
            used_knowledge=build.used_knowledge,
            requires_web=build.requires_web,
            timings=SearchTimings(
                memory_ms=build.timings.memory_ms,
                knowledge_ms=build.timings.knowledge_ms,
                prompt_ms=build.timings.prompt_ms,
                total_ms=build.timings.total_ms + model_ms,
            ),
        )


search = SearchEngine()