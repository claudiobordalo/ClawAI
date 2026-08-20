"""
Gerenciamento do servidor backend (FastAPI + uvicorn).

Inicia/para o servidor, detecta portas disponíveis,
e expõe utilitários para comunicação com o frontend.
"""

import subprocess
import sys
import time
import socket
import os
import platform
from pathlib import Path
from contextlib import contextmanager


def find_free_port(start: int = 8000, max_attempts: int = 100) -> int:
    """Encontra uma porta TCP livre começando de `start`."""
    for port in range(start, start + max_attempts):
        if not _is_port_in_use(port):
            return port
    raise RuntimeError(f"Nenhuma porta livre encontrada em {start}-{start + max_attempts}")


def _is_port_in_use(port: int) -> bool:
    """Verifica se uma porta já está em uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


class BackendServer:
    """Controla o ciclo de vida do servidor FastAPI."""

    def __init__(self, root_dir: Path | None = None):
        self.root_dir = root_dir or self._find_root()
        self.server_process: subprocess.Popen | None = None
        self.port: int = 8000
        self._base_url: str = ""

    def _find_root(self) -> Path:
        """Tenta encontrar o diretório raiz do ClawAI."""
        # Tenta o diretório pai do desktop
        candidates = [
            Path(__file__).parent.parent,
            Path(__file__).parent / "..",
            Path.cwd(),
        ]
        for candidate in candidates:
            resolved = candidate.resolve()
            if (resolved / "backend" / "main.py").exists():
                return resolved
        return Path.cwd()

    @property
    def backend_dir(self) -> Path:
        return self.root_dir / "backend"

    @property
    def api_url(self) -> str:
        return self._base_url

    @property
    def ws_url(self) -> str:
        return self._base_url.replace("http://", "ws://")

    def start(self, timeout: float = 15.0) -> str:
        """
        Inicia o servidor FastAPI.
        Retorna a URL base da API.
        """
        # Verifica se já está rodando
        if self.server_process and self.server_process.poll() is None:
            return self._base_url

        # Encontra porta livre
        self.port = find_free_port(8000)
        self._base_url = f"http://localhost:{self.port}"

        # Verifica se o diretório backend existe
        main_py = self.backend_dir / "main.py"
        if not main_py.exists():
            raise FileNotFoundError(
                f"backend/main.py não encontrado em {self.backend_dir}. "
                "Certifique-se de que o ClawAI está instalado corretamente."
            )

        # Verifica dependências
        self._check_dependencies()

        # Inicia o processo
        python = sys.executable
        env = os.environ.copy()
        env["CLAWAI_DESKTOP"] = "1"
        env.setdefault("PYTHONUNBUFFERED", "1")

        self.server_process = subprocess.Popen(
            [
                python, "-m", "uvicorn",
                "main:app",
                "--host", "127.0.0.1",
                "--port", str(self.port),
                "--log-level", "info",
            ],
            cwd=str(self.backend_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Espera o servidor ficar disponível
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not _is_port_in_use(self.port):
                time.sleep(0.1)
                continue
            if self.server_process.poll() is not None:
                stdout = self.server_process.stdout.read() if self.server_process.stdout else ""
                raise RuntimeError(
                    f"Servidor backend falhou ao iniciar.\n{stdout}"
                )
            # Testa conexão
            try:
                with socket.create_connection(("localhost", self.port), timeout=1) as s:
                    s.close()
                    return self._base_url
            except OSError:
                pass
            time.sleep(0.2)

        raise RuntimeError(f"Timeout: servidor não respondeu em {timeout}s")

    def stop(self):
        """Para o servidor backend."""
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
        self.server_process = None
        self._base_url = ""

    def is_running(self) -> bool:
        return (
            self.server_process is not None
            and self.server_process.poll() is None
        )

    def _check_dependencies(self):
        """Verifica se as dependências do backend estão instaladas."""
        import importlib
        required = ["fastapi", "uvicorn", "pydantic", "starlette"]
        missing = []
        for pkg in required:
            try:
                importlib.import_module(pkg)
            except ImportError:
                missing.append(pkg)
        if missing:
            raise RuntimeError(
                f"Dependências ausentes: {', '.join(missing)}. "
                f"Execute: pip install {' '.join(missing)}"
            )


# Singleton global
_server_instance: BackendServer | None = None


def get_server(root_dir: Path | None = None) -> BackendServer:
    global _server_instance
    if _server_instance is None:
        _server_instance = BackendServer(root_dir)
    return _server_instance


def reset_server():
    global _server_instance
    if _server_instance:
        _server_instance.stop()
    _server_instance = None
