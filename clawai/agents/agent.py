from __future__ import annotations

from clawai.ai.router import AIRouter
from clawai.memory.memory import memory


class Agent:

    category = "general"
    system_prompt = ""

    def __init__(self) -> None:

        self.router = AIRouter()

    def ask(
        self,
        prompt: str,
    ) -> str:

        memories = memory.search(
            self.category,
            prompt,
            limit=5,
        )

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

        answer = self.router.ask(final_prompt)

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

                answer = answer.split("<MEMORY>")[0].strip()

            except Exception:
                pass

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
