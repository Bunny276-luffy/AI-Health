@echo off
echo ========================================================
echo Starting NeuroScan Full Stack (Backend + Frontend)
echo ========================================================

echo 1. Launching Backend in new window...
start "NeuroScan Backend" cmd.exe /c "start_backend.bat"

echo 2. Launching Frontend in new window...
start "NeuroScan Frontend" cmd.exe /c "start_frontend.bat"

echo.
echo Both servers are starting up!
echo The frontend will be available at http://localhost:3000
echo The backend API will be available at http://localhost:8000
echo.
pause
