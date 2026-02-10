@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\\venv\\Scripts\\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%ROOT%"

echo Running release gate...
"%PY%" backend\scripts\release_gate.py %*

endlocal
