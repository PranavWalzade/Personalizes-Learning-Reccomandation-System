@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Python virtual environment not found.
    echo Create it with: python -m venv .venv
    echo Then install dependencies with: .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

start "LearnAI Backend" /D "%~dp0" "%~dp0\.venv\Scripts\python.exe" "%~dp0\app\backend\app.py"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5000/"
