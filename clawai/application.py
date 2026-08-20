from __future__ import annotations

from clawai.bootstrap import build_container
from clawai.core.container import ServiceContainer
from clawai.chat.chat_service import ChatService
from clawai.ai.router import AIRouter


class Application:
    """Unified application entry point."""

    def __init__(self) -> None:
        self.container: ServiceContainer = build_container()
        self.chat_service: ChatService = self.container.resolve(ChatService)
        self.router: AIRouter = self.container.resolve(AIRouter)

    def start(self) -> None:
        print("ClawAI Application Started.")
        # Start CLI or API server here
        self._run_cli()

    def _run_cli(self) -> None:
        while True:
            try:
                prompt = input("\n> ")
                if prompt.lower() in ('exit', 'quit'):
                    break
                response = self.chat_service.ask(prompt)
                print(f"\n{response.answer}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


def create_application() -> Application:
    return Application()
