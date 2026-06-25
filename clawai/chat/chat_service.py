from __future__ import annotations

from pathlib import Path

from clawai.agents.agent import GeneralAgent
from clawai.documents.reader import documents
from clawai.search.search_engine import search


class ChatService:

    def __init__(self) -> None:

        self.agent = GeneralAgent()

    def ask(
        self,
        prompt: str,
        file: str | None = None,
    ) -> str:

        if file:

            path = Path(file)

            if not path.exists():
                raise FileNotFoundError(path)

            content = documents.read(path)

            prompt = f"""
Arquivo enviado:

Nome:
{path.name}

Conteúdo:

{content}

Pergunta do usuário:

{prompt}
"""

        result = search.ask(prompt)

        if result.requires_web:

            prompt = f"""
Caso o conhecimento não seja suficiente,
responda utilizando seu conhecimento atual e
explique onde há incerteza.

Pergunta:

{prompt}
"""

        return self.agent.ask(prompt)


chat = ChatService()
