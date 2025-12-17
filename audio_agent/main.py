"""Main audio agent with state machine."""

import logging
import asyncio
import sys
from enum import Enum
from datetime import datetime
from typing import Optional

import numpy as np

from .config import Config
from .audio_capture import AudioCapture
from .wake_word import WakeWordDetector
from .websocket_client import WebSocketClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/audio_agent.log')
    ]
)

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Audio agent states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class AudioAgent:
    """Main audio agent orchestrating wake word detection and audio streaming."""

    def __init__(self, config: Config):
        """
        Initialize audio agent.

        Args:
            config: Application configuration
        """
        self.config = config
        self.state = AgentState.IDLE
        
        # Initialize components
        self.audio = AudioCapture(
            device_index=config.audio.device_index,
            sample_rate=config.audio.sample_rate,
            channels=config.audio.channels,
            chunk_size=config.audio.chunk_size,
        )
        
        self.wake_word = WakeWordDetector(
            model_name=config.wake_word.model_name,
            threshold=config.wake_word.threshold,
        )
        
        self.ws_client = WebSocketClient(
            url=config.backend_ws_url,
            client_id=config.client_id,
            heartbeat_interval=config.session.heartbeat_interval,
        )
        
        # Streaming state
        self.is_streaming = False
        self.stream_sequence = 0
        self.last_wake_event = datetime.min
        
        # Register WebSocket event handlers
        self.ws_client.on_state_change = self.handle_state_change
        self.ws_client.on_interrupt_tts = self.handle_interrupt_tts
        self.ws_client.on_session_reset = self.handle_session_reset
        self.ws_client.on_tool_status = self.handle_tool_status

    async def start(self) -> None:
        """Start the audio agent."""
        logger.info("Starting Audio Agent...")
        logger.info(f"Client ID: {self.config.client_id}")
        logger.info(f"Backend URL: {self.config.backend_ws_url}")
        
        # List audio devices
        self.audio.list_devices()
        
        # Load wake word model
        self.wake_word.load_model()
        logger.info(f"Wake word model info: {self.wake_word.get_model_info()}")
        
        # Start audio capture
        self.audio.start()
        logger.info("Audio capture started")
        
        # Initial connection to backend
        try:
            await self.ws_client.connect()
        except Exception as e:
            logger.warning(f"Initial connection failed: {e}, will retry...")
        
        # Start in IDLE, waiting for wake word
        logger.info("🎤 Listening for wake word...")
        
        # Start tasks - the connection_manager_loop handles reconnection
        tasks = [
            asyncio.create_task(self.audio_processing_loop()),
            asyncio.create_task(self.connection_manager_loop()),
            asyncio.create_task(self.heartbeat_loop()),
        ]
        
        logger.info("Audio Agent running. Press Ctrl+C to stop.")
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            await self.stop()

    async def connection_manager_loop(self) -> None:
        """Manage WebSocket connection with automatic reconnection."""
        reconnect_delay = 3  # seconds
        
        while True:
            try:
                # Ensure we're connected
                if not self.ws_client.connected:
                    logger.info("WebSocket not connected, attempting to connect...")
                    try:
                        await self.ws_client.connect()
                        logger.info("✅ WebSocket reconnected successfully")
                    except Exception as e:
                        logger.error(f"Failed to connect: {e}")
                        await asyncio.sleep(reconnect_delay)
                        continue
                
                # Run the receive loop - this will exit when connection closes
                await self.ws_client.receive_messages()
                
                # If we get here, connection was closed
                logger.warning("WebSocket connection lost, will reconnect...")
                self.ws_client.connected = False
                
            except Exception as e:
                logger.error(f"Connection manager error: {e}")
                self.ws_client.connected = False
            
            # Wait before reconnecting
            await asyncio.sleep(reconnect_delay)

    async def stop(self) -> None:
        """Stop the audio agent."""
        logger.info("Stopping Audio Agent...")
        self.audio.stop()
        await self.ws_client.disconnect()
        logger.info("Audio Agent stopped")

    async def audio_processing_loop(self) -> None:
        """Main loop: process audio chunks for wake word and streaming."""
        logger.info("Audio processing loop started")
        
        while True:
            try:
                # Read audio chunk
                audio_chunk = self.audio.read_chunk()
                
                # Always run wake word detection (even during streaming/speaking)
                detected, confidence = self.wake_word.detect(audio_chunk)
                
                if detected:
                    await self.handle_wake_word(confidence)
                
                # Stream audio to backend if in LISTENING state
                if self.is_streaming:
                    # Get raw bytes directly from audio chunk
                    # audio_chunk is numpy array - convert to bytes properly for Deepgram
                    audio_bytes = audio_chunk.astype(np.int16).tobytes()
                    await self.ws_client.send_audio_chunk(audio_bytes, self.stream_sequence)
                    self.stream_sequence += 1
                
                # Small delay to prevent CPU overload
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Error in audio processing loop: {e}")
                await asyncio.sleep(1)

    async def handle_wake_word(self, confidence: float) -> None:
        """
        Handle wake word detection.

        Args:
            confidence: Detection confidence score
        """
        # Cooldown check to prevent spamming from single utterance
        if (datetime.now() - self.last_wake_event).total_seconds() < 1.0:
            return

        self.last_wake_event = datetime.now()

        if self.state == AgentState.IDLE:
            # Wake word detected - immediately start listening (don't wait for backend)
            logger.info(f"🎙️ Wake word detected! (confidence: {confidence:.3f})")
            
            # Start listening immediately (Pi controls its own state)
            self.state = AgentState.LISTENING
            self.start_streaming()
            
            # Notify backend (for transcript processing)
            await self.ws_client.send_wake_word_detected(confidence)
            
        elif self.state == AgentState.SPEAKING:
            # Barge-in: wake word during TTS playback
            logger.info(f"🛑 Wake word BARGE-IN detected during SPEAKING (confidence: {confidence:.3f})")
            
            # IMMEDIATELY mute the speaker at OS level - no network latency!
            import subprocess
            try:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], 
                              timeout=0.1, check=False, capture_output=True)
                logger.info("🔇 Speaker muted locally")
            except Exception as e:
                logger.warning(f"Failed to mute speaker: {e}")
            
            # Notify backend (so it can send interrupt_tts to frontend)
            await self.ws_client.send_wake_word_barge_in(confidence)
            
            # Small delay for the mute to take effect and any residual audio to clear
            await asyncio.sleep(0.3)
            
            # Unmute speaker (TTS should be stopped by now)
            try:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], 
                              timeout=0.1, check=False, capture_output=True)
                logger.info("🔊 Speaker unmuted")
            except Exception as e:
                logger.warning(f"Failed to unmute speaker: {e}")
            
            # Now start listening
            self.state = AgentState.LISTENING
            self.start_streaming()

    def handle_state_change(self, new_state: str) -> None:
        """
        Handle state change command from backend.

        Args:
            new_state: New state to transition to
        """
        try:
            old_state = self.state
            self.state = AgentState(new_state)
            logger.info(f"State transition: {old_state.value} -> {self.state.value}")
            
            # Handle state-specific actions
            if self.state == AgentState.LISTENING:
                self.start_streaming()
            elif self.state == AgentState.IDLE:
                self.stop_streaming()
            elif self.state == AgentState.PROCESSING:
                self.stop_streaming()
            
        except ValueError:
            logger.error(f"Invalid state received: {new_state}")

    def handle_interrupt_tts(self) -> None:
        """Handle TTS interrupt command from backend."""
        logger.info("TTS interrupt received")
        # In a full implementation, this would stop audio playback
        # For now, just acknowledge
        pass

    def handle_session_reset(self) -> None:
        """Handle session reset command from backend."""
        logger.info("Session reset received")
        self.stop_streaming()
        self.wake_word.reset()
        self.state = AgentState.IDLE

    def handle_tool_status(self, status: str, name: str) -> None:
        """Handle tool status updates from backend."""
        if status == "started":
            logger.info(f"🔧 Tool starting: {name}")
        elif status == "finished":
            logger.info(f"✅ Tool finished: {name}")
        elif status == "error":
            logger.warning(f"❌ Tool error: {name}")

    def start_streaming(self) -> None:
        """Start streaming audio to backend."""
        if not self.is_streaming:
            logger.info("🔴 Starting audio streaming to backend")
            self.is_streaming = True
            self.stream_sequence = 0

    def stop_streaming(self) -> None:
        """Stop streaming audio to backend."""
        if self.is_streaming:
            logger.info("⏹️ Stopping audio streaming")
            self.is_streaming = False
            self.stream_sequence = 0

    async def heartbeat_loop(self) -> None:
        """Send periodic heartbeat to backend."""
        while True:
            # Send heartbeat more frequently during SPEAKING to keep connection alive
            # (since we're not sending audio chunks during TTS)
            if self.state == AgentState.SPEAKING:
                interval = 2  # more frequent during TTS
            else:
                interval = self.config.session.heartbeat_interval
            
            await asyncio.sleep(interval)
            
            if self.ws_client.connected:
                await self.ws_client.send_heartbeat()


async def main():
    """Main entry point."""
    # Load configuration
    config = Config.from_env()
    
    # Set log level
    logging.getLogger().setLevel(config.log_level)
    
    # Create and start agent
    agent = AudioAgent(config)
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
