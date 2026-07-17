"""
System tray module for ClawAI Desktop.

Provides a native Windows system tray with:
- Show/hide window
- Reload frontend
- Settings
- Model management
- Quit
"""

from .tray_manager import SystemTray

__all__ = ["SystemTray"]
