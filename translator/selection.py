from __future__ import annotations

import math
import time
from typing import Optional

from PySide6.QtCore import QObject, QPoint, QTimer, Signal, Slot

try:
    import keyboard as keyboard_lib
except ImportError:  # pragma: no cover - runtime fallback
    keyboard_lib = None

from pynput import keyboard as pynput_keyboard
from pynput import mouse

from .clipboard import ClipboardManager
from .config import AppConfig


class SelectionWatcher(QObject):
    pointer_pressed = Signal(int, int)
    selection_released = Signal(int, int)
    selected_text = Signal(str, int, int)
    error = Signal(str)

    def __init__(self, clipboard: ClipboardManager, config: AppConfig) -> None:
        super().__init__()
        self.clipboard = clipboard
        self.config = config
        self.enabled = True
        self._listener: mouse.Listener | None = None
        self._press_pos: Optional[tuple[int, int]] = None
        self._last_trigger = 0.0
        self._fallback_keyboard = pynput_keyboard.Controller()
        self.selection_released.connect(self._on_selection_released)

    def update_config(self, config: AppConfig) -> None:
        self.config = config

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = mouse.Listener(on_click=self._on_click)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is None:
            return
        self._listener.stop()
        self._listener = None

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if button != mouse.Button.left:
            return

        if pressed:
            self.pointer_pressed.emit(x, y)
            self._press_pos = (x, y)
            return

        if not self.enabled or self._press_pos is None:
            return

        start_x, start_y = self._press_pos
        self._press_pos = None
        distance = math.hypot(x - start_x, y - start_y)
        if distance < self.config.min_drag_pixels:
            return

        now = time.monotonic()
        if (now - self._last_trigger) * 1000 < self.config.debounce_ms:
            return
        self._last_trigger = now

        self.selection_released.emit(x, y)

    @Slot(int, int)
    def _on_selection_released(self, x: int, y: int) -> None:
        point = QPoint(x, y)
        QTimer.singleShot(self.config.copy_delay_ms, lambda: self._capture(point))

    def _capture(self, point: QPoint) -> None:
        snapshot = self.clipboard.snapshot()
        self.clipboard.clear()

        try:
            self._send_ctrl_c()
        except Exception as exc:  # pragma: no cover - depends on OS hook state
            self.clipboard.restore(snapshot)
            self.error.emit(f"复制选中文本失败：{exc}")
            return

        QTimer.singleShot(
            self.config.copy_wait_ms,
            lambda: self._read_after_copy(snapshot, point),
        )

    def _read_after_copy(self, snapshot, point: QPoint) -> None:
        try:
            selected = self.clipboard.text().strip()
        finally:
            self.clipboard.restore(snapshot)

        if len(selected) < self.config.min_selection_chars:
            return
        if not any(char.isalnum() or "\u4e00" <= char <= "\u9fff" for char in selected):
            return
        self.selected_text.emit(selected, point.x(), point.y())

    def _send_ctrl_c(self) -> None:
        if keyboard_lib is not None:
            keyboard_lib.send("ctrl+c")
            return

        with self._fallback_keyboard.pressed(pynput_keyboard.Key.ctrl):
            self._fallback_keyboard.press("c")
            self._fallback_keyboard.release("c")
