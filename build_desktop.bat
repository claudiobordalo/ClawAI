@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo   ClawAI Studio - Build Desktop
echo ========================================
echo.

REM Verificar se o Python está disponível
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python nao encontrado. Instale o Python 3.10+.
    pause
    exit /b 1
)

REM Verificar se o uv está disponível
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando uv...
    pip install uv
)

REM Instalar dependências desktop
echo.
echo [INFO] Instalando dependencias desktop...
uv pip install pywebview httpx psutil

REM Verificar se o Node.js está disponível
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Node.js nao encontrado. O frontend sera servido como HTML estatico.
    goto :skip_frontend
)

REM Build do frontend
echo.
echo [INFO] Buildando frontend...
pushd frontend
call npm run build
set FRONTEND_BUILD_ERROR=!errorlevel!
popd
if !FRONTEND_BUILD_ERROR! neq 0 (
    echo [WARN] Falha no build do frontend. Continuando sem...
    goto :skip_frontend
)
echo [OK] Frontend buildado com sucesso.

:skip_frontend

REM Build do .exe com PyInstaller
echo.
echo [INFO] Buildando ClawAI.exe com PyInstaller...

REM Remover build anterior
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Instalar PyInstaller se necessario
uv pip install pyinstaller 2>nul

REM Executar PyInstaller
pyinstaller --onefile ^
    --name ClawAI ^
    --noconsole ^
    --add-data "frontend/dist;frontend/dist" ^
    --add-data "clawai;clawai" ^
    --add-data "configs;configs" ^
    --add-data "database;database" ^
    --hidden-import=webview ^
    --hidden-import=pynvml ^
    --hidden-import=psutil ^
    --hidden-import=uvicorn ^
    --hidden-import=httpx ^
    --hidden-import=fastapi ^
    main.py

if %errorlevel% neq 0 (
    echo [ERROR] Falha no build do PyInstaller.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build concluido com sucesso!
echo   Executavel: dist\ClawAI.exe
echo ========================================
echo.
echo Para testar:
echo   dist\ClawAI.exe
echo.
pause
