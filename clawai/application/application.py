import sys
import os
import threading
import http.server
from functools import partial
from pathlib import Path
import webview

from clawai.ai import ModelRole
from clawai.ai import ModelRouter
from clawai.prompts import PromptEngine
from clawai.providers.factory import ProviderFactory
from clawai.providers.implementations.ollama_provider import OllamaProvider
from clawai.providers.implementations.openai_provider import OpenAIProvider


class Application:

    def __init__(
        self,
        model_router: ModelRouter | None = None,
    ) -> None:
        # ProviderFactory é a fonte única da disponibilidade de providers.
        # A registration acontece durante o bootstrap da Application, antes
        # de qualquer chamada a ModelRouter.provider_for().
        ProviderFactory.register_provider("ollama", OllamaProvider)
        ProviderFactory.register_provider("openai", OpenAIProvider)

        self._model_router = model_router or ModelRouter()

        self._prompt_engine = PromptEngine(
            self._model_router.provider_for(ModelRole.CODER)
        )

    @property
    def prompt_engine(
        self,
    ) -> PromptEngine:
        return self._prompt_engine

    @property
    def model_router(
        self,
    ) -> ModelRouter:
        return self._model_router

    def start(self):
        """Inicia a interface gráfica da aplicação."""
        if getattr(sys, 'frozen', False):
            # Se estiver rodando como executável (PyInstaller)
            base_path = Path(sys._MEIPASS)
        else:
            # Se estiver rodando como script
            base_path = Path(__file__).resolve().parent.parent

        frontend_path = base_path / 'frontend' / 'dist'
        if not frontend_path.exists():
            raise FileNotFoundError(f"Frontend não encontrado em: {frontend_path}")

        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(frontend_path))

        class ReusableThreadingHTTPServer(http.server.ThreadingHTTPServer):
            allow_reuse_address = True

        httpd = ReusableThreadingHTTPServer(("127.0.0.1", 8080), handler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        try:
            webview.create_window('ClawAI', 'http://127.0.0.1:8080')
            webview.start()
        finally:
            httpd.shutdown()
            httpd.server_close()


def create_application() -> "Application":
    return Application()
