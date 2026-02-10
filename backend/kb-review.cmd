@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
cd /d "%~dp0.."

"%PY%" backend\scripts\kb_benchmark_review.py %*

endlocal
