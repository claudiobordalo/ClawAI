from __future__ import annotations

import argparse
import re

from clawai.prompts import PromptEngine
from clawai.providers.factory import ProviderFactory
from clawai.workspace.services.file_locator import FileLocator
from clawai.workspace.services.code_extractor import CodeExtractor


class ChatSession:

    def __init__(
        self,
        project: str,
    ) -> None:

        self.project = project
        self.provider = ProviderFactory.create(provider="ollama")
        self.engine = PromptEngine(self.provider)
        self.locator = FileLocator()
        self.extractor = CodeExtractor()

    def ask(
        self,
        question: str,
    ) -> None:

        symbols = re.findall(
            r"[A-Z][A-Za-z0-9_]+",
            question,
        )

        symbol = symbols[0] if symbols else ""

        files = self.locator.find(
            self.project,
            question,
            limit=1,
        )

        if not files:
            print("Nenhum arquivo encontrado.")
            return

        code = self.extractor.extract(
            files[0],
            symbol,
        )

        prompt = f"""
Responda SOMENTE utilizando o código abaixo.

Arquivo:
{files[0].name}

Código:

{code}

Pergunta:
{question}
"""

        print()
        print(self.engine.execute("system", prompt))
        print()


def main():

    parser = argparse.ArgumentParser(prog="claw")

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    chat = sub.add_parser("chat")
    chat.add_argument("project")

    ask = sub.add_parser("ask")
    ask.add_argument("project")
    ask.add_argument("question")

    args = parser.parse_args()

    if args.command == "ask":

        ChatSession(
            args.project
        ).ask(
            args.question
        )

        return

    if args.command == "chat":

        session = ChatSession(
            args.project
        )

        print("ClawAI Chat")
        print("Digite 'exit' para sair.\n")

        while True:

            question = input("> ").strip()

            if question.lower() in {
                "exit",
                "quit",
            }:
                break

            if not question:
                continue

            session.ask(question)


if __name__ == "__main__":
    main()
