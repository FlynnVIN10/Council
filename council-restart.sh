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
sleep 2

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
echo "The Council is ready."
echo ""

python run_council.py
