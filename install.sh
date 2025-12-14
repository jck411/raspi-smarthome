#!/bin/bash
set -e

echo "======================================"
echo "  Raspberry Pi Audio Agent Installer"
echo "======================================"
echo ""

# Check if we're on a Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "✓ Detected: $MODEL"
else
    echo "⚠ Warning: Not running on Raspberry Pi hardware"
fi

echo ""
echo "Step 1: Installing system dependencies..."
echo "-------------------------------------------"

# Install portaudio (required for PyAudio)
if ! dpkg -l | grep -q libportaudio2; then
    echo "Installing portaudio..."
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev
    echo "✓ Portaudio installed"
else
    echo "✓ Portaudio already installed"
fi

echo ""
echo "Step 2: Installing uv package manager..."
echo "-------------------------------------------"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for this session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    echo "✓ uv installed"
else
    echo "✓ uv already installed"
fi

echo ""
echo "Step 3: Installing Python dependencies..."
echo "-------------------------------------------"

# Install Python packages using uv
echo "Installing packages..."
uv sync

echo ""
echo "✓ All Python dependencies installed"

echo ""
echo "Step 4: Verifying audio devices..."
echo "-------------------------------------------"

# List available audio devices
echo "Available audio devices:"
python3 -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f'  [{i}] {info[\"name\"]} (inputs: {info[\"maxInputChannels\"]})')
p.terminate()
" || echo "⚠ Could not list audio devices. PyAudio may not be installed correctly."

echo ""
echo "Step 5: Configuration..."
echo "-------------------------------------------"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠ IMPORTANT: Edit .env file to configure:"
    echo "  - BACKEND_WS_URL: Your backend server IP"
    echo "  - AUDIO_DEVICE_INDEX: ReSpeaker device index (check list above)"
    echo "  - CLIENT_ID: Unique identifier for this Pi"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Step 6: Systemd service installation (optional)..."
echo "-------------------------------------------"

read -p "Do you want to install as a systemd service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Get absolute path to project directory
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Update service file with correct paths
    sed "s|/home/pi/raspi-smarthome|$PROJECT_DIR|g" audio_agent.service | \
    sed "s|User=pi|User=$USER|g" | \
    sudo tee /etc/systemd/system/audio_agent.service > /dev/null
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    echo "✓ Systemd service installed"
    echo ""
    echo "To control the service:"
    echo "  sudo systemctl start audio_agent     # Start service"
    echo "  sudo systemctl stop audio_agent      # Stop service"
    echo "  sudo systemctl enable audio_agent    # Enable on boot"
    echo "  sudo journalctl -u audio_agent -f   # View logs"
else
    echo "Skipped systemd service installation"
    echo ""
    echo "To run manually:"
    echo "  python3 -m audio_agent.main"
fi

echo ""
echo "======================================"
echo "  Installation Complete! 🎉"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env to configure backend URL and audio device"
echo "  2. Test manually: python3 -m audio_agent.main"
echo "  3. Say 'hey Jarvis' to test wake word detection"
echo ""
