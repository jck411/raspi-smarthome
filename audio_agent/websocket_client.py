"""WebSocket client for backend communication."""

import logging
import asyncio
import json
import base64
from typing import Callable, Optional
import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for communicating with backend server."""

    def __init__(self, url: str, client_id: str, heartbeat_interval: int = 10):
        """
        Initialize WebSocket client.

        Args:
            url: WebSocket server URL (e.g., ws://192.168.1.100:8000/api/voice/connect)
            client_id: Unique identifier for this client
            heartbeat_interval: Seconds between heartbeat messages
        """
        self.url = url
        self.client_id = client_id
        self.heartbeat_interval = heartbeat_interval
        
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_delay = 3
        
        # Event handlers
        self.on_state_change: Optional[Callable[[str], None]] = None
        self.on_interrupt_tts: Optional[Callable[[], None]] = None
        self.on_tts_audio: Optional[Callable[[bytes, str], None]] = None
        self.on_session_reset: Optional[Callable[[], None]] = None
        self.on_transcript: Optional[Callable[[str, bool], None]] = None

    async def connect(self) -> None:
        """Establish WebSocket connection to backend."""
        try:
            logger.info(f"Connecting to backend: {self.url}")
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            logger.info("WebSocket connected successfully")
            
            # Send connection ready message
            await self.send_event("connection_ready", {
                "client_id": self.client_id,
                "timestamp": self._get_timestamp()
            })
            
        except Exception as e:
            logger.error(f"Failed to connect to backend: {e}")
            self.connected = False
            raise

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.websocket:
            logger.info("Disconnecting from backend")
            await self.websocket.close()
            self.websocket = None
            self.connected = False

    async def send_event(self, event_type: str, data: dict) -> None:
        """
        Send an event to the backend.

        Args:
            event_type: Type of event (e.g., 'wakeword_detected', 'audio_chunk')
            data: Event payload
        """
        if not self.connected or not self.websocket:
            logger.warning(f"Cannot send event {event_type}: not connected")
            return

        message = {
            "type": event_type,
            "data": data
        }

        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent event: {event_type}")
        except Exception as e:
            logger.error(f"Failed to send event {event_type}: {e}")
            self.connected = False

    async def send_wake_word_detected(self, confidence: float) -> None:
        """Send wake word detection event."""
        await self.send_event("wakeword_detected", {
            "confidence": confidence,
            "timestamp": self._get_timestamp()
        })

    async def send_wake_word_barge_in(self, confidence: float) -> None:
        """Send wake word barge-in event (during speaking)."""
        await self.send_event("wakeword_barge_in", {
            "confidence": confidence,
            "timestamp": self._get_timestamp()
        })

    async def send_audio_chunk(self, audio_data: bytes, sequence: int) -> None:
        """
        Send audio chunk to backend.

        Args:
            audio_data: Raw audio bytes (PCM 16-bit)
            sequence: Sequence number for ordering
        """
        # Convert audio to base64 for JSON transmission
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        await self.send_event("audio_chunk", {
            "audio": audio_b64,
            "seq": sequence
        })

    async def send_stream_end(self, reason: str) -> None:
        """Send stream end notification."""
        await self.send_event("stream_end", {
            "reason": reason
        })

    async def send_heartbeat(self) -> None:
        """Send heartbeat to keep connection alive."""
        await self.send_event("heartbeat", {
            "timestamp": self._get_timestamp()
        })

    async def receive_messages(self) -> None:
        """Listen for messages from backend and dispatch to handlers."""
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            self.connected = False

    async def _handle_message(self, message: str) -> None:
        """Process incoming message from backend."""
        try:
            data = json.loads(message)
            event_type = data.get("type")
            payload = data.get("data", {})

            logger.debug(f"Received event: {event_type}")

            if event_type == "set_state":
                state = payload.get("state")
                if self.on_state_change and state:
                    self.on_state_change(state)

            elif event_type == "interrupt_tts":
                if self.on_interrupt_tts:
                    self.on_interrupt_tts()

            elif event_type == "tts_audio":
                audio_b64 = payload.get("audio")
                audio_format = payload.get("format", "pcm")
                if self.on_tts_audio and audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    self.on_tts_audio(audio_bytes, audio_format)

            elif event_type == "session_reset":
                if self.on_session_reset:
                    self.on_session_reset()

            elif event_type == "transcript":
                text = payload.get("text")
                is_final = payload.get("is_final", False)
                if self.on_transcript and text:
                    self.on_transcript(text, is_final)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def run_with_reconnect(self, receive_handler: Callable) -> None:
        """
        Run WebSocket client with automatic reconnection.

        Args:
            receive_handler: Async function to handle incoming messages
        """
        while True:
            try:
                await self.connect()
                await receive_handler()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                
            self.connected = False
            logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
            await asyncio.sleep(self.reconnect_delay)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
