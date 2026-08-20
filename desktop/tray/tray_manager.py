"""
SystemTray - Windows system tray manager for ClawAI Desktop.

Provides a native Windows tray icon with context menu for:
- Show/Hide main window
- Reload frontend
- Open settings
- Open model manager
- Quit application
"""

import os
import sys
import threading
import win32con
import win32gui
import win32api
import win32menu
from pathlib import Path
from typing import Callable, Optional

import pystray
from PIL import Image


class SystemTray:
    """Manages the Windows system tray icon and menu for ClawAI."""

    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_hide: Optional[Callable] = None,
        on_reload: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        icon_path: Optional[str] = None,
    ):
        self.on_show = on_show
        self.on_hide = on_hide
        self.on_reload = on_reload
        self.on_settings = on_settings
        self.on_quit = on_quit
        self.tray = None
        self._window_id = None

        # Find icon
        if icon_path and Path(icon_path).exists():
            self.icon_path = icon_path
        else:
            # Try to find icon in resources
            self.icon_path = None
            for candidate in [
                Path(__file__).parent.parent.parent / "assets" / "icon.png",
                Path(__file__).parent.parent.parent / "icon.ico",
                Path(__file__).parent / "icon.ico",
            ]:
                if candidate.exists():
                    self.icon_path = str(candidate)
                    break

    def _get_default_icon(self) -> Image.Image:
        """Create a default icon if none is available."""
        # Create a simple 64x64 icon with ClawAI branding
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        # Draw a circle
        for x in range(64):
            for y in range(64):
                if (x - 32) ** 2 + (y - 32) ** 2 <= 30 ** 2:
                    img.putpixel((x, y), (30, 64, 155, 255))
        return img

    def _on_click(self, icon, item):
        """Handle tray menu item clicks."""
        if item == "Show":
            if self.on_show:
                self.on_show()
        elif item == "Hide":
            if self.on_hide:
                self.on_hide()
        elif item == "Reload":
            if self.on_reload:
                self.on_reload()
        elif item == "Settings":
            if self.on_settings:
                self.on_settings()
        elif item == "Models":
            if self.on_settings:
                self.on_settings()
        elif item == "Quit":
            if self.on_quit:
                self.on_quit()
            icon.stop()

    def _build_menu(self):
        """Build the tray context menu."""
        return pystray.Menu(
            pystray.MenuItem("Show", lambda i: self._on_click(i, "Show")),
            pystray.MenuItem("Hide", lambda i: self._on_click(i, "Hide")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Reload", lambda i: self._on_click(i, "Reload")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", lambda i: self._on_click(i, "Settings")),
            pystray.MenuItem("Models", lambda i: self._on_click(i, "Models")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda i: self._on_click(i, "Quit")),
        )

    def start(self, window_id: Optional[int] = None):
        """Start the system tray."""
        self._window_id = window_id
        icon = pystray.Icon(
            "clawai",
            self._get_default_icon() if not self.icon_path else None,
            "ClawAI Studio",
            menu=self._build_menu(),
        )

        if self.icon_path and Path(self.icon_path).exists():
            try:
                icon.icon = Image.open(self.icon_path)
            except Exception:
                pass

        self.tray = icon
        threading.Thread(target=icon.run, daemon=True).start()

    def stop(self):
        """Stop the system tray."""
        if self.tray:
            self.tray.stop()
            self.tray = None

    def hide_window(self):
        """Hide the main window."""
        if self._window_id:
            try:
                win32gui.ShowWindow(self._window_id, win32con.SW_HIDE)
            except Exception:
                pass

    def show_window(self):
        """Show the main window."""
        if self._window_id:
            try:
                win32gui.ShowWindow(self._window_id, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(self._window_id)
            except Exception:
                pass
