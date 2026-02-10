@echo off
setlocal

REM Resolve repo root from this script's location.
set "ROOT=%~dp0.."
set "VENV=%ROOT%\\venv"
set "PY=%VENV%\\Scripts\\python.exe"
set "RUNTIME_DIR=%ROOT%\\.runtime"
set "PORT_FILE=%RUNTIME_DIR%\\backend-port.txt"
set "PORT=%BACKEND_PORT%"

REM Prefer a stable Python for dependencies (SQLAlchemy currently breaks on Python 3.14).
set "PY_LAUNCHER="
for %%V in (3.12 3.11 3.10) do (
  py -%%V -V >nul 2>&1 && set "PY_LAUNCHER=py -%%V" && goto :found_py
)
:found_py
if "%PY_LAUNCHER%"=="" set "PY_LAUNCHER=python"

if not exist "%PY%" (
  echo Creating Python virtual environment with %PY_LAUNCHER% ...
  %PY_LAUNCHER% -m venv "%VENV%"
)

REM If existing venv uses Python 3.13+ and we have a 3.12/3.11, recreate it.
"%PY%" -c "import sys; raise SystemExit(0 if sys.version_info < (3,13) else 1)" >nul 2>&1
if errorlevel 1 (
  if not "%PY_LAUNCHER%"=="python" (
    echo Detected Python 3.13+ in venv. Recreating with %PY_LAUNCHER% ...
    rmdir /s /q "%VENV%"
    %PY_LAUNCHER% -m venv "%VENV%"
  )
)

REM Ensure backend runtime deps are installed before launching uvicorn.
"%PY%" -c "import importlib.util as u, sys; mods=('psutil','fastapi','uvicorn'); missing=[m for m in mods if u.find_spec(m) is None]; sys.exit(1 if missing else 0)" >nul 2>&1
if errorlevel 1 (
  echo Installing backend dependencies...
  "%PY%" -m pip install -r "%~dp0requirements.txt"
)

if "%PORT%"=="" (
  for /f %%P in ('powershell -NoProfile -Command "$p=8001; while (Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue) { $p++ }; Write-Output $p"') do set "PORT=%%P"
)

if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%"
> "%PORT_FILE%" echo %PORT%

set PYTHONUNBUFFERED=1
echo Using backend port %PORT%
"%PY%" "%~dp0start_server.py" --port %PORT% --force

endlocal
