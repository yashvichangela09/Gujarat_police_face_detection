@echo off
setlocal
cd /d "%~dp0"

set PYTHON_BIN=python
if exist "%~dp0venv\Scripts\python.exe" (
  set PYTHON_BIN="%~dp0venv\Scripts\python.exe"
)

echo Starting SENTINEL AI Multi-Camera Intelligence Command Center...
%PYTHON_BIN% main.py

pause
endlocal
