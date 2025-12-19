#!/bin/bash

echo "The Council — Full Restart"

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

echo "Starting API server..."
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000

echo "The Council is running at http://localhost:8000"
