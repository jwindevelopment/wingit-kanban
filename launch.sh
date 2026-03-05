#!/bin/bash
# WingIt — Launch Script
# Run this once from anywhere. It serves index.html from ~/Downloads.

PORT="${PORT:-8080}"
FILE="index.html"

# Find the most recently downloaded WingIt index.html in ~/Downloads
DOWNLOADS="$HOME/Downloads"
SRC=$(ls -t "$DOWNLOADS"/index*.html 2>/dev/null | head -1)

if [ -z "$SRC" ]; then
  echo "❌  No index.html found in ~/Downloads."
  echo "    Download the latest WingIt file from Claude and try again."
  exit 1
fi

# Copy to ~/Code/kanban-app/ so it's served cleanly
DIR="$HOME/Code/kanban-app"
mkdir -p "$DIR"
cp "$SRC" "$DIR/index.html"

cd "$DIR"

echo ""
echo "  ██╗    ██╗██╗███╗   ██╗ ██████╗ ██╗████████╗"
echo "  ██║    ██║██║████╗  ██║██╔════╝ ██║╚══██╔══╝"
echo "  ██║ █╗ ██║██║██╔██╗ ██║██║  ███╗██║   ██║   "
echo "  ██║███╗██║██║██║╚██╗██║██║   ██║██║   ██║   "
echo "  ╚███╔███╔╝██║██║ ╚████║╚██████╔╝██║   ██║   "
echo "   ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝   ╚═╝  "
echo ""
echo "  Source:  $SRC"
echo "  Serving: $DIR/index.html"
echo "  URL:     http://localhost:$PORT"
echo ""
echo "  Press Ctrl+C to stop."
echo ""

# Open browser
if command -v open &>/dev/null; then
  (sleep 0.8 && open "http://localhost:$PORT") &
fi

# Start server
if command -v python3 &>/dev/null; then
  python3 -m http.server "$PORT"
elif command -v python &>/dev/null; then
  python -m SimpleHTTPServer "$PORT"
elif command -v npx &>/dev/null; then
  npx --yes serve -l "$PORT" .
else
  echo "❌  No suitable server found. Install Python 3 or Node.js."
  exit 1
fi
