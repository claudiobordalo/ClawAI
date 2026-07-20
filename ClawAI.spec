# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for ClawAI Desktop.

Build (single-file):
    pyinstaller --clean --onefile ClawAI.spec

Build (single-directory — default in this file):
    pyinstaller --clean ClawAI.spec
"""

import os
from pathlib import Path

block_cipher = None

# ── Data files to embed ────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent          # project root
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"        # React build output
DIST_DEST  = os.path.join("frontend", "dist")         # destination inside bundle

a_datas = [
    (str(FRONTEND_DIST), DIST_DEST) if FRONTEND_DIST.exists() else None,
]
# Filter out the None entry in case dist doesn't exist yet.
a_datas = [d for d in a_datas if d is not None]

a = Analysis(
    ["main.py"],                                        # entry point (will be inside bundle root)
    pathex=[],                                          # nothing extra needed
    binaries=[],
    datas=a_datas,                                      # React static assets
    hiddenimports=[
        "uvicorn",
        "fastapi",
        "httpx",
        "psutil",
        "webview",
        "clawai.main",
        "clawai.server",
        "clawai.bootstrap",
        "clawai.desktop_server",
        # FastAPI runtime deps
        "starlette.middleware.cors",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "pytest",
        "sphinx",
        "jupyter",
        "IPython",
        "_pyrepl",
        "test",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

# ── Single-file EXE (uncomment for --onefile builds) ───────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ClawAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                         # compress bootloaders with UPX when available
    console=False,                    # no terminal window (desktop app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
