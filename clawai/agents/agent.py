from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from clawai.ai.router import AIRouter
from clawai.memory.memory import memory


@dataclass(slots=True, frozen=True)
class AgentTimings:
    memory_ms: float = 0.0
    prompt_ms: float = 0.0
    model_ms: float = 0.0
    postprocess_ms: float = 0.0
    total_ms: float = 0.0


@dataclass(slots=True, frozen=True)
class AgentResult:
    answer: str = ""
    timings: AgentTimings = field(default_factory=AgentTimings)
    memory_hits: int = 0
    memory_saved: bool = False


class Agent:
    category = "general"
    system_prompt = ""

    def __init__(self) -> None:
        self.router = AIRouter()

    def ask(
        self,
        prompt: str,
        include_metrics: bool = False,
    ) -> str | AgentResult:
        started = time.perf_counter()

        memory_started = time.perf_counter()
        memories = memory.search(
            self.category,
            prompt,
            limit=5,
        )
        memory_ms = (time.perf_counter() - memory_started) * 1000

        prompt_started = time.perf_counter()
        context = ""

        if memories:
            context = "Conhecimento acumulado:\n\n"

            for item in memories:
                context += (
                    f"Título: {item['title']}\n"
                    f"Conteúdo: {item['content']}\n\n"
                )

        final_prompt = f"""
{self.system_prompt}

{context}

Pergunta do usuário:

{prompt}

Se utilizar alguma informação nova que mereça ser lembrada futuramente,
termine sua resposta exatamente com:

<MEMORY>
titulo: ...
conteudo: ...
</MEMORY>

Caso contrário, não utilize essa marcação.
"""
        prompt_ms = (time.perf_counter() - prompt_started) * 1000

        model_started = time.perf_counter()
        answer = self.router.ask(final_prompt)
        model_ms = (time.perf_counter() - model_started) * 1000

        postprocess_started = time.perf_counter()
        memory_saved = False

        if "<MEMORY>" in answer and "</MEMORY>" in answer:
            try:
                block = answer.split("<MEMORY>")[1].split("</MEMORY>")[0]

                title = ""
                content = ""

                for line in block.splitlines():
                    if line.lower().startswith("titulo:"):
                        title = line.split(":", 1)[1].strip()

                    if line.lower().startswith("conteudo:"):
                        content = line.split(":", 1)[1].strip()

                if title and content:
                    memory.add(
                        category=self.category,
                        title=title,
                        content=content,
                        source="agent",
                    )
                    memory_saved = True

                answer = answer.split("<MEMORY>")[0].strip()

            except Exception:
                pass

        postprocess_ms = (time.perf_counter() - postprocess_started) * 1000
        total_ms = (time.perf_counter() - started) * 1000

        if include_metrics:
            return AgentResult(
                answer=answer,
                timings=AgentTimings(
                    memory_ms=memory_ms,
                    prompt_ms=prompt_ms,
                    model_ms=model_ms,
                    postprocess_ms=postprocess_ms,
                    total_ms=total_ms,
                ),
                memory_hits=len(memories),
                memory_saved=memory_saved,
            )

        return answer


class GeneralAgent(Agent):
    category = "general"

    system_prompt = """
Você é o ClawAI.

Você é um assistente geral.

Pode responder sobre programação, saúde, alimentação, jogos,
Windows, Linux, SAP, Dofus, GTA, estudos e qualquer outro assunto.

Quando aprender algo que provavelmente será útil novamente para este
usuário, grave apenas UMA memória resumida.

Nunca grave informações temporárias, conversas casuais ou fatos públicos.
"""