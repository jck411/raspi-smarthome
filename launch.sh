#!/bin/bash
# Smart Home Launcher
# Starts browser in kiosk mode and the wake word listener

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set DISPLAY for X11 (needed when running from SSH or systemd)
export DISPLAY="${DISPLAY:-:0}"

# Load .env for BACKEND URL (extract host from WebSocket URL)
if [ -f .env ]; then
    source <(grep -E '^[A-Z_]+=.*' .env | sed 's/\r$//')
fi

# Default backend URL (http, derived from ws url or fallback)
BACKEND_HOST="${BACKEND_WS_URL:-ws://localhost:8000}"
BACKEND_HOST="${BACKEND_HOST#ws://}"
BACKEND_HOST="${BACKEND_HOST#wss://}"
BACKEND_HOST="${BACKEND_HOST%%/*}"
FRONTEND_URL="http://${BACKEND_HOST}"

# Cleanup any stale audio agent processes from previous runs
echo "Checking for stale audio agent processes..."
if pgrep -f "audio_agent.main" > /dev/null; then
    echo "  Found stale audio agent processes. Cleaning up..."
    pkill -f "audio_agent.main" || true
    sleep 1
    # Force kill if still running
    pkill -9 -f "audio_agent.main" 2>/dev/null || true
fi

echo "============================================"
echo "   Smart Home Launcher"
echo "============================================"
echo "Frontend URL: $FRONTEND_URL"
echo "Script Dir: $SCRIPT_DIR"
echo "Display: $DISPLAY"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    
    # Kill cursor hider if running
    if [ -n "$UNCLUTTER_PID" ]; then
        kill "$UNCLUTTER_PID" 2>/dev/null || true
    fi
    
    # Kill browser if we started it
    if [ -n "$BROWSER_PID" ]; then
        kill "$BROWSER_PID" 2>/dev/null || true
    fi
    
    # Kill audio agent if running
    if [ -n "$AGENT_PID" ]; then
        kill "$AGENT_PID" 2>/dev/null || true
    fi
    
    echo "Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Hide cursor for touch screen (requires unclutter)
if command -v unclutter &> /dev/null; then
    echo "Hiding cursor for touch screen..."
    unclutter -idle 0.1 -root &
    UNCLUTTER_PID=$!
else
    echo "  ⚠ unclutter not found - cursor will be visible"
    echo "    Install with: sudo apt install unclutter"
fi

# Detect and start browser in kiosk mode (background)
echo "Detecting browser..."
if command -v chromium-browser &> /dev/null; then
    echo "  ✓ Found: Chromium (RECOMMENDED for Raspberry Pi kiosk)"
    echo "Starting Chromium in kiosk mode (touch optimized)..."
    chromium-browser \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --disable-session-crashed-bubble \
        --disable-restore-session-state \
        --no-first-run \
        --touch-events=enabled \
        --enable-features=TouchpadOverscrollHistoryNavigation \
        --enable-touch-drag-drop \
        --disable-pinch \
        --overscroll-history-navigation=0 \
        "$FRONTEND_URL" &
    BROWSER_PID=$!
elif command -v chromium &> /dev/null; then
    echo "  ✓ Found: Chromium"
    echo "Starting Chromium in kiosk mode (touch optimized)..."
    chromium \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --disable-session-crashed-bubble \
        --disable-restore-session-state \
        --no-first-run \
        --touch-events=enabled \
        --enable-features=TouchpadOverscrollHistoryNavigation \
        --enable-touch-drag-drop \
        --disable-pinch \
        --overscroll-history-navigation=0 \
        "$FRONTEND_URL" &
    BROWSER_PID=$!
elif command -v firefox &> /dev/null; then
    firefox --kiosk "$FRONTEND_URL" &
    BROWSER_PID=$!
else
    echo "WARNING: No supported browser found (chromium-browser, chromium, or firefox)"
    echo "Please install Chromium: sudo apt install chromium-browser"
fi

# Give browser a moment to start
sleep 2

# Start the audio agent (wake word listener)
echo "Starting wake word listener..."
uv run python -m audio_agent.main &
AGENT_PID=$!

echo ""
echo "============================================"
echo "   Smart Home is running!"
echo "   Press Ctrl+C to stop"
echo "============================================"
echo ""

# Wait for processes
wait $AGENT_PID
