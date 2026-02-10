@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\\venv\\Scripts\\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%ROOT%"

echo Running deploy with rollback...
"%PY%" backend\scripts\deploy_with_rollback.py %*

endlocal
