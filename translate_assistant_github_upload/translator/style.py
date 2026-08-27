from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


# Unified UI size multiplier. Change this value to resize the whole UI.
# Examples: 1.0 = original size, 1.5 = medium, 2.0 = current large size.
UI_SCALE = 1.0

def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "assets").exists():
            return exe_dir
        if (exe_dir.parent / "assets").exists():
            return exe_dir.parent
        return exe_dir
    return Path(__file__).resolve().parent.parent


# Put your custom floating translate icon here:
# E:\demo\python\translate_assistant\assets\translate_icon.png
FLOAT_ICON_PATH = app_base_dir() / "assets" / "translate_icon.png"
TRAY_ICON_PATH = app_base_dir() / "assets" / "tray_icon.png"

# Floating icon/button sizing. These base values are multiplied by UI_SCALE.
FLOAT_BUTTON_WIDTH = 70
FLOAT_BUTTON_HEIGHT = 70
FLOAT_ICON_SIZE = 64
FLOAT_BUTTON_SHOW_FRAME = False

# Floating icon position relative to the mouse release point.
# Smaller values place it closer to the selected text.
FLOAT_OFFSET_X = -500
FLOAT_OFFSET_Y = -200
RESULT_OFFSET_Y = 0


def scaled(value: int | float) -> int:
    return round(value * UI_SCALE)


def float_button_style() -> str:
    if not FLOAT_BUTTON_SHOW_FRAME:
        return f"""
        #translateButtonPopup {{
            background: transparent;
        }}
        #translateButton {{
            background-color: transparent;
            color: #202124;
            border: none;
            border-radius: 0;
            font-size: {scaled(18)}px;
            padding: 0;
        }}
        #translateButton:hover {{
            background-color: transparent;
        }}
        #translateButton:disabled {{
            color: #80868b;
        }}
        """

    return f"""
    #translateButton {{
        background: #202124;
        color: #ffffff;
        border: {scaled(1)}px solid #3c4043;
        border-radius: {scaled(8)}px;
        font-size: {scaled(18)}px;
    }}
    #translateButton:hover {{
        background: #303134;
    }}
    #translateButton:disabled {{
        color: #c0c0c0;
    }}
    """


def apply_global_style(app: QApplication) -> None:
    app.setStyleSheet(
        f"""
        QMenu {{
            font-size: {scaled(13)}px;
            padding: {scaled(6)}px;
        }}
        QMenu::item {{
            min-width: {scaled(96)}px;
            padding: {scaled(9)}px {scaled(18)}px;
        }}
        QMenu::item:selected {{
            background: #e9edf2;
            color: #202124;
        }}
        QDialog, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton {{
            font-size: {scaled(13)}px;
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox {{
            min-height: {scaled(28)}px;
            padding: 0 {scaled(7)}px;
        }}
        QDialogButtonBox QPushButton {{
            min-width: {scaled(76)}px;
            min-height: {scaled(30)}px;
            padding: {scaled(5)}px {scaled(12)}px;
        }}
        """
    )
