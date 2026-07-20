# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add the current directory to Python path 
sys.path.insert(0, str(Path(__file__).parent))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # Include any binary files if needed
    ],
    datas=[
        # Include frontend static files  
        ('frontend/dist/**/*', 'frontend/dist'),
        
        # Include configuration and environment files 
        ('*.env', '.'),
        ('config.json', '.'), 
        
        # Include all Python modules from clawai package
        ('clawaii/**/*.py', 'clawaii'), 
        ('clawai/**/*.py', 'clawai'),
    ],
    hiddenimports=[
        'httpx._client',
        'uvicorn.main',
        'fastapi',
        'starlette',
        'pywebview.platforms.winforms'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude standard library modules
        'tkinter', 
        'unittest',
        'pdb',
        
        # Exclude test-related packages  
        'pytest',
        '_test*',
        
        # Exclude development tools and debuggers
        'debugpy'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClawAI-Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for desktop app
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
    name='ClawAI-Studio',
)