#!/bin/bash

# The Council full restart script

echo "Stopping existing processes..."
pkill -f "ollama serve"
pkill -f "uvicorn"

echo "Starting Ollama server..."
ollama serve &

echo "Waiting for Ollama to initialize..."
sleep 5

echo "Activating virtual environment and starting API..."
source venv/bin/activate
uvicorn src.api.main:app --reload

echo "The Council is now running at http://localhost:8000"
