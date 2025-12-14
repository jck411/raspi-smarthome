# Raspberry Pi Audio Agent

Smart home voice assistant audio agent for Raspberry Pi 5 with always-on wake word detection and barge-in support.

## Features

- ✅ **Always-on wake word detection** using openwakeword ("hey Jarvis")
- ✅ **OS-level audio capture** from ReSpeaker 4 Mic Array
- ✅ **WebSocket communication** with backend server
- ✅ **Barge-in capable** - detects wake word even during TTS playback
- ✅ **Automatic reconnection** on network drops
- ✅ **Systemd service** with auto-restart

## System Requirements

- Raspberry Pi 5 (tested) or compatible
- ReSpeaker 4 Mic Array USB
- Python 3.11+
- Debian 12 (bookworm) or compatible

## Quick Start

### 1. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

Update `BACKEND_WS_URL` to your backend server's IP:
```
BACKEND_WS_URL=ws://192.168.1.100:8000/api/voice/connect
```

### 2. Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

This will:
- Install system dependencies (portaudio)
- Install **uv** package manager (if not present)
- Install Python packages via uv
- List available audio devices
- Optionally install systemd service

### 3. Verify Audio Device

Check that ReSpeaker is detected:
```bash
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'[{i}] {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
```

Look for device with "ReSpeaker" in the name and note its index (usually 2).
Update `AUDIO_DEVICE_INDEX` in `.env` if needed.

### 4. Test Manually

```bash
python3 -m audio_agent.main
```

Say "hey Jarvis" and watch the logs for detection.

### 5. Run as Service

```bash
# Start service
sudo systemctl start audio_agent

# View logs
sudo journalctl -u audio_agent -f

# Enable on boot
sudo systemctl enable audio_agent
```

## Configuration

All configuration via `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_WS_URL` | WebSocket URL of backend server | `ws://localhost:8000/api/voice/connect` |
| `CLIENT_ID` | Unique identifier for this Pi | `pi-default` |
| `AUDIO_DEVICE_INDEX` | PyAudio device index (ReSpeaker) | `2` |
| `AUDIO_SAMPLE_RATE` | Sample rate in Hz | `16000` |
| `AUDIO_CHANNELS` | Number of channels | `1` (mono) |
| `AUDIO_CHUNK_SIZE` | Frames per buffer | `1024` |
| `WAKE_WORD_MODEL` | openwakeword model name | `hey_jarvis_v0.1.onnx` |
| `WAKE_WORD_THRESHOLD` | Detection threshold (0.0-1.0) | `0.5` |
| `SILENCE_TIMEOUT` | Seconds before timeout | `10` |
| `MAX_SESSION_DURATION` | Max listening duration (sec) | `60` |
| `HEARTBEAT_INTERVAL` | WebSocket heartbeat interval | `10` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Architecture

```
┌─────────────────────────────────────┐
│   Raspberry Pi Audio Agent          │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────┐    ┌──────────────┐  │
│  │ PyAudio  │───>│ Wake Word    │  │
│  │ Capture  │    │ Detection    │  │
│  └──────────┘    └──────────────┘  │
│       │                 │           │
│       │                 v           │
│       │          ┌──────────────┐  │
│       └─────────>│ State        │  │
│                  │ Machine      │  │
│                  └──────────────┘  │
│                        │            │
│                        v            │
│                  ┌──────────────┐  │
│                  │ WebSocket    │  │
│                  │ Client       │  │
│                  └──────────────┘  │
└─────────────────────┬───────────────┘
                      │
                      v
        Backend Server (FastAPI + Deepgram)
```

## State Machine

```
IDLE (wake word only)
  │ wake word detected
  v
LISTENING (stream audio + wake word)
  │ silence/timeout
  v
PROCESSING (backend processing)
  │ response ready
  v
SPEAKING (TTS playback + wake word)
  │ wake word detected (BARGE-IN!)
  └──> back to LISTENING
```

**Key Feature:** Wake word detection runs continuously in ALL states for barge-in capability.

## WebSocket Protocol

### Pi → Backend Messages

| Event | Payload | Trigger |
|-------|---------|---------|
| `connection_ready` | `{client_id, timestamp}` | Initial connection |
| `wakeword_detected` | `{confidence, timestamp}` | Wake word from IDLE |
| `wakeword_barge_in` | `{confidence, timestamp}` | Wake word during SPEAKING |
| `audio_chunk` | `{audio: base64, seq: int}` | Streaming in LISTENING |
| `stream_end` | `{reason: str}` | Stop streaming |
| `heartbeat` | `{timestamp}` | Every 10 seconds |

### Backend → Pi Messages

| Event | Payload | Action |
|-------|---------|--------|
| `set_state` | `{state: str}` | Change agent state |
| `interrupt_tts` | `{}` | Stop TTS playback |
| `tts_audio` | `{audio: base64, format: str}` | Play audio response |
| `session_reset` | `{}` | Reset to IDLE |

## Troubleshooting

### Wake word not detecting

1. Check microphone device index:
   ```bash
   arecord -l
   ```

2. Test audio capture:
   ```bash
   arecord -D hw:2,0 -f S16_LE -r 16000 -d 5 test.wav
   aplay test.wav
   ```

3. Lower wake word threshold in `.env`:
   ```
   WAKE_WORD_THRESHOLD=0.3
   ```

### WebSocket connection fails

1. Check backend is running and accessible
2. Verify `BACKEND_WS_URL` in `.env`
3. Test connectivity:
   ```bash
   ping 192.168.1.100
   ```

### Service not starting

1. Check logs:
   ```bash
   sudo journalctl -u audio_agent -e
   ```

2. Test manually first:
   ```bash
   python3 -m audio_agent.main
   ```

3. Verify dependencies installed:
   ```bash
   uv pip list | grep -E "openwakeword|pyaudio|websockets"
   ```

## Development

### Project Structure

```
raspi-smarthome/
├── audio_agent/
│   ├── __init__.py
│   ├── main.py              # Main orchestrator & state machine
│   ├── config.py            # Configuration management
│   ├── audio_capture.py     # PyAudio interface
│   ├── wake_word.py         # openwakeword integration
│   └── websocket_client.py  # WebSocket communication
├── requirements.txt         # Python dependencies
├── .env.example            # Example configuration
├── .env                    # Your configuration (gitignored)
├── audio_agent.service     # Systemd service definition
├── install.sh              # Installation script
└── README.md               # This file
```

### Testing Without Backend

The agent will continuously retry connection if backend is unavailable. You can test wake word detection locally by watching logs even without backend running.

## Performance

- **Wake word latency:** <150ms (local processing)
- **Memory usage:** ~150MB RSS
- **CPU usage:** ~5-10% on Pi 5 (single core)
- **Network:** ~32 Kbps during audio streaming

## Security Notes

- WebSocket communication is unencrypted (local network only)
- No audio is stored locally
- Audio streams directly to backend, then discarded
- No authentication (add `client_id` verification in production)

## License

See main project LICENSE.

## Next Steps

Once the audio agent is running:

1. **Build backend server** on separate machine (see `implementation_plan.md`)
   - Note: `/home/jck411/Backend_FastAPI` is for reference only, do NOT modify it
   - Backend work happens on a different development machine
2. Configure kiosk UI for visual feedback (future)
3. Add smart home MCP server integration (backend)
4. Train custom wake word (optional)

---

For full system implementation details, see `implementation_plan.md`.
