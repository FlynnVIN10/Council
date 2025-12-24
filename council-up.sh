#!/bin/bash

# The Council — Start (runnable from anywhere)

COUNCIL_DIR="/Users/Flynn/Documents/GitHub/Council"

cd "$COUNCIL_DIR" || { echo "Error: Cannot access Council directory at $COUNCIL_DIR"; exit 1; }

echo "================================================================="
echo "                         THE COUNCIL"
echo "================================================================="
echo ""
sleep 1
echo "System integrity check... COMPLETE"
sleep 1
echo "Neural activation... COMPLETE"
sleep 1
echo "Conduit Open"
echo ""

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "Starting Ollama..."
  ollama serve &
  sleep 8
fi

source venv/bin/activate
echo "The Council is ready."
echo ""
exec python run_council.py </dev/tty
