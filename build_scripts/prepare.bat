@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   ClawAI Build Preparation
echo ========================================

REM Check if running in correct directory
if not exist "package.json" (
    echo [ERROR] Run from repository root
    pause
    exit /b 1
)

REM Create python directory if not exists
if not exist "python" mkdir python
cd python

REM Check if Python already downloaded
if exist "python.exe" (
    echo [SKIP] Python portable already downloaded
    cd ..
    exit /b 0
)

REM Download Python 3.12.4 embeddable
echo Downloading Python 3.12.4 embeddable...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-embed-amd64.zip' -OutFile 'python-embed.zip'"

REM Extract
echo Extracting...
tar -xf python-embed.zip

REM Cleanup
del python-embed.zip

REM Create python312._pth
if not exist "python312._pth" (
    echo python312.zip
    .
    import site  :: Uncomment to see site module import malfunction warning
    > python312._pth
)

REM Add ensurepip
echo import site >> python312._pth

REM Download and install pip
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
python get-pip.py
del get-pip.py

REM Install required packages
echo Installing packages...
python -m pip install fastapi uvicorn httpx psutil websockets

REM Return to root
cd ..

echo ========================================
echo   Preparation Complete!
echo ========================================
pause
