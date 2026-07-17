"""
ClawAI Desktop Application
==========================
Single executable entry point that:
1. Starts the FastAPI backend as a subprocess
2. Builds or serves the frontend
3. Launches pywebview window
4. Handles lifecycle (start/stop/cleanup)
"""

import argparse
import asyncio
import logging
import os
import platform
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import uvicorn

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_DEV_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("clawai.desktop")


# ---------------------------------------------------------------------------
# Backend management
# ---------------------------------------------------------------------------
class BackendManager:
    """Manages the FastAPI backend lifecycle."""

    def __init__(self, port: int = BACKEND_PORT):
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self.server: uvicorn.Server | None = None
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None

    def start_uvicorn(self) -> None:
        """Start backend using uvicorn in a thread (in-process)."""
        config = uvicorn.Config(
            "main:app",
            host="127.0.0.1",
            port=self.port,
            log_level="info",
            reload=False,
        )
        self.server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self.server.run, daemon=True)
        self._thread.start()
        logger.info(f"Backend started in-process on {self.url}")

    def start_subprocess(self) -> None:
        """Start backend as a separate process."""
        python = sys.executable
        main_py = ROOT_DIR / "main.py"
        self._process = subprocess.Popen(
            [python, str(main_py)],
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0,
        )
        logger.info(f"Backend started as subprocess (PID {self._process.pid}) on {self.url}")

    async def wait_ready(self, timeout: float = 30.0) -> bool:
        """Wait for the backend to respond to /health."""
        import urllib.request
        import urllib.error

        start = time.monotonic()
        while time.monotonic() - start < timeout:
            try:
                req = urllib.request.Request(f"{self.url}/health")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                pass
            await asyncio.sleep(0.5)
        return False

    def stop(self) -> None:
        """Stop the backend."""
        if self.server:
            self.server.should_exit = True
            logger.info("Backend server shutting down...")
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            logger.info("Backend subprocess terminated.")


# ---------------------------------------------------------------------------
# Frontend management
# ---------------------------------------------------------------------------
class FrontendManager:
    """Manages the frontend build and serving."""

    def __init__(self, port: int = FRONTEND_PORT):
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self._process: subprocess.Popen | None = None

    def build(self) -> bool:
        """Build the frontend with Vite."""
        logger.info("Building frontend...")
        frontend_dir = ROOT_DIR / "frontend"
        result = subprocess.run(
            ["npx", "vite", "build"],
            cwd=str(frontend_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"Frontend build failed:\n{result.stderr}")
            return False
        logger.info("Frontend built successfully.")
        return True

    def start_dev_server(self) -> bool:
        """Start Vite dev server as subprocess."""
        logger.info(f"Starting Vite dev server on port {self.port}...")
        frontend_dir = ROOT_DIR / "frontend"
        self._process = subprocess.Popen(
            ["npx", "vite", "--port", str(self.port)],
            cwd=str(frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0,
        )
        # Wait for Vite to be ready
        return asyncio.get_event_loop().run_until_complete(self._wait_ready_dev())

    async def _wait_ready_dev(self, timeout: float = 30.0) -> bool:
        import urllib.request
        import urllib.error

        start = time.monotonic()
        while time.monotonic() - start < timeout:
            try:
                req = urllib.request.Request(self.url)
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                pass
            await asyncio.sleep(0.5)
        return False

    def stop(self) -> None:
        """Stop the Vite dev server."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()


# ---------------------------------------------------------------------------
# WebView management
# ---------------------------------------------------------------------------
class WindowManager:
    """Manages the pywebview window."""

    def __init__(self, title: str = "ClawAI", width: int = 1400, height: int = 900):
        self.title = title
        self.width = width
        self.height = height
        self._window = None

    def show(self, url: str) -> None:
        """Show the application window."""
        import webview

        self._window = webview.create_window(
            self.title,
            url,
            width=self.width,
            height=self.height,
            resizable=True,
            minimizable=True,
            fullscreenable=False,
            text_select=True,
            background="#1e1e2e",  # catppuccin mocha base
        )
        webview.start(
            js_api=None,
            gui="edgechromium",  # WebView2 on Windows
            debug=False,
        )

    def load_html(self, html: str, title: str = "ClawAI") -> None:
        """Show HTML directly (for embedded static build)."""
        import webview

        webview.create_window(
            title,
            html=html,
            width=self.width,
            height=self.height,
            resizable=True,
            minimizable=True,
            background="#1e1e2e",
        )
        webview.start(gui="edgechromium", debug=False)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
async def wait_for_backend(url: str, timeout: float = 30.0) -> bool:
    """Wait for backend /health endpoint."""
    import urllib.request
    import urllib.error

    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="ClawAI Desktop Application")
    parser.add_argument("--dev", action="store_true", help="Run Vite dev server (hot reload)")
    parser.add_argument("--backend-only", action="store_true", help="Only start backend, no UI")
    parser.add_argument("--port", type=int, default=BACKEND_PORT, help="Backend port (default: 8000)")
    parser.add_argument("--width", type=int, default=1400, help="Window width")
    parser.add_argument("--height", type=int, default=900, help="Window height")
    parser.add_argument("--title", default="ClawAI", help="Window title")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("ClawAI Desktop starting...")
    logger.info("=" * 60)

    # 1. Start backend
    backend = BackendManager(port=args.port)
    backend.start_uvicorn()

    # 2. Wait for backend health
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ready = loop.run_until_complete(wait_for_backend(backend.url))
    loop.close()

    if not ready:
        logger.error("Backend failed to start. Aborting.")
        sys.exit(1)

    logger.info(f"Backend is healthy at {backend.url}")

    # 3. Handle --backend-only
    if args.backend_only:
        logger.info("Running in backend-only mode. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        backend.stop()
        return

    # 4. Start frontend
    frontend = FrontendManager()
    if args.dev:
        logger.info("Running in dev mode with Vite hot reload.")
        frontend.start_dev_server()
        app_url = frontend.url
    else:
        # Build frontend and serve from dist
        if not frontend.build():
            logger.error("Frontend build failed. Falling back to dev mode.")
            frontend.start_dev_server()
            app_url = frontend.url
        else:
            app_url = f"file://{FRONTEND_DIST / 'index.html'}"
            logger.info(f"Serving built frontend from {app_url}")

    # 5. Show window
    window = WindowManager(title=args.title, width=args.width, height=args.height)
    window.show(app_url)

    # 6. Cleanup on exit
    backend.stop()
    frontend.stop()
    logger.info("ClawAI Desktop shut down.")


if __name__ == "__main__":
    main()
