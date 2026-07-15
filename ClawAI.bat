@echo off
cd /d D:\ClawAI
echo Iniciando servidores (Backend + Frontend)...
call npm run dev
timeout /t 5 /nobreak >nul
echo Abrindo navegador...
start "" "http://localhost:5173"
pause
