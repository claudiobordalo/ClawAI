"""
AutoStart - Windows startup registration for ClawAI Desktop.

Handles:
- Adding ClawAI to Windows startup registry
- Removing ClawAI from Windows startup
- Checking if ClawAI is registered for startup
"""

import sys
import winreg
from pathlib import Path


class AutoStart:
    """Manages Windows startup registration for ClawAI."""

    REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    REGISTRY_NAME = "ClawAI"

    @staticmethod
    def is_enabled() -> bool:
        """Check if ClawAI is registered for startup."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                AutoStart.REGISTRY_KEY,
                0,
                winreg.KEY_READ,
            )
            try:
                value, _ = winreg.QueryValueEx(key, AutoStart.REGISTRY_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    @staticmethod
    def enable() -> bool:
        """Register ClawAI for startup."""
        try:
            # Get the executable path
            if getattr(sys, "frozen", False):
                # Running as PyInstaller bundle
                exe_path = sys.executable
            else:
                # Running from source
                exe_path = str(Path(__file__).parent.parent / "main.py")

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                AutoStart.REGISTRY_KEY,
                0,
                winreg.KEY_SET_VALUE,
            )
            try:
                winreg.SetValueEx(
                    key,
                    AutoStart.REGISTRY_NAME,
                    0,
                    winreg.REG_SZ,
                    f'"{exe_path}"',
                )
                return True
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            print(f"[AutoStart] Failed to enable: {e}")
            return False

    @staticmethod
    def disable() -> bool:
        """Remove ClawAI from startup."""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                AutoStart.REGISTRY_KEY,
                0,
                winreg.KEY_SET_VALUE,
            )
            try:
                winreg.DeleteValue(key, AutoStart.REGISTRY_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            print(f"[AutoStart] Failed to disable: {e}")
            return False

    @staticmethod
    def get_exe_path() -> str:
        """Get the path to the ClawAI executable."""
        if getattr(sys, "frozen", False):
            return sys.executable
        return str(Path(__file__).parent.parent / "main.py")
