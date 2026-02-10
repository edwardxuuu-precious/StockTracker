@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "BACKEND_PORT=%BACKEND_PORT%"
set "PORT_FILE=%~dp0..\\.runtime\\backend-port.txt"
if "%BACKEND_PORT%"=="" (
  set /a WAIT_COUNT=0
  :wait_port_file
  if exist "%PORT_FILE%" (
    set /p BACKEND_PORT=<"%PORT_FILE%"
  ) else (
    set /a WAIT_COUNT+=1
    if !WAIT_COUNT! LEQ 30 (
      ping -n 2 127.0.0.1 >nul
      goto :wait_port_file
    )
  )
)
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8001"
set "VITE_API_URL=http://localhost:%BACKEND_PORT%"
echo Using API URL %VITE_API_URL%

REM Wait for backend API to become reachable before running frontend preflight.
set /a API_WAIT=0
:wait_backend_api
curl.exe -s -o nul "%VITE_API_URL%/api/v1/portfolios/" >nul 2>&1
if errorlevel 1 (
  set /a API_WAIT+=1
  if !API_WAIT! LEQ 30 (
    ping -n 2 127.0.0.1 >nul
    goto :wait_backend_api
  )
)

REM Choose an available frontend port starting from 5173.
set "PORT=5173"
:find_port
set "INUSE="
for /f "tokens=1,2,3,4,5" %%A in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do set "INUSE=1"
if defined INUSE (
  set /a PORT+=1
  goto find_port
)

if not exist node_modules (
  echo Installing frontend dependencies...
  npm install
)

if not exist .env (
  copy /y .env.example .env >nul
)

echo Starting frontend on http://localhost:%PORT%/
npm run dev -- --port %PORT% --strictPort --open

endlocal
