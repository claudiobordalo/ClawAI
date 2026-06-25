from __future__ import annotations

from dataclasses import dataclass

from clawai.ai.router import AIRouter
from clawai.knowledge.knowledge import knowledge
from clawai.memory.memory import memory


@dataclass
class SearchResult:

    answer: str
    used_memory: bool
    used_knowledge: bool
    requires_web: bool


class SearchEngine:

    def __init__(self) -> None:

        self.router = AIRouter()

    def ask(
        self,
        question: str,
        category: str = "general",
    ) -> SearchResult:

        memories = memory.search(
            category=category,
            query=question,
            limit=5,
        )

        docs = knowledge.search(question)

        requires_web = (
            len(memories) == 0
            and len(docs) == 0
        )

        prompt = ""

        if memories:

            prompt += "MEMÓRIA:\n\n"

            for item in memories:

                prompt += (
                    f"- {item['title']}: "
                    f"{item['content']}\n"
                )

            prompt += "\n"

        if docs:

            prompt += "BASE DE CONHECIMENTO:\n\n"

            for doc in docs[:3]:

                prompt += (
                    f"Tópico: {doc['topic']}\n\n"
                    f"{doc['content'][:4000]}\n\n"
                )

        if requires_web:

            prompt += """
Não existe conhecimento suficiente para responder.

Explique que será necessária uma pesquisa na internet.
Não invente informações.
"""

        prompt += f"""

Pergunta:

{question}
"""

        answer = self.router.ask(prompt)

        return SearchResult(
            answer=answer,
            used_memory=bool(memories),
            used_knowledge=bool(docs),
            requires_web=requires_web,
        )


search = SearchEngine()
