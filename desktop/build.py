"""
ClawAI Desktop Build Script
============================
Builds the frontend and creates the standalone .exe via PyInstaller.

Usage:
    python desktop/build.py              # Build everything
    python desktop/build.py --frontend   # Only build frontend
    python desktop/build.py --exe        # Only build .exe
    python desktop/build.py --clean      # Clean build artifacts
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DESKTOP_DIR = ROOT_DIR / "desktop"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
SPEC_FILE = DESKTOP_DIR / "clawai.spec"
EXE_NAME = "ClawAI"


def log(msg: str) -> None:
    print(f"[build] {msg}")


def build_frontend() -> bool:
    """Build the React frontend with Vite."""
    log("Building frontend...")
    result = subprocess.run(
        [sys.executable, "-m", "vite", "build"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
    )
    # Fallback: try npx
    if result.returncode != 0:
        result = subprocess.run(
            ["npx", "vite", "build"],
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        log(f"Frontend build failed:\n{result.stderr}")
        return False
    log("Frontend built successfully.")
    return True


def clean() -> None:
    """Remove build artifacts."""
    log("Cleaning build artifacts...")
    for d in [BUILD_DIR, DIST_DIR]:
        if d.exists():
            shutil.rmtree(d)
    # Clean frontend dist
    frontend_dist = FRONTEND_DIR / "dist"
    if frontend_dist.exists():
        shutil.rmtree(frontend_dist)
    # Clean .exe
    exe_path = ROOT_DIR / f"{EXE_NAME}.exe"
    if exe_path.exists():
        exe_path.unlink()
    log("Clean complete.")


def build_exe() -> bool:
    """Build the .exe with PyInstaller."""
    log("Building .exe with PyInstaller...")
    result = subprocess.run(
        ["pyinstaller", "--clean", str(SPEC_FILE)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log(f"PyInstaller failed:\n{result.stderr}")
        return False
    log(f".exe built successfully: {ROOT_DIR / EXE_NAME}.exe")
    return True


def main():
    parser = argparse.ArgumentParser(description="ClawAI Desktop Build")
    parser.add_argument("--frontend", action="store_true", help="Only build frontend")
    parser.add_argument("--exe", action="store_true", help="Only build .exe")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--all", action="store_true", help="Build everything (default)")
    args = parser.parse_args()

    if args.clean:
        clean()
        return

    if args.frontend or args.all:
        if not build_frontend():
            sys.exit(1)

    if args.exe or args.all:
        # Ensure frontend is built first
        if not (FRONTEND_DIR / "dist").exists():
            if not build_frontend():
                sys.exit(1)
        if not build_exe():
            sys.exit(1)

    log("Done!")


if __name__ == "__main__":
    main()
