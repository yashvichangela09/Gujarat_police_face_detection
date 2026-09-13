@echo off
title SENTINEL GUJARAT POLICE INNOVATION CHALLENGE 2026
echo =========================================================================
echo  GUJARAT POLICE INNOVATION CHALLENGE 2026 - SENTINEL CCTV AI PLATFORM
echo =========================================================================
echo [1/3] Starting Python FastAPI Backend Server & AI Engine (Port 8000)...
start "Sentinel Python AI Backend" cmd /k "cd /d E:\Projects\sentinel_police_ai && python run.py"

echo [2/3] Starting React + Vite CCTV Web Dashboard (Port 3000)...
start "Sentinel React Web Platform" cmd /k "cd /d E:\Projects\sentinel-gujarat-cctv-platform && npm run dev"

echo =========================================================================
echo  [SUCCESS] All systems launched!
echo  - Python AI & GIS Dashboard: http://localhost:8000
echo  - React CCTV Web Portal: http://localhost:3000
echo =========================================================================
timeout /t 5
