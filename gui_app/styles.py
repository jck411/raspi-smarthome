from PySide6.QtGui import QColor, QFont

class Styles:
    # Colors
    BACKGROUND_COLOR = "#121212"  # Deep dark gray/black
    TEXT_COLOR = "#FFFFFF"
    ACCENT_COLOR = "#00ADB5"      # Teal accent
    OVERLAY_BG = "rgba(0, 0, 0, 180)" # Semi-transparent black

    # Fonts
    @staticmethod
    def get_clock_font(size=120):
        font = QFont("Arial", size, QFont.Weight.Bold)
        return font
    
    @staticmethod
    def get_date_font(size=32):
        font = QFont("Arial", size, QFont.Weight.Normal)
        return font

    @staticmethod
    def get_transcription_font(size=24):
        font = QFont("Arial", size, QFont.Weight.Medium)
        return font

    # Stylesheets
    MAIN_WINDOW_STYLE = f"""
        QMainWindow {{
            background-color: {BACKGROUND_COLOR};
        }}
        QWidget {{
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
        }}
    """
