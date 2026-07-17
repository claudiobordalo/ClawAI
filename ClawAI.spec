# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para ClawAI Studio.

Build:
    pyinstaller ClawAI.spec

Output:
    dist/ClawAI/ClawAI.exe  (single directory)
    dist/ClawAI.exe          (via build_exe.py single-file)
"""

import os
from pathlib import Path

block_cipher = None

# ──────────────────────────────────────────────
# Data files to include
# ──────────────────────────────────────────────

# Frontend dist (if exists)
frontend_dist = Path("frontend/dist")
datas = [
    ("configs", "configs"),
    ("database", "database"),
    ("clawai", "clawai"),
]
if frontend_dist.exists():
    datas.append(("frontend/dist", "frontend/dist"))

# ──────────────────────────────────────────────
# Analysis
# ──────────────────────────────────────────────

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # FastAPI + Uvicorn
        'uvicorn',
        'uvicorn.config',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'fastapi',
        'fastapi.middleware.cors',
        'fastapi.responses',
        'fastapi.staticfiles',
        'pydantic',
        'pydantic.networks',
        # HTTP clients
        'httpx',
        'httpx._config',
        'httpx._client',
        'httpcore',
        'httpcore._async',
        'httpcore.backends.auto',
        # Desktop
        'webview',
        'webview.platforms',
        'webview.util',
        'webbrowser',
        # System
        'psutil',
        # Internal modules
        'clawai.api.tools_api',
        'clawai.autopilot',
        'clawai.autonomy.proactive',
        'clawai.chat.chat_service',
        'clawai.workspaces',
        'clawai.desktop_server',
        'clawai.server',
        'clawai.main',
        'clawai.bootstrap',
        'clawai.config',
        'clawai.config.config_manager',
        'clawai.config.settings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'pytest',
        'sphinx',
        'setuptools',
        'jupyter',
        'notebook',
        'IPython',
        'matplotlib',
        'scipy',
        'numpy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single-directory build (default)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClawAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClawAI',
)
