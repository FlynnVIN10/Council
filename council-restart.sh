#!/bin/bash

# The Council — Full Restart (runnable from anywhere)

COUNCIL_DIR="/Users/Flynn/Documents/GitHub/Council"

cd "$COUNCIL_DIR" || { echo "Error: Cannot access Council directory at $COUNCIL_DIR"; exit 1; }

echo ""
echo "================================================================="
echo "                         THE COUNCIL"
echo "================================================================="
echo ""

echo "Stopping existing Ollama processes..."
pkill -9 -f "ollama serve" || true

echo "Aggressively stopping existing uvicorn processes..."
pkill -9 -f "uvicorn" || true
sleep 2

echo "Ensuring port 8000 is free..."
for i in {1..10}; do
    if lsof -i :8000 > /dev/null 2>&1; then
        echo "Waiting for port 8000 to free... ($i/10)"
        sleep 1
    else
        break
    fi
done

if lsof -i :8000 > /dev/null 2>&1; then
    echo "Error: Port 8000 still in use. Manual cleanup required."
    echo "Run: pkill -9 -f uvicorn"
    exit 1
fi

echo "Starting Ollama server..."
nohup ollama serve > ollama.log 2>&1 &
sleep 8

echo "Stopping existing processes...COMPLETE"
echo "Starting...COMPLETE"
echo "Activating environment...COMPLETE"
source venv/bin/activate

echo ""
echo "================================================================="
echo "WELCOME"
echo "================================================================="
echo ""
echo "System integrity check... COMPLETE"
sleep 1
echo "Neural activation... COMPLETE"
sleep 1
echo "Conduit Open"
echo ""
echo "Access:"
echo "http://localhost:8000"
echo ""

# Uncomment the line below to automatically open the browser (macOS only)
# open http://localhost:8000

uvicorn src.api.main:app --reload --port 8000
