from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .style import TRAY_ICON_PATH


class TrayController(QObject):
    toggle_enabled = Signal(bool)
    settings_requested = Signal()
    open_log_requested = Signal()
    open_history_requested = Signal()
    clear_log_requested = Signal()
    clear_history_requested = Signal()
    quit_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._enabled = True
        self.tray = QSystemTrayIcon(self._build_icon())
        self.tray.setToolTip("划词翻译助手")

        self.menu = QMenu()
        self.toggle_action = QAction("暂停", self.menu)
        self.settings_action = QAction("设置", self.menu)
        self.open_log_action = QAction("打开日志", self.menu)
        self.open_history_action = QAction("打开历史记录", self.menu)
        self.clear_log_action = QAction("清除日志", self.menu)
        self.clear_history_action = QAction("清除历史记录", self.menu)
        self.quit_action = QAction("退出", self.menu)

        self.toggle_action.triggered.connect(self._toggle)
        self.settings_action.triggered.connect(self.settings_requested.emit)
        self.open_log_action.triggered.connect(self.open_log_requested.emit)
        self.open_history_action.triggered.connect(self.open_history_requested.emit)
        self.clear_log_action.triggered.connect(self.clear_log_requested.emit)
        self.clear_history_action.triggered.connect(self.clear_history_requested.emit)
        self.quit_action.triggered.connect(self.quit_requested.emit)

        self.menu.addAction(self.toggle_action)
        self.menu.addAction(self.settings_action)
        self.menu.addSeparator()
        self.menu.addAction(self.open_log_action)
        self.menu.addAction(self.open_history_action)
        self.menu.addSeparator()
        self.menu.addAction(self.clear_log_action)
        self.menu.addAction(self.clear_history_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)
        self.tray.setContextMenu(self.menu)

    def show(self) -> None:
        self.tray.show()
        self.tray.showMessage("划词翻译助手", "已在后台运行。", QSystemTrayIcon.MessageIcon.Information, 1800)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.toggle_action.setText("暂停" if enabled else "开启")
        self.tray.setToolTip("划词翻译助手：运行中" if enabled else "划词翻译助手：已暂停")

    def notify_error(self, message: str) -> None:
        self.tray.showMessage("划词翻译助手", message, QSystemTrayIcon.MessageIcon.Warning, 3500)

    def notify_info(self, message: str) -> None:
        self.tray.showMessage("划词翻译助手", message, QSystemTrayIcon.MessageIcon.Information, 2200)

    def _toggle(self) -> None:
        self.set_enabled(not self._enabled)
        self.toggle_enabled.emit(self._enabled)

    def _build_icon(self) -> QIcon:
        if TRAY_ICON_PATH.exists():
            icon = QIcon(str(TRAY_ICON_PATH))
            if not icon.isNull():
                return icon

        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#202124"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#ffffff"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(32)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x84, "T")
        painter.end()
        return QIcon(pixmap)

    def quit(self) -> None:
        self.tray.hide()
        QApplication.quit()
