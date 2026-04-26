@echo off
echo ==========================================
echo  AI Billing System - Startup Script
echo ==========================================
echo.

REM Get the local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo Your Local IP: %LOCAL_IP%
echo.
echo Starting Backend Server (Port 8001)...
echo Starting Frontend Server (Port 8080)...
echo.
echo Access from this PC:    http://localhost:8080/ai_billing.html
echo Access from other device: http://%LOCAL_IP%:8080/ai_billing.html
echo.
echo ==========================================
echo Press Ctrl+C to stop both servers
echo ==========================================
echo.

start "Backend API - Port 8001" cmd /k "cd /d c:\Users\Rohit\Desktop\smart_billing_api && python billing_api.py"
timeout /t 3 >nul
start "Frontend Server - Port 8080" cmd /k "cd /d c:\Users\Rohit\Desktop\smart_billing_api && python -m http.server 8080"

echo.
echo Both servers started! Open your browser to the URLs above.
pause

