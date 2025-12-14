"""Audio capture module using PyAudio."""

import logging
import pyaudio
import numpy as np
from typing import Generator

logger = logging.getLogger(__name__)


class AudioCapture:
    """Handles audio capture from microphone."""

    def __init__(self, device_index: int, sample_rate: int, channels: int, chunk_size: int):
        """
        Initialize audio capture.

        Args:
            device_index: Index of the audio input device
            sample_rate: Sample rate in Hz (16000 for speech)
            channels: Number of audio channels (1 for mono)
            chunk_size: Number of frames per buffer
        """
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = pyaudio.paInt16

        self.pyaudio = pyaudio.PyAudio()
        self.stream = None

    def start(self) -> None:
        """Start audio capture stream."""
        try:
            logger.info(
                f"Opening audio stream: device={self.device_index}, "
                f"rate={self.sample_rate}, channels={self.channels}"
            )
            self.stream = self.pyaudio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
            )
            logger.info("Audio stream opened successfully")
        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            raise

    def stop(self) -> None:
        """Stop audio capture stream."""
        if self.stream:
            logger.info("Closing audio stream")
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def read_chunk(self) -> np.ndarray:
        """
        Read a single audio chunk.

        Returns:
            Audio data as numpy array of int16 samples
        """
        if not self.stream:
            raise RuntimeError("Audio stream not started")

        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            # Convert bytes to numpy array of int16
            audio_array = np.frombuffer(data, dtype=np.int16)
            return audio_array
        except Exception as e:
            logger.error(f"Error reading audio chunk: {e}")
            raise

    def stream_chunks(self) -> Generator[np.ndarray, None, None]:
        """
        Generator that yields audio chunks continuously.

        Yields:
            Audio chunks as numpy arrays
        """
        while True:
            yield self.read_chunk()

    def get_device_info(self) -> dict:
        """Get information about the audio device."""
        try:
            info = self.pyaudio.get_device_info_by_index(self.device_index)
            return info
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return {}

    def list_devices(self) -> None:
        """List all available audio devices."""
        logger.info("Available audio devices:")
        for i in range(self.pyaudio.get_device_count()):
            info = self.pyaudio.get_device_info_by_index(i)
            logger.info(f"  [{i}] {info['name']} (inputs: {info['maxInputChannels']})")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        self.pyaudio.terminate()
