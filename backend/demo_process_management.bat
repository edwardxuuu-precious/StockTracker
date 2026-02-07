@echo off
REM Demonstration of the new process management system
echo ====================================================================
echo StockTracker Backend Process Management Demonstration
echo ====================================================================
echo.

echo [Test 1] Starting server for the first time...
echo.
start /B python start_server.py --port 8001
timeout /t 5 /nobreak >nul

echo.
echo [Test 2] Attempting to start server again (should fail - port in use)...
echo.
python start_server.py --port 8001
timeout /t 2 /nobreak >nul

echo.
echo [Test 3] Force restart - killing existing processes and restarting...
echo.
python start_server.py --port 8001 --force

echo.
echo [Test 4] Stopping server gracefully...
echo.
python stop_server.py --port 8001

echo.
echo ====================================================================
echo Demonstration complete!
echo ====================================================================
pause
