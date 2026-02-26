@echo off
title AMiGA Simulation Server

echo =========================================
echo   Starting AMiGA Simulation
echo =========================================
echo.

:: Get the directory where the script is located
set "TARGET_DIR=%~dp0"
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

echo [1/2] Starting Python Backend in SIMULATION mode...
start "AMiGA Backend (Simulation)" cmd /c ".venv\Scripts\python backend\api\main.py"

echo [2/2] Starting Vite Frontend...
cd frontend
start "AMiGA Frontend" cmd /c "npm run dev"

echo.
echo =========================================
echo   AMiGA SIMULATION is now running.
echo   - The mocked backend runs in a separate window.
echo   - The frontend runs in a separate window.
echo.
echo   Note: Real hardware GPIO is disabled.
echo   Close those windows to stop the servers.
echo =========================================
pause
