#!/bin/bash
# Launch ttyd web terminals for The Council project

# Kill any existing ttyd processes
pkill -f ttyd

# Launch Codex CLI terminal on port 7681 (WITH -W for writable)
ttyd -W -i 127.0.0.1 -O -p 7681 -t titleFixed="Codex CLI - The Council" codex &

# Launch Council bash terminal on port 7682 (WITH -W for writable)
ttyd -W -i 127.0.0.1 -O -p 7682 -t titleFixed="Council Terminal" bash &

echo "Web terminals launched:"
echo "  - Codex CLI: http://localhost:7681"
echo "  - Council Terminal: http://localhost:7682"
echo ""
echo "To stop: pkill -f ttyd"

