@echo off
for /f "tokens=*" %%a in ('powershell -Command "(Start-Process -FilePath 'ping' -ArgumentList '127.0.0.1', '-n', '10' -PassThru -NoNewWindow -RedirectStandardOutput 'backend.log').Id"') do set BACKEND_PID=%%a
echo PID=%BACKEND_PID%
tasklist /FI "PID eq %BACKEND_PID%"

echo Press any key to kill
pause >nul
taskkill /PID %BACKEND_PID% /T /F
