#!/bin/bash
# WingIt — Launch Script
# Starts the Anthropic proxy (port 3001) + file server (port 8080), opens browser.

APP_PORT="${APP_PORT:-8080}"
PROXY_PORT=3001
DIR="$HOME/Code/wingit-kanban"

if [ ! -d "$DIR" ]; then
  echo "❌  $DIR not found. Run: git clone https://github.com/jwindevelopment/wingit-kanban.git ~/Code/wingit-kanban"
  exit 1
fi

cd "$DIR"

echo ""
echo "  ██╗    ██╗██╗███╗   ██╗ ██████╗ ██╗████████╗"
echo "  ██║    ██║██║████╗  ██║██╔════╝ ██║╚══██╔══╝"
echo "  ██║ █╗ ██║██║██╔██╗ ██║██║  ███╗██║   ██║   "
echo "  ██║███╗██║██║██║╚██╗██║██║   ██║██║   ██║   "
echo "  ╚███╔███╔╝██║██║ ╚████║╚██████╔╝██║   ██║   "
echo "   ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝   ╚═╝  "
echo ""
echo "  App:    http://localhost:$APP_PORT"
echo "  Proxy:  http://localhost:$PROXY_PORT  (Anthropic API)"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo ""

# Kill proxy on exit
cleanup() {
  echo ""
  echo "  Shutting down..."
  kill "$PROXY_PID" 2>/dev/null
  exit 0
}
trap cleanup INT TERM

# Start proxy in background
python3 "$DIR/proxy.py" &
PROXY_PID=$!

# Give proxy a moment to bind
sleep 0.5

# Open browser
if command -v open &>/dev/null; then
  (sleep 0.5 && open "http://localhost:$APP_PORT") &
fi

# Start file server (foreground)
python3 -m http.server "$APP_PORT"
