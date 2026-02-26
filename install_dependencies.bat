@echo off
setlocal enabledelayedexpansion
title AMiGA Dependency Installation Script

echo =========================================
echo   Setting up AMiGA Environment (Windows)
echo =========================================
echo.

:: Get the directory where the script is located
set "TARGET_DIR=%~dp0"
cd /d "%TARGET_DIR%"

:: 1. Setup Backend
echo [1/2] Setting up Python backend environment...
echo.

:: Check for Python
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.10+ from the Microsoft Store or python.org
    echo and ensure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)

if not exist ".venv\" (
    echo Creating virtual environment in .venv...
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
) else (
    echo Virtual environment .venv already exists.
)

echo Activating virtual environment and installing requirements...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
if !errorlevel! neq 0 (
    echo [WARNING] Some backend dependencies failed to install.
    echo This is normal for Raspberry Pi specific hardware libraries on Windows.
    echo The simulation should continue to work.
)
echo [SUCCESS] Backend dependency step complete.
echo.

:: 2. Setup Frontend
echo [2/2] Setting up Vite frontend environment...
echo.

:: Check for Node.js
node --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Node.js is not installed or not added to your system PATH.
    echo Please download and install Node.js v20+ from https://nodejs.org/
    pause
    exit /b 1
)

:: Ensure npm is available
npm --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] npm is missing. Please reinstall Node.js.
    pause
    exit /b 1
)

cd frontend

echo Installing npm dependencies...
call npm install
if !errorlevel! neq 0 (
    echo [WARNING] npm install had some issues, continuing anyway...
)
echo [SUCCESS] Frontend dependency step complete.
echo.

cd /d "%TARGET_DIR%"

echo =========================================
echo   Setup Complete^^! 
echo   You can now run the backend using:
echo   .venv\Scripts\python backend\api\main.py
echo.
echo   And the frontend using:
echo   cd frontend ^&^& npm run dev
echo =========================================
pause
