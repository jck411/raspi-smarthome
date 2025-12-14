"""Configuration management for audio agent."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AudioConfig:
    """Audio capture configuration."""
    device_index: int
    sample_rate: int
    channels: int
    chunk_size: int


@dataclass
class WakeWordConfig:
    """Wake word detection configuration."""
    model_name: str
    threshold: float


@dataclass
class SessionConfig:
    """Session timeout configuration."""
    silence_timeout: int
    max_duration: int
    heartbeat_interval: int


@dataclass
class Config:
    """Main application configuration."""
    backend_ws_url: str
    client_id: str
    audio: AudioConfig
    wake_word: WakeWordConfig
    session: SessionConfig
    log_level: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            backend_ws_url=os.getenv("BACKEND_WS_URL", "ws://localhost:8000/api/voice/connect"),
            client_id=os.getenv("CLIENT_ID", "pi-default"),
            audio=AudioConfig(
                device_index=int(os.getenv("AUDIO_DEVICE_INDEX", "2")),
                sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
                channels=int(os.getenv("AUDIO_CHANNELS", "1")),
                chunk_size=int(os.getenv("AUDIO_CHUNK_SIZE", "1024")),
            ),
            wake_word=WakeWordConfig(
                model_name=os.getenv("WAKE_WORD_MODEL", "hey_jarvis_v0.1.onnx"),
                threshold=float(os.getenv("WAKE_WORD_THRESHOLD", "0.5")),
            ),
            session=SessionConfig(
                silence_timeout=int(os.getenv("SILENCE_TIMEOUT", "10")),
                max_duration=int(os.getenv("MAX_SESSION_DURATION", "60")),
                heartbeat_interval=int(os.getenv("HEARTBEAT_INTERVAL", "10")),
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
