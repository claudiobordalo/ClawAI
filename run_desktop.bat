@echo off
echo ========================================
echo   ClawAI Desktop - Inicializando...
echo ========================================
echo.

REM Verifica se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python n"ao encontrado. Instale o Python 3.9+.
    pause
    exit /b 1
)

REM Verifica se o Node.js está instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js n"ao encontrado. Instale o Node.js 18+.
    pause
    exit /b 1
)

REM Verifica se as dependências do Python estão instaladas
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando dependencias do Python...
    pip install -e .
)

REM Verifica se o frontend está buildado
if not exist "frontend\dist" (
    echo [INFO] Buildando frontend...
    cd frontend
    npm run build
    cd ..
)

echo.
echo [INFO] Iniciando ClawAI Desktop...
echo [INFO] O navegador sera aberto automaticamente.
echo.
python main.py

pause
