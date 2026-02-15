@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0clean-local.ps1" %*
endlocal
