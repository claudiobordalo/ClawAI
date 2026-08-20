@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   ClawAI Desktop Build
echo   (Python Embedded + Electron)
echo ========================================

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)

echo [1/6] Downloading Python portable (if not exists)...
if not exist "python\python.exe" (
    call build_scripts\download_python.bat
    if %errorlevel% neq 0 (
        echo [ERROR] Python download failed
        pause
        exit /b 1
    )
) else (
    echo [SKIP] Python portable already exists
)

echo [2/6] Installing build dependencies...
pip install -q pyinstaller electron-builder
npm install

echo [3/6] Building frontend...
cd frontend
npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo [4/6] Building Python backend with PyInstaller...
pyinstaller --clean --onefile ^
    --name backend ^
    --add-data "clawai;clawai" ^
    --hidden-import uvicorn ^
    --hidden-import fastapi ^
    --hidden-import httpx ^
    --hidden-import psutil ^
    --hidden-import websockets ^
    --exclude-module tkinter ^
    --exclude-module pytest ^
    --exclude-module jupyter ^
    --exclude-module IPython ^
    main.py
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)

echo [5/6] Packaging with electron-builder...
cd frontend
npm run electron:build:win
if %errorlevel% neq 0 (
    echo [ERROR] electron-builder failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo [6/6] Creating installer with Inno Setup...
if exist "build_scripts\installer.iss" (
    iscc "build_scripts\installer.iss"
    if %errorlevel% equ 0 (
        echo [SUCCESS] Installer created: release\ClawAI-Setup.exe
    )
)

echo ========================================
echo   Build Complete!
echo ========================================
pause
