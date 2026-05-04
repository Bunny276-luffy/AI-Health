@echo off
echo ========================================================
echo Starting NeuroScan Next.js Frontend...
echo ========================================================
cd /d "f:\projects\ai\uncertainty-aware-tumor-detection\frontend"

:: Install dependencies if node_modules is missing
if not exist "node_modules\" (
    echo [INFO] node_modules not found, installing dependencies...
    call npm install
)

:: Also install the new libraries we added for the 6 features just in case
echo [INFO] Verifying feature dependencies (lucide-react, react-hot-toast, axios)...
call npm install lucide-react react-hot-toast axios

:: Start dev server
echo Starting Next.js...
npm run dev

pause
