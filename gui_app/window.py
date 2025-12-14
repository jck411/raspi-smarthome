from PySide6.QtWidgets import QMainWindow, QStackedWidget, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent

from .screens.clock import ClockScreen
from .screens.photos import PhotoAlbumScreen
from .styles import Styles

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Home Assistant")
        self.setGeometry(0, 0, 800, 480) # Std Raspberry Pi Touchscreen Res
        
        # Styles
        self.setStyleSheet(Styles.MAIN_WINDOW_STYLE)

        # Central Widget & Stack
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # Add Screens
        self.clock_screen = ClockScreen()
        self.photo_screen = PhotoAlbumScreen()
        
        self.stack.addWidget(self.clock_screen)
        self.stack.addWidget(self.photo_screen)
        
        # Transcription Overlay
        self.overlay_label = QLabel(self)
        self.overlay_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.overlay_label.setWordWrap(True)
        self.overlay_label.setFont(Styles.get_transcription_font(28))
        self.overlay_label.setStyleSheet(f"""
            background-color: {Styles.OVERLAY_BG};
            color: {Styles.TEXT_COLOR};
            padding: 20px;
            border-radius: 15px;
            margin: 20px;
        """)
        self.overlay_label.hide() # Hidden by default
        
        # Swipe Logic Vars
        self.drag_start_pos = None

    def resizeEvent(self, event):
        # Position overlay at bottom center, with some margin
        rect = self.geometry()
        overlay_height = 100
        margin = 20
        self.overlay_label.setGeometry(
            margin, 
            rect.height() - overlay_height - margin, 
            rect.width() - (margin * 2), 
            overlay_height
        )
        super().resizeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.drag_start_pos:
            drag_end_pos = event.pos()
            delta = drag_end_pos - self.drag_start_pos
            
            # Threshold for swipe
            min_swipe = 50
            
            if abs(delta.x()) > min_swipe:
                if delta.x() > 0: # Swipe Right -> Previous
                    self.prev_screen()
                else: # Swipe Left -> Next
                    self.next_screen()
            
            self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    def next_screen(self):
        idx = self.stack.currentIndex()
        if idx < self.stack.count() - 1:
            self.stack.setCurrentIndex(idx + 1)
        else:
            self.stack.setCurrentIndex(0) # Loop

    def prev_screen(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
        else:
            self.stack.setCurrentIndex(self.stack.count() - 1) # Loop

    def update_transcription(self, text):
        if text:
            # If text is received, ensure overlay is shown
            self.overlay_label.setText(text)
            self.overlay_label.show()
            self.overlay_label.raise_()
            
            # Reset style to default if it was changed by state
            self.overlay_label.setStyleSheet(f"""
                background-color: {Styles.OVERLAY_BG};
                color: {Styles.TEXT_COLOR};
                padding: 20px;
                border-radius: 15px;
                margin: 20px;
            """)
        else:
            self.overlay_label.hide()

    def update_state(self, state):
        # Map states to UI feedback
        # IDLE, LISTENING, PROCESSING, SPEAKING
        state = state.lower()
        
        if state == "idle":
            self.overlay_label.hide()
            
        elif state == "listening":
            self.overlay_label.setText("Listening...")
            self.overlay_label.show()
            self.overlay_label.setStyleSheet(f"""
                background-color: {Styles.ACCENT_COLOR};
                color: {Styles.TEXT_COLOR};
                padding: 20px;
                border-radius: 15px;
                margin: 20px;
            """)
            self.overlay_label.raise_()
            
        elif state == "processing":
            self.overlay_label.setText("Thinking...")
            self.overlay_label.setStyleSheet(f"""
                background-color: {Styles.OVERLAY_BG};
                color: {Styles.ACCENT_COLOR};
                padding: 20px;
                border-radius: 15px;
                margin: 20px;
                border: 2px solid {Styles.ACCENT_COLOR};
            """)
            
        elif state == "speaking":
            # Keep showing the last transcript or "Speaking..."?
            # Usually we want to assume the text displayed IS what is being spoken 
            # if we had full sync. But here we might just show the indicator.
            pass
