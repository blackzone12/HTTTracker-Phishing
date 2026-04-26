#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Python3 is not installed. Please install it."
    exit 1
fi

# Create Virtual Environment if not exists
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment (venv)..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install/Update dependencies
if [ -f "requirements.txt" ]; then
    echo "[*] Checking dependencies..."
    pip install -r requirements.txt --quiet
fi

# Install Playwright if not already installed
if [ ! -f "venv/.playwright_done" ]; then
    echo "[*] Installing Playwright Chromium..."
    playwright install chromium
    touch "venv/.playwright_done"
fi

# Run the tracker
echo "[*] Launching HTT Tracker..."
python3 tracker.py "$@" --serve
