#!/bin/bash

# The Council — Clean Shutdown (runnable from anywhere)

COUNCIL_DIR="/Users/Flynn/Documents/GitHub/Council"

cd "$COUNCIL_DIR" || { echo "Error: Cannot access Council directory at $COUNCIL_DIR"; exit 1; }

echo ""
echo "================================================================="
echo "                         THE COUNCIL"
echo "================================================================="
echo ""
sleep 2
echo "System shutdown initiated..."
sleep 1
echo "Terminating neural pathways..."
sleep 2
echo "Conduit closing..."
echo ""
echo "The Council rests."
echo ""
echo "================================================================="
echo "GOODBYE"
echo "================================================================="
echo ""

echo "Stopping local processes..."
pkill -f "run_council.py" >/dev/null 2>&1 || true
pkill -f "ollama serve" >/dev/null 2>&1 || true

echo ""
echo "All processes terminated."
