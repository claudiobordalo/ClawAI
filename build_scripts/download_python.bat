@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Downloading Python Portable
echo ========================================

REM Create python directory
if not exist "python" mkdir python
cd python

REM Download Python 3.12.4 Windows embeddable package
echo Downloading Python 3.12.4 embeddable package...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-embed-amd64.zip' -OutFile 'python-embed.zip'"

REM Extract
echo Extracting...
tar -xf python-embed.zip

REM Remove zip file
del python-embed.zip

REM Create python312._pth file if not exists
if not exist "python312._pth" (
    echo python312.zip
    .
    import site  :: Uncomment to see site module import malfunction warning
    > python312._pth
)

REM Add ensurepip for pip support
echo import site >> python312._pth

REM Download get-pip.py
echo Downloading get-pip.py...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"

REM Install pip
echo Installing pip...
python get-pip.py

REM Install required packages
echo Installing required packages...
python -m pip install fastapi uvicorn httpx psutil websockets

REM Cleanup
del get-pip.py

REM Return to root
cd ..

echo ========================================
echo   Python Portable Ready!
echo ========================================
pause
