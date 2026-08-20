@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   ClawAI Desktop Build
echo ========================================

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)

echo [1/5] Installing build dependencies...
pip install -q pyinstaller electron-builder

echo [2/5] Building frontend...
cd frontend
npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo [3/5] Building Python backend with PyInstaller...
pyinstaller --clean --onefile ^
    --name backend ^
    --add-data "clawai;clawai" ^
    --hidden-import uvicorn ^
    --hidden-import fastapi ^
    --hidden-import httpx ^
    --hidden-import psutil ^
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

echo [4/5] Packaging with electron-builder...
cd frontend
npm run electron:build:win
if %errorlevel% neq 0 (
    echo [ERROR] electron-builder failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo [5/5] Creating installer with Inno Setup...
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
