"""Wake word detection using openwakeword."""

import logging
import numpy as np
from openwakeword.model import Model as WakeWordModel

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Detects wake words in audio stream using openwakeword."""

    def __init__(self, model_name: str, threshold: float = 0.5):
        """
        Initialize wake word detector.

        Args:
            model_name: Name of the wake word model (e.g., 'hey_jarvis_v0.1.onnx')
            threshold: Detection confidence threshold (0.0 to 1.0)
        """
        self.model_name = model_name
        self.threshold = threshold
        self.model = None

    def load_model(self) -> None:
        """Load the wake word model."""
        try:
            logger.info(f"Loading wake word model: {self.model_name}")
            
            # Check if it's a path to a local file
            import os
            local_path = os.path.join(os.getcwd(), "models", self.model_name)
            logger.info(f"Checking for model at: {local_path}")
            
            if os.path.exists(local_path):
                logger.info(f"Found local model file: {local_path}")
                self.model = WakeWordModel(wakeword_models=[local_path])
            else:
                logger.info(f"Local model not found, trying built-in models")
                # openwakeword will auto-download models if not found
                self.model = WakeWordModel(wakeword_models=[self.model_name])
            
            logger.info(f"Wake word model loaded successfully with threshold {self.threshold}")
        except Exception as e:
            logger.error(f"Failed to load wake word model: {e}")
            raise

    def detect(self, audio_chunk: np.ndarray) -> tuple[bool, float]:
        """
        Process audio chunk and detect wake word.

        Args:
            audio_chunk: Audio data as numpy array of int16 samples

        Returns:
            Tuple of (detected: bool, confidence: float)
        """
        if self.model is None:
            raise RuntimeError("Wake word model not loaded")

        try:
            # openwakeword expects audio as numpy array
            prediction = self.model.predict(audio_chunk)
            
            # Get the highest confidence score from all models
            # prediction is a dict with model names as keys
            max_confidence = 0.0
            for model_name, score in prediction.items():
                if score > max_confidence:
                    max_confidence = score

            detected = max_confidence >= self.threshold

            if detected:
                logger.info(f"Wake word detected! Confidence: {max_confidence:.3f}")

            return detected, max_confidence

        except Exception as e:
            logger.error(f"Error during wake word detection: {e}")
            return False, 0.0

    def reset(self) -> None:
        """Reset the wake word model state."""
        if self.model:
            self.model.reset()
            logger.debug("Wake word model reset")

    def get_model_info(self) -> dict:
        """Get information about loaded models."""
        if not self.model:
            return {}
        
        return {
            "models": list(self.model.models.keys()) if hasattr(self.model, 'models') else [],
            "threshold": self.threshold,
        }
