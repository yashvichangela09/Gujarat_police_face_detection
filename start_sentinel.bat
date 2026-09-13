@echo off
title SENTINEL GUJARAT POLICE INNOVATION CHALLENGE 2026
echo =========================================================================
echo  GUJARAT POLICE INNOVATION CHALLENGE 2026 - SENTINEL CCTV AI PLATFORM
echo =========================================================================
echo [1/2] Starting Python FastAPI Backend Server & AI Engine (Port 5000)...
start "Sentinel Python AI Backend" cmd /k "cd /d E:\Projects\sentinel_police_ai && python main.py"

echo [2/2] Starting React + Vite CCTV Web Dashboard (Port 5173)...
start "Sentinel React Web Platform" cmd /k "cd /d E:\Projects\sentinel_ui && npm run dev"

echo =========================================================================
echo  [SUCCESS] All systems launched!
echo  - Python AI Backend: http://localhost:5000
echo  - React CCTV Web Portal: http://localhost:5173
echo =========================================================================
timeout /t 5
