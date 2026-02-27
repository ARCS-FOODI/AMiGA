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
if %errorlevel% neq 0 goto InstallPython
goto CheckVenv

:InstallPython
echo [ERROR] Python is not installed or not added to your system PATH.
echo Attempting to install Python 3.12 using winget...
winget install Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python via winget. Please install Python 3.10+ manually.
    pause
    exit /b 1
)
echo Python installed successfully!
echo IMPORTANT: You MUST close this terminal and open a new one for the PATH changes to take effect.
echo Then run this script again.
pause
goto CheckVenv

:CheckVenv
if exist ".venv\" goto VenvExists
echo Creating virtual environment in .venv...
python -m venv .venv
if %errorlevel% neq 0 goto FailVenv
goto InstallBackend

:VenvExists
echo Virtual environment .venv already exists.
goto InstallBackend

:FailVenv
echo [ERROR] Failed to create virtual environment!
pause
exit /b 1

:InstallBackend
echo Installing backend requirements...
.venv\Scripts\python.exe -m pip install --upgrade pip
echo Installing backend requirements one by one to allow skipping unrecognized packages...
for /f "usebackq eol=# tokens=* delims=" %%a in ("requirements.txt") do (
    set "req=%%a"
    echo Installing: !req!
    .venv\Scripts\python.exe -m pip install "!req!" || echo [WARNING] Failed to install !req!. Skipping...
)
echo [SUCCESS] Backend dependency step complete.
echo.
goto SetupFrontend

:FailBackend
echo [ERROR] Backend dependencies failed to install!
pause
exit /b 1

:SetupFrontend
:: 2. Setup Frontend
echo [2/2] Setting up Vite frontend environment...
echo.

:: Check for Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not added to your system PATH.
    echo Attempting to install Node.js 22 using winget...
    winget install OpenJS.NodeJS -e --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Node.js via winget. Please install Node.js v20+ manually.
        pause
        exit /b 1
    )
    echo Node.js installed successfully!
    echo IMPORTANT: You MUST close this terminal and open a new one for the PATH changes to take effect.
    echo Then run this script again.
    pause
    exit /b 0
)

:: Ensure npm is available
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is missing. Please reinstall Node.js.
    pause
    exit /b 1
)

:InstallFrontend
cd frontend

echo Installing npm dependencies...
call npm.cmd install
if %errorlevel% neq 0 goto WarnNpm
goto SuccessNpm

:WarnNpm
echo [WARNING] npm install had some issues, continuing anyway...
goto SuccessNpm

:SuccessNpm
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
