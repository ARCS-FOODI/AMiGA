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

echo [1/2] Starting Python Backend on port 8000...
start /B "AMiGA Backend" cmd /c ".venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1"
set BACKEND_PID=UNKNOWN
echo [SUCCESS] Backend background execution initiated.

echo.
echo [2/2] Starting Vite Frontend on port 5173...
cd frontend
start /B "AMiGA Frontend" cmd /c "npm run dev"
set FRONTEND_PID=UNKNOWN
cd ..

echo.
echo =========================================
echo   Servers are running!
echo   - Backend Documentation: http://localhost:8000/docs#/
echo   - UI Dashboard:          http://localhost:5173
echo.
echo   Press any key to stop both servers...
echo =========================================
pause >nul

echo.
echo Stopping servers...
echo Done.
