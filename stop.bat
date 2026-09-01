@echo off
setlocal

echo =============================================
echo  RAG QA System - one-click shutdown
echo =============================================

call :killport 8000
call :killport 5173

echo.
echo Done. Ports 8000 / 5173 are released.
endlocal
exit /b

:killport
for /f "tokens=5" %%a in ('netstat -ano ^| findstr LISTENING ^| findstr /c:":%1 "') do (
  echo Closing port %1 (PID %%a) ...
  taskkill /F /PID %%a >nul 2>&1
)
exit /b
