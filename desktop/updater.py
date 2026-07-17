"""
Updater - Update checker for ClawAI Desktop.

Handles:
- Checking for new versions on GitHub
- Downloading updates
- Applying updates
"""

import os
import sys
import json
import hashlib
import logging
import tempfile
import threading
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger("clawai.updater")


class Updater:
    """Manages application updates for ClawAI Desktop."""

    GITHUB_REPO = "ClawAI/ClawAI"  # Placeholder - update to actual repo
    GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    APP_NAME = "ClawAI"

    def __init__(self, current_version: str = "1.0.0"):
        self.current_version = current_version
        self._latest_release = None
        self._download_url = None
        self._download_path = None

    async def check_for_updates(self) -> Optional[dict]:
        """Check for new versions on GitHub."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    self.GITHUB_API,
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code != 200:
                    logger.warning(f"Failed to check updates: HTTP {resp.status_code}")
                    return None

                releases = resp.json()
                if not releases:
                    return None

                # Find the latest stable release
                for release in releases:
                    if release.get("prerelease"):
                        continue
                    tag = release.get("tag_name", "")
                    if tag and tag > self.current_version:
                        self._latest_release = release
                        # Find the .exe asset
                        for asset in release.get("assets", []):
                            if asset.get("name", "").endswith(".exe"):
                                self._download_url = asset["browser_download_url"]
                                break
                        return {
                            "version": tag,
                            "name": release.get("name", tag),
                            "notes": release.get("body", ""),
                            "download_url": self._download_url,
                            "published_at": release.get("published_at"),
                        }

                return None  # No update available

        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return None

    async def download_update(self) -> Optional[str]:
        """Download the latest update."""
        if not self._download_url:
            return None

        self._download_path = Path(tempfile.gettempdir()) / f"{self.APP_NAME}_update.exe"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("GET", self._download_url) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("content-length", 0))
                    downloaded = 0

                    with open(self._download_path, "wb") as f:
                        async for chunk in resp.aiter_chunk(8192):
                            f.write(chunk)
                            downloaded += len(chunk)

            logger.info(f"Update downloaded: {self._download_path}")
            return str(self._download_path)

        except Exception as e:
            logger.error(f"Update download failed: {e}")
            if self._download_path and self._download_path.exists():
                self._download_path.unlink()
            return None

    def apply_update(self) -> bool:
        """Apply the downloaded update."""
        if not self._download_path or not self._download_path.exists():
            return False

        try:
            # Run the installer silently
            import subprocess
            subprocess.Popen(
                [str(self._download_path), "/S"],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except Exception as e:
            logger.error(f"Update apply failed: {e}")
            return False

    def get_update_status(self) -> dict:
        """Get the current update status."""
        return {
            "current_version": self.current_version,
            "latest_version": self._latest_release.get("tag_name") if self._latest_release else None,
            "has_update": self._latest_release is not None,
            "download_path": str(self._download_path) if self._download_path else None,
        }
