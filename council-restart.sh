#!/bin/bash
# One-command restart for The Council platform
# Kills existing processes and starts fresh Ollama + API

# Kill existing ollama serve processes
pkill -f "ollama serve" 2>/dev/null

# Kill existing uvicorn processes
pkill -f "uvicorn.*src.api.main" 2>/dev/null

# Wait a moment for processes to stop
sleep 1

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start ollama serve in background
ollama serve &

# Change to council directory
cd "$SCRIPT_DIR"

# Activate virtual environment and start API
source venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

