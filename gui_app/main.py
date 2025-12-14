import sys
import os
import signal

# Add the parent directory to sys.path to allow imports from gui_app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from PySide6.QtWidgets import QApplication
from gui_app.window import MainWindow
from gui_app.audio_integration import AudioWorker

def main():
    # Allow Ctrl+C to exit
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    if "--fullscreen" in sys.argv:
        window.showFullScreen()
    else:
        window.show()
    
    # Start Audio Agent Worker
    worker = AudioWorker()
    worker.transcription_received.connect(window.update_transcription)
    worker.state_changed.connect(window.update_state)
    
    # Only start audio agent if not in mock test mode
    if "--test-mock" in sys.argv:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: window.update_transcription("Listening..."))
        QTimer.singleShot(4000, lambda: window.update_transcription("Hello World! This is a test."))
        QTimer.singleShot(7000, lambda: window.update_transcription(""))
    else:
        worker.start()

    ret = app.exec()
    
    # Cleanup
    worker.stop_agent()
    sys.exit(ret)

if __name__ == "__main__":
    main()
