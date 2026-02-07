@echo off
REM Validate environment configuration before starting frontend

echo ========================================
echo StockTracker Frontend Configuration Check
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file from .env.example:
    echo   copy .env.example .env
    echo.
    pause
    exit /b 1
)

echo [OK] .env file exists
echo.

REM Check VITE_API_URL value
findstr /C:"VITE_API_URL=http://localhost:8001" .env >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] API URL is correctly configured: http://localhost:8001
    echo.
) else (
    findstr /C:"VITE_API_URL" .env
    echo.
    echo [ERROR] API URL is not set to http://localhost:8001
    echo.
    echo Please update .env file:
    echo   VITE_API_URL=http://localhost:8001
    echo.
    echo Then restart the frontend server.
    echo.
    pause
    exit /b 1
)

REM Check if backend is running
echo Checking backend server connectivity...
curl -s -o nul -w "%%{http_code}" http://localhost:8001/api/v1/portfolios/ > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if "%STATUS%"=="200" (
    echo [OK] Backend server is running on port 8001
    echo.
) else (
    echo [ERROR] Cannot connect to backend server!
    echo.
    echo Please start the backend server:
    echo   start-backend.bat
    echo.
    echo Or manually:
    echo   cd backend
    echo   python start_server.py --port 8001
    echo.
    pause
    exit /b 1
)

echo ========================================
echo [SUCCESS] All checks passed!
echo You can now start the frontend server.
echo ========================================
echo.

exit /b 0
