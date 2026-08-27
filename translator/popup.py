from __future__ import annotations

import re

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .style import (
    FLOAT_BUTTON_HEIGHT,
    FLOAT_BUTTON_WIDTH,
    FLOAT_ICON_PATH,
    FLOAT_ICON_SIZE,
    FLOAT_OFFSET_X,
    FLOAT_OFFSET_Y,
    RESULT_OFFSET_Y,
    float_button_style,
    scaled,
)


def _clamp_to_screen(widget: QWidget, point: QPoint) -> QPoint:
    screen = QGuiApplication.screenAt(point) or QGuiApplication.primaryScreen()
    geometry = screen.availableGeometry()
    widget.adjustSize()
    size = widget.size()
    x = max(geometry.left(), min(point.x(), geometry.right() - size.width()))
    y = max(geometry.top(), min(point.y(), geometry.bottom() - size.height()))
    return QPoint(x, y)


class TranslateButtonPopup(QWidget):
    translate_requested = Signal(str, int, int)

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setObjectName("translateButtonPopup")
        self._text = ""

        self.button = QPushButton("\u2728")
        self.button.setObjectName("translateButton")
        self.button.setFlat(True)
        self.button.setAutoFillBackground(False)
        self.button.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.button.setFixedSize(scaled(FLOAT_BUTTON_WIDTH), scaled(FLOAT_BUTTON_HEIGHT))
        self.button.clicked.connect(self._emit_translate)
        self._apply_translate_icon()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button)
        self.setStyleSheet(float_button_style())

    def show_for_text(self, text: str, x: int, y: int) -> None:
        self._text = text
        self.button.setEnabled(True)
        self._apply_translate_icon()
        target = _clamp_to_screen(self, QPoint(x + scaled(FLOAT_OFFSET_X), y + scaled(FLOAT_OFFSET_Y)))
        self.move(target)
        self.show()
        self.raise_()

    def show_loading(self) -> None:
        self.button.setEnabled(False)
        self.button.setIcon(QIcon())
        self.button.setText("...")

    def _apply_translate_icon(self) -> None:
        if FLOAT_ICON_PATH.exists():
            self.button.setText("")
            self.button.setIcon(QIcon(str(FLOAT_ICON_PATH)))
            self.button.setIconSize(QSize(scaled(FLOAT_ICON_SIZE), scaled(FLOAT_ICON_SIZE)))
            return

        self.button.setIcon(QIcon())
        self.button.setText("\u2728")

    def _emit_translate(self) -> None:
        self.translate_requested.emit(self._text, self.x(), self.y())


class ResultPopup(QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setObjectName("resultPopup")

        frame = QFrame()
        frame.setObjectName("resultFrame")

        self.label = QLabel()
        self.label.setObjectName("resultLabel")
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label.setMinimumSize(scaled(120), scaled(32))
        self.label.setMaximumWidth(scaled(460))

        self.copy_button = QPushButton("复制")
        self.copy_button.clicked.connect(self._copy_result)
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.hide)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.copy_button)
        actions.addWidget(self.close_button)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(scaled(14), scaled(12), scaled(14), scaled(12))
        frame_layout.setSpacing(scaled(10))
        frame_layout.addWidget(self.label)
        frame_layout.addLayout(actions)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        self.setStyleSheet(
            f"""
            #resultFrame {{
                background: #ffffff;
                color: #202124;
                border: {scaled(1)}px solid #d5d7da;
                border-radius: {scaled(8)}px;
            }}
            #resultLabel {{
                color: #202124;
                background: transparent;
                font-size: {scaled(13)}px;
                line-height: 1.45;
            }}
            QPushButton {{
                background: #f4f6f8;
                color: #202124;
                border: {scaled(1)}px solid #d5d7da;
                border-radius: {scaled(6)}px;
                padding: {scaled(5)}px {scaled(10)}px;
            }}
            QPushButton:hover {{
                background: #e9edf2;
            }}
            """
        )

    def show_result(self, text: str, x: int, y: int) -> None:
        visible_text = self._visible_text(text)
        self.label.setText(visible_text or "翻译结果为空。请查看日志确认模型原始返回。")
        self.label.adjustSize()
        self.adjustSize()
        target = _clamp_to_screen(self, QPoint(x, y + scaled(RESULT_OFFSET_Y)))
        self.move(target)
        self.show()
        self.raise_()

    def _copy_result(self) -> None:
        QApplication.clipboard().setText(self.label.text())

    def _visible_text(self, text: str) -> str:
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return text.strip()
