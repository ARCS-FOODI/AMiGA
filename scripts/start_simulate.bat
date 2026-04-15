@echo off
title AMiGA Simulation Server

echo =========================================
echo   Starting AMiGA Simulation
echo =========================================
echo.

:: Get the project root (parent of the scripts directory)
set "TARGET_DIR=%~dp0.."
cd /d "%TARGET_DIR%"

:: Verify .venv exists
if not exist ".venv\" (
    echo [ERROR] The .venv environment was not found!
    echo Please run install_dependencies.bat first.
    pause
    exit /b 1
)

:: ENABLE SIMULATION MODE
:: This tells the backend to mock missing Raspberry Pi hardware
set AMIGA_SIMULATE=1

:: Create logs directory if it doesn't exist
if not exist "logs\" mkdir logs

:: Daily log file: one log per calendar day, all runs append to the same file
:: Use PowerShell for locale-independent YYYY-MM-DD date formatting
for /f "tokens=*" %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%d"
set "LOG_FILE=logs\backend_simulate_%TODAY%.log"

echo [1/2] Starting Python Backend in SIMULATION mode on port 8000...
echo. >> "%LOG_FILE%"
echo === Simulation session started: %date% %time% === >> "%LOG_FILE%"
start "AMiGA Backend" cmd /c ".venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload >> "%LOG_FILE%" 2>&1"
echo [SUCCESS] Backend execution initiated. Logging to: %LOG_FILE%
echo.
echo [2/2] Starting Vite Frontend on port 5173...
cd frontend
start "AMiGA Frontend" cmd /c "npm run dev"
cd ..

echo.
echo =========================================
echo   AMiGA SIMULATION is now running.
echo   - The mocked backend runs in a separate window.
echo   - The frontend runs in a separate window.
echo.
echo   - Backend Documentation: http://localhost:8000/docs#/
echo   - UI Dashboard:          http://localhost:5173
echo.
echo   Note: Real hardware GPIO is disabled.
echo   Close those windows to stop the servers.
echo =========================================
pause
