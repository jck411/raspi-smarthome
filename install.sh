#!/bin/bash
# Installation script for audio agent

set -e

echo "=== Audio Agent Installation Script ==="
echo ""

# Check if running on Pi
if [ ! -f /proc/cpuinfo ] || ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it first:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y portaudio19-dev

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo ""
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the cargo env to make uv available in current shell
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo ""
    echo "uv is already installed"
fi

# Install dependencies using uv sync
echo ""
echo "Syncing dependencies with uv..."
uv sync

# Test audio device
echo ""
echo "Testing audio devices..."
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f\"[{i}] {p.get_device_info_by_index(i)['name']}\") for i in range(p.get_device_count())]"

# Install systemd service
echo ""
read -p "Install as systemd service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing systemd service..."
    sudo cp audio_agent.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable audio_agent.service
    echo ""
    echo "Service installed successfully!"
    echo ""
    echo "To start the service:"
    echo "  sudo systemctl start audio_agent"
    echo ""
    echo "To view logs:"
    echo "  sudo journalctl -u audio_agent -f"
    echo ""
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To test manually (without systemd):"
echo "  python3 -m audio_agent.main"
echo ""
