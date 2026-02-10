@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\\venv\\Scripts\\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%~dp0"

echo Starting StockTracker Scheduler...
"%PY%" run_scheduler.py

endlocal
