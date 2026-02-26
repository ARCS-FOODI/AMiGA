@echo off
title AMiGA Production Server

echo =========================================
echo   Starting AMiGA Native Application
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

:: Ensure simulation is off
set AMIGA_SIMULATE=0

echo [1/2] Starting Python Backend...
start "AMiGA Backend" cmd /c ".venv\Scripts\python backend\api\main.py"

echo [2/2] Starting Vite Frontend...
cd frontend
start "AMiGA Frontend" cmd /c "npm run dev"

echo.
echo =========================================
echo   AMiGA is now running.
echo   - The backend runs in a separate window.
echo   - The frontend runs in a separate window.
echo.
echo   Close those windows to stop the servers.
echo =========================================
pause
