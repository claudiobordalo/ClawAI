@echo off
setlocal
cd /d "%~dp0"

where uv >nul 2>nul
if errorlevel 1 (
    echo uv nao encontrado no PATH.
    pause
    exit /b 1
)

uv run python verify.py
set "EXITCODE=%ERRORLEVEL%"
pause
exit /b %EXITCODE%
