"""
desktop_tray.py – Optional system-tray icon for ClawAI Studio.

Provides a pystray-based tray menu (Show / Hide / Quit).
This module is imported lazily; if pystray or Pillow are missing,
the desktop app still works without the tray icon.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("clawai.desktop.tray")


def create_desktop_icon(window) -> object:  # noqa: ANN201 — returns pystray.Icon or None.
    """Create a system-tray icon for ClawAI Studio (optional)."""
    try:
        import pystray   # type: ignore[import-not-found]

        def on_show(icon, item):  # noqa: ARG001
            window.show()

        def on_hide(icon, item):  # noqa: ARG001
            window.hide()

        def _on_quit(icon, item):    # noqa: ANN202 — pystray callback signature.
            import sys as _sys   # type: ignore[import-not-found]
            _sys.exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Show ClawAI", on_show),
            pystray.MenuItem("Hide ClawAI", on_hide),
            pystray.Menu.Separator(),
            pystray.MenuItem("Quit", _on_quit),
        )

    except ImportError as exc:       # noqa: PERF203
        logger.info("pystray not installed — tray icon disabled (%s)", exc)
        return None  # type: ignore[return-value]

    # Try to load an icon file. Returns the menu if no icon is found.
    for candidate in [Path(__file__).parent.parent / "frontend" / "public" / "icon.ico"]:   # type: ignore[name-defined] — __file__ works at runtime.
        if not candidate.exists():
            logger.info("No icon file found; running without system-tray icon.")
            return pystray.Icon(  # noqa: F821, type: ignore[return-value]
                name="ClawAI", title="ClawAI Studio", menu=menu,
            )

        try:
            from PIL import Image as _Image  # noqa: TID251, F401 — lazy-import to avoid hard dep on Pillow for headless builds.
        except ImportError as exc:       # noqa: PERF203
            logger.warning("Pillow not installed — tray icon disabled (%s)", exc)
            return pystray.Icon(  # type: ignore[return-value]
                name="ClawAI", title="ClawAI Studio", menu=menu,
            )

        img = _Image.open(str(candidate))
        resized_img = img.resize((64, 64), getattr(_Image.Resampling, "LANCZOS", _Image.ANTIALIAS))   # type: ignore[attr-defined]

    app_icon = pystray.Icon(  # noqa: F841 — caller uses it.
        name="ClawAI", image=resized_img,   # type: ignore[name-defined]
        title="ClawAI Studio", menu=menu,
    )
    return app_icon
