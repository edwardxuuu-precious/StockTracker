@echo off
setlocal

REM Start backend and frontend in separate windows so logs stay visible.
REM Backend logs will appear in the backend window in real time.

set "ROOT=%~dp0"
set "RUNTIME_DIR=%ROOT%.runtime"
set "PORT_FILE=%RUNTIME_DIR%\backend-port.txt"

echo Checking for existing StockTracker windows...
taskkill /FI "WINDOWTITLE eq StockTracker Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq StockTracker Frontend*" /T /F >nul 2>&1

echo Cleaning up old StockTracker backend/frontend processes...
powershell -NoProfile -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "$root=(Resolve-Path '%ROOT%').Path;" ^
  "$targets=Get-CimInstance Win32_Process | Where-Object {" ^
  "  $name=($_.Name + '').ToLowerInvariant();" ^
  "  if($name -notin @('python.exe','node.exe','cmd.exe')){ return $false };" ^
  "  $cmd=$_.CommandLine;" ^
  "  if(-not $cmd){ return $false };" ^
  "  ($cmd -like ('*'+$root+'*backend*start_server.py*')) -or" ^
  "  ($cmd -like ('*'+$root+'*uvicorn app.main:app*')) -or" ^
  "  ($cmd -like ('*'+$root+'*frontend*vite*')) -or" ^
  "  ($cmd -like ('*'+$root+'*frontend*npm*run dev*'))" ^
  "};" ^
  "foreach($p in $targets){ Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }"

if exist "%PORT_FILE%" del /q "%PORT_FILE%" >nul 2>&1
ping -n 2 127.0.0.1 >nul

echo Starting StockTracker Backend...
start "StockTracker Backend" /d "%ROOT%backend" cmd /k "start-backend.cmd"

echo Starting StockTracker Frontend...
start "StockTracker Frontend" /d "%ROOT%frontend" cmd /k "start-frontend.cmd"

set "BACKEND_PORT="
set /a WAIT_COUNT=0
:wait_backend_port
if exist "%PORT_FILE%" (
  set /p BACKEND_PORT=<"%PORT_FILE%"
) else (
  set /a WAIT_COUNT+=1
  if %WAIT_COUNT% LEQ 30 (
    ping -n 2 127.0.0.1 >nul
    goto :wait_backend_port
  )
)
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8001"

echo.
echo Backend and frontend started.
echo Backend URL: http://localhost:%BACKEND_PORT%/
echo API Docs:    http://localhost:%BACKEND_PORT%/docs
echo Close the windows or press Ctrl+C in each to stop.
endlocal
