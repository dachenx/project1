@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo  RAG QA System - one-click startup
echo =============================================

echo [1/3] Starting backend  (FastAPI :8000) ...
start "RAG Backend" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe run.py"

echo [2/3] Starting frontend (Vite :5173) ...
start "RAG Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo [3/3] Waiting for backend to become ready ...
set /a tries=0

:waitloop
curl -s -m 3 http://127.0.0.1:8000/api/health 2>nul | findstr /c:"ok" >nul
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% GEQ 30 goto timeout
timeout /t 2 /nobreak >nul
goto waitloop

:ready
echo Backend is ready. Opening browser ...
start http://localhost:5173
goto done

:timeout
echo [WARN] Backend not ready after ~60s. Check the "RAG Backend" window.
echo Opening browser anyway ...
start http://localhost:5173

:done
echo Done. Close the two server windows to stop the system.
endlocal
