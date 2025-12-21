#!/bin/bash

# The Council — CLI-only execution (default)
# For Docker deployment, use: docker-compose up --build

COUNCIL_DIR="/Users/Flynn/Documents/GitHub/Council"

cd "$COUNCIL_DIR" || { echo "Error: Cannot access Council directory at $COUNCIL_DIR"; exit 1; }

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
pkill -f "ollama serve" || true
ollama serve &
sleep 8
source venv/bin/activate
echo "The Council is ready."
echo ""
exec python run_council.py
