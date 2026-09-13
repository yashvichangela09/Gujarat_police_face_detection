@echo off
setlocal

set PYTHON_BIN=python
if exist "%~dp0venv\Scripts\python.exe" (
  set PYTHON_BIN="%~dp0venv\Scripts\python.exe"
)

if "%~1"=="" (
  echo No video specified. Automatically using project demo video...
  %PYTHON_BIN% demo_runner.py --camera-id CAM-001 --location "Demo Surveillance Zone"
) else (
  %PYTHON_BIN% demo_runner.py --video "%~1" --camera-id CAM-001 --location "Demo Surveillance Zone"
)
endlocal
