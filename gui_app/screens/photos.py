import os
import random
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap
from ..styles import Styles

class PhotoAlbumScreen(QWidget):
    def __init__(self, photo_dir=None):
        super().__init__()
        # Default to standard Pictures directory if none provided
        if photo_dir is None:
            photo_dir = os.path.expanduser("~/Pictures")
        
        self.photo_dir = photo_dir
        self.image_files = []
        self.current_index = 0
        
        self.init_ui()
        self.scan_photos()
        
        # Change photo every 30 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_photo)
        self.timer.start(30000) 

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel("No Photos Found")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(f"color: {Styles.TEXT_COLOR}; font-size: 24px;")
        
        # Ensure image scales
        self.image_label.setScaledContents(True) # Note: QLabel scaling can be tricky with aspect ratio
        # Better approach for aspect ratio is custom paintEvent or setting pixmap manually with scaling
        
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def scan_photos(self):
        if not os.path.exists(self.photo_dir):
            return
            
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        self.image_files = [
            os.path.join(self.photo_dir, f) 
            for f in os.listdir(self.photo_dir) 
            if f.lower().endswith(valid_extensions)
        ]
        
        if self.image_files:
            random.shuffle(self.image_files)
            self.show_photo(0)

    def show_photo(self, index):
        if not self.image_files:
            return

        image_path = self.image_files[index]
        pixmap = QPixmap(image_path)
        
        if not pixmap.isNull():
            # Scale to fit window while keeping aspect ratio
            # We need the label size, but it might not be layouted yet.
            # Ideally we scale in resizeEvent, but for MVP:
            scaled_pixmap = pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            # Use setPixmap on a centered label (not scaledContents=True) to keep aspect ratio
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("") # Clear text
        else:
            self.image_label.setText("Could not load image")

    def next_photo(self):
        if not self.image_files:
            self.scan_photos() # Retry scanning
            return
            
        self.current_index = (self.current_index + 1) % len(self.image_files)
        self.show_photo(self.current_index)

    def resizeEvent(self, event):
        # Reliably handle resizing
        if self.image_files:
            self.show_photo(self.current_index)
        super().resizeEvent(event)
