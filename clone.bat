@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH. Please install Python.
    exit /b 1
)

:: Create Virtual Environment if not exists
if not exist "venv" (
    echo [*] Creating virtual environment (venv)...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate

:: Install/Update dependencies
if exist "requirements.txt" (
    echo [*] Checking dependencies...
    pip install -r requirements.txt --quiet
)

:: Install Playwright if not already installed
if not exist "venv\.playwright_done" (
    echo [*] Installing Playwright Chromium...
    playwright install chromium
    echo done > "venv\.playwright_done"
)

:: Run the tracker
echo [*] Launching HTT Tracker...
python tracker.py %* --serve
