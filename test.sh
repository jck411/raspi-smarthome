#!/bin/bash
# Quick test script for audio agent

echo "=== Audio Agent Test ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Run: cp .env.example .env"
    echo "Then edit .env to set BACKEND_WS_URL"
    exit 1
fi

# Check backend URL
BACKEND_URL=$(grep BACKEND_WS_URL .env | cut -d '=' -f2)
echo "Backend configured: $BACKEND_URL"
echo ""

# Check if dependencies installed
echo "Checking dependencies..."
if ! python3 -c "import pyaudio" 2>/dev/null; then
    echo "❌ PyAudio not installed. Run: ./install.sh"
    exit 1
fi

if ! python3 -c "import openwakeword" 2>/dev/null; then
    echo "❌ openwakeword not installed. Run: ./install.sh"
    exit 1
fi

if ! python3 -c "import websockets" 2>/dev/null; then
    echo "❌ websockets not installed. Run: ./install.sh"
    exit 1
fi

echo "✅ All dependencies installed"
echo ""

# List audio devices
echo "Audio devices:"
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'  [{i}] {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count()) if p.get_device_info_by_index(i)['maxInputChannels'] > 0]"
echo ""

# Run the agent
echo "Starting audio agent..."
echo "Press Ctrl+C to stop"
echo "Say 'hey Jarvis' to test wake word detection"
echo ""

python3 -m audio_agent.main
