"""
ClawAI – Entry point.

Starts the desktop application (FastAPI + PyWebView) by default,
or runs in CLI mode when ``CLAWAI_MODE=cli`` is set.
The same code path works both during development and inside a PyInstaller bundle.
"""
import os
import sys
from pathlib import Path


def _ensure_paths() -> None:
    """Ensure the project root is on sys.path so imports work from any CWD."""
    script_dir = Path(__file__).resolve().parent.parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))


_ensure_paths()

# ── Mode selection (default → desktop) ────────────────────────
_MODE = os.environ.get("CLAWAI_MODE", "desktop")

if _MODE == "cli":
    # Legacy CLI mode — kept for backward compatibility.
    from clawai.application import create_application  # noqa: E402

    app = None
    try:
        app = create_application()
        app.start()
    except KeyboardInterrupt:
        pass
else:
    # Desktop mode (default) – FastAPI + PyWebView.
    from clawai.desktop_server import start_desktop  # noqa: E402

    try:
        start_desktop()
    except KeyboardInterrupt:
        pass

