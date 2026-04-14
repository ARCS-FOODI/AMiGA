@echo off
setlocal
echo Starting test script...
for /f "tokens=*" %%a in ('powershell -Command "(Start-Process -FilePath 'ping' -ArgumentList '127.0.0.1 -n 10' -PassThru -NoNewWindow -RedirectStandardOutput 'test_ps.log').Id"') do set PID=%%a

echo Started process with PID: %PID%

timeout /t 2 /nobreak >nul
tasklist /FI "PID eq %PID%" | find "%PID%" >nul
if errorlevel 1 (
    echo [ERROR] Process crashed.
) else (
    echo [SUCCESS] Process running.
)

echo Killing %PID%
taskkill /PID %PID% /T /F
echo Done!
