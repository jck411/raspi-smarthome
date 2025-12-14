# Implementation Plan - Raspberry Pi GUI (Phase 2)

Goal: Create a sleek, modern, swipeable GUI for the Raspberry Pi Voice Assistant using PySide6.
Features: Clock, Photo Album, and Live Transcription display.

## User Review Required
> [!IMPORTANT]
> This requires installing `PySide6` on the Raspberry Pi. This can sometimes be tricky on ARM architectures. We will assume standard `pip install PySide6` works, but might need system packages (`sudo apt install python3-pyside6`) if pip fails.

## Proposed Changes

### `raspi-smarthome/requirements.txt`
- [MODIFY] Add `PySide6`
- [MODIFY] Add `python-dateutil` (optional, for easy time formatting if needed)

### `raspi-smarthome/gui_app/` [NEW DIRECTORY]

#### [NEW] `gui_app/main.py`
- Entry point for the GUI application.
- Sets up `QApplication` and the main `MainWindow`.

#### [NEW] `gui_app/window.py`
- Defines `MainWindow`.
- Uses `QStackedWidget` for managing screens (Clock, Photos).
- Implements "swipe" gestures (mouse/touch events) to switch indices.
- Contains a "Transcription Overlay" (floating text label) that appears when voice is active.

#### [NEW] `gui_app/screens/clock.py`
- `ClockScreen` widget.
- Large, modern typography for time/date.
- Updates every second.

#### [NEW] `gui_app/screens/photos.py`
- `PhotoAlbumScreen` widget.
- Loads images from a local directory (`~/Pictures` or similar).
- Cycles through photos automatically or via interaction.

#### [NEW] `gui_app/styles.py`
- Defines the "sleek" look (fonts, colors, gradients).
- Dark mode compatible.

### Integration with `audio_agent`
The GUI needs to receive events from the Audio Agent (running in a separate thread/process).
- We will modify `audio_agent/main.py` or create a wrapper that runs BOTH the Audio Client and the GUI.
- **Approach**: The GUI is the main thread (`QApplication`). The Audio Client runs in a background thread (`QThread` or `threading.Thread`) and emits Qt Signals (`transcription_received`, `listening_state_changed`) to the GUI to update the UI safely.

## Verification Plan

### Automated
- We can write a test script that instantiates the GUI and simulates signals (text received) to verify the UI updates.

### Manual Verification
1.  **Run locally**: Execute `python gui_app/main.py`.
2.  **Verify Clock**: Check if time updates.
3.  **Verify Photos**: Check if photos load (mock directory).
4.  **Verify Swipe**: Click and drag/swipe to change views.
5.  **Verify Transcription**: Mock a signal to show "Hello World" on the readout.
