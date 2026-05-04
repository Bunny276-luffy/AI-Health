@echo off
echo ========================================================
echo Starting NeuroScan Backend API...
echo ========================================================
cd /d "f:\projects\ai\uncertainty-aware-tumor-detection\backend"

:: Verify virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at backend\venv!
    echo Please create one using: python -m venv venv
    pause
    exit /b 1
)

:: Run Uvicorn server
echo Running Uvicorn on port 8000...
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

pause
