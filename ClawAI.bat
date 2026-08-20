@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   ClawAI Desktop
echo ========================================
echo.

if exist "dist\ClawAI.exe" (
    echo [INFO] Opening packaged desktop app: dist\ClawAI.exe
    start "" "dist\ClawAI.exe"
    exit /b 0
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nao encontrado. Instale o Python 3.10+ ou execute o executavel em dist\.
    pause
    exit /b 1
)

echo [INFO] Starting ClawAI from source...
python main.py
pause
