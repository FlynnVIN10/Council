#!/bin/bash

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

echo "Stopping existing Ollama processes..."
pkill -f "ollama serve" || true
sleep 2

echo "Stopping existing uvicorn processes..."
pkill -f "uvicorn" || true
sleep 2

echo "Starting Ollama server..."
nohup ollama serve > ollama.log 2>&1 &

echo "Waiting for Ollama to initialize..."
sleep 8

# Uncomment the line below to automatically open the browser (macOS only)
# open http://localhost:8000

echo "Starting API server..."
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
