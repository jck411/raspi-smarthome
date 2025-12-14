import asyncio
import logging
from PySide6.QtCore import QThread, Signal

# Import Audio Agent components
# Assumes sys.path is correct (handled in main.py)
from audio_agent.config import Config
from audio_agent.main import AudioAgent

logger = logging.getLogger(__name__)

class AudioWorker(QThread):
    # Signals to update GUI
    transcription_received = Signal(str, bool) # text, is_final
    state_changed = Signal(str) # new_state
    
    def __init__(self):
        super().__init__()
        self.loop = None
        self.agent = None

    def run(self):
        """Run the asyncio loop in this thread."""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Load config and create agent
            config = Config.from_env()
            self.agent = AudioAgent(config)
            
            # Hook up callbacks
            # We wrap them to emit signals via the thread-safe Qt mechanism
            original_on_transcript = self.agent.ws_client.on_transcript
            
            def on_transcript_wrapper(text, is_final):
                self.transcription_received.emit(text, is_final)
                if original_on_transcript:
                    original_on_transcript(text, is_final)
            
            original_on_state = self.agent.ws_client.on_state_change
            
            def on_state_wrapper(state):
                self.state_changed.emit(state)
                if original_on_state:
                    original_on_state(state)

            self.agent.ws_client.on_transcript = on_transcript_wrapper
            self.agent.ws_client.on_state_change = on_state_wrapper
            
            # Run the agent
            self.loop.run_until_complete(self.agent.start())
            
        except Exception as e:
            logger.error(f"AudioWorker failed: {e}")
        finally:
            if self.loop:
                self.loop.close()

    def stop_agent(self):
        """Stop the agent cleanly."""
        if self.loop and self.agent:
            # Schedule the stop coroutine in the running loop
            self.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.agent.stop())
            )
        self.quit()
        self.wait()
