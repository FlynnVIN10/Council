#!/bin/bash

echo "🏛️  THE COUNCIL - Web Terminal Launcher"
echo "========================================"
echo ""

# Navigate to Council repository
cd ~/Documents/GitHub/Council

# Check if ttyd is installed
if ! command -v ttyd &> /dev/null; then
    echo "❌ ttyd not found. Installing via Homebrew..."
    brew install ttyd
fi

echo "✅ ttyd installed (version: $(ttyd --version))"
echo ""
echo "Launching terminals..."
echo ""

# Launch Codex CLI on port 7681
ttyd -p 7681 -t titleFixed="Codex CLI - The Council" codex &
CODEX_PID=$!

# Launch general bash terminal on port 7682
ttyd -p 7682 -t titleFixed="Council Terminal" bash &
BASH_PID=$!

# Wait a moment for terminals to start
sleep 2

echo "🚀 Terminals launched successfully!"
echo ""
echo "📡 Access in your browser:"
echo "   Codex CLI:        http://localhost:7681"
echo "   Council Terminal: http://localhost:7682"
echo ""
echo "📊 Process IDs:"
echo "   Codex:    $CODEX_PID"
echo "   Terminal: $BASH_PID"
echo ""
echo "💾 RAM Impact: ~10-20MB total (negligible)"
echo ""
echo "Press Ctrl+C to stop all terminals"

# Trap Ctrl+C to clean up
trap "echo ''; echo '🛑 Stopping terminals...'; kill $CODEX_PID $BASH_PID 2>/dev/null; echo '✅ Terminals stopped'; exit 0" INT

# Keep script running
wait

