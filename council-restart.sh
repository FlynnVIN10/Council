#!/bin/bash

# The Council — Full Restart (runnable from anywhere)

COUNCIL_DIR="/Users/Flynn/Documents/GitHub/Council"

cd "$COUNCIL_DIR" || { echo "Error: Cannot access Council directory at $COUNCIL_DIR"; exit 1; }

echo ""
echo "================================================================="
echo "                         THE COUNCIL"
echo "================================================================="
echo ""
sleep 2
echo "System integrity check... COMPLETE"
sleep 1
echo "Neural activation... COMPLETE"
sleep 2
echo "Conduit Open"
echo ""
echo "Access:"
echo "http://localhost:8000"
echo ""
echo "================================================================="
echo "WELCOME"
echo "================================================================="
echo ""

echo "Stopping existing processes..."
pkill -f "ollama serve" || true
pkill -f "uvicorn" || true
sleep 2

echo "Starting Ollama server..."
nohup ollama serve > ollama.log 2>&1 &

echo "Waiting for Ollama to initialize..."
sleep 8

echo "Activating environment and starting API..."
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000

echo "The Council is running at http://localhost:8000"
