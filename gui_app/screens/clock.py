from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt, QTime, QDate
from .styles import Styles  # Relative import within the package

class ClockScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000) # Update every second
        
        self.update_time()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(Styles.get_clock_font(140))
        self.time_label.setStyleSheet(f"color: {Styles.TEXT_COLOR}; background-color: transparent;")
        
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setFont(Styles.get_date_font(40))
        self.date_label.setStyleSheet(f"color: {Styles.ACCENT_COLOR}; background-color: transparent;")

        layout.addWidget(self.time_label)
        layout.addSpacing(20)
        layout.addWidget(self.date_label)
        
        self.setLayout(layout)

    def update_time(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        
        # Format: HH:MM
        self.time_label.setText(current_time.toString("HH:mm"))
        
        # Format: dddd, MMMM d
        self.date_label.setText(current_date.toString("dddd, MMMM d"))
