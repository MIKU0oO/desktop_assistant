from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication

from .clipboard import ClipboardManager
from .config import ConfigStore
from .diagnostics import clear_log_file, ensure_log_file, get_logger, setup_logging
from .history import append_history, clear_history_file, ensure_history_file
from .popup import ResultPopup, TranslateButtonPopup
from .selection import SelectionWatcher
from .settings import SettingsDialog
from .style import apply_global_style
from .translator import ModelTranslator, TranslationRequest
from .tray import TrayController


class TranslationWorker(QObject):
    finished = Signal(str, str)
    failed = Signal(str)

    def __init__(self, translator: ModelTranslator, text: str) -> None:
        super().__init__()
        self.translator = translator
        self.text = text

    @Slot()
    def run(self) -> None:
        try:
            result = self.translator.translate(TranslationRequest(self.text))
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(self.text, result)


class AppController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.store = ConfigStore()
        self.config = self.store.load()
        self.translator = ModelTranslator(self.config)
        self.clipboard = ClipboardManager()
        self.selection = SelectionWatcher(self.clipboard, self.config)
        self.tray = TrayController()
        self.button_popup = TranslateButtonPopup()
        self.result_popup = ResultPopup()
        self._thread: QThread | None = None
        self._worker: TranslationWorker | None = None
        self._last_popup_pos = (0, 0)
        self._translation_in_progress = False
        self.logger = get_logger("app")

        self.selection.selected_text.connect(self._show_selection_button)
        self.selection.pointer_pressed.connect(self._hide_popups_on_outside_click)
        self.selection.error.connect(self.tray.notify_error)
        self.button_popup.translate_requested.connect(self._translate_selected)
        self.tray.toggle_enabled.connect(self.selection.set_enabled)
        self.tray.settings_requested.connect(self._open_settings)
        self.tray.open_log_requested.connect(self._open_log)
        self.tray.open_history_requested.connect(self._open_history)
        self.tray.clear_log_requested.connect(self._clear_log)
        self.tray.clear_history_requested.connect(self._clear_history)
        self.tray.quit_requested.connect(self.quit)

    def start(self) -> None:
        self.selection.start()
        self.tray.show()

    @Slot(int, int)
    def _hide_popups_on_outside_click(self, x: int, y: int) -> None:
        QTimer.singleShot(180, lambda: self._hide_popups_on_outside_click_now(x, y))

    def _hide_popups_on_outside_click_now(self, x: int, y: int) -> None:
        if self._translation_in_progress or self._thread is not None:
            return
        point = QPoint(x, y)
        if self._contains_global_point(self.button_popup, point):
            return
        if self._contains_global_point(self.result_popup, point):
            return
        self.button_popup.hide()
        self.result_popup.hide()

    def _contains_global_point(self, widget, point: QPoint) -> bool:
        if not widget.isVisible():
            return False
        geometry = widget.frameGeometry().adjusted(-120, -120, 120, 120)
        return geometry.contains(point)

    @Slot(str, int, int)
    def _show_selection_button(self, text: str, x: int, y: int) -> None:
        if self._translation_in_progress or self._thread is not None:
            return
        self.logger.info("读取 length=%s", len(text))
        self.button_popup.show_for_text(text, x, y)

    @Slot(str, int, int)
    def _translate_selected(self, text: str, x: int, y: int) -> None:
        if self._translation_in_progress or self._thread is not None:
            self.tray.notify_error("翻译正在进行，请稍后。")
            return

        self._translation_in_progress = True
        self._last_popup_pos = (x, y)
        self.button_popup.show_loading()
        self.result_popup.hide()

        self.logger.info("加载中 length=%s", len(text))
        self._thread = QThread()
        self._worker = TranslationWorker(self.translator, text)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._show_translation)
        self._worker.failed.connect(self._show_error)
        self._worker.finished.connect(self._cleanup_worker)
        self._worker.failed.connect(self._cleanup_worker)
        self._thread.start()

    @Slot(str, str)
    def _show_translation(self, source: str, result: str) -> None:
        self.logger.info("完成 status=success result_length=%s", len(result))
        append_history(source, result)
        x, y = self._last_popup_pos
        self.button_popup.hide()
        self.result_popup.show_result(result, x, y)

    @Slot(str)
    def _show_error(self, message: str) -> None:
        self.logger.info("完成 status=failed")
        x, y = self._last_popup_pos
        self.button_popup.hide()
        self.result_popup.show_result(message, x, y)
        self.tray.notify_error(message)

    @Slot()
    def _cleanup_worker(self) -> None:
        if self._thread is None:
            return
        self._thread.quit()
        self._thread.wait()
        self._worker = None
        self._thread = None
        self._translation_in_progress = False

    @Slot()
    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self.store)
        if dialog.exec() != SettingsDialog.DialogCode.Accepted or dialog.saved_config is None:
            return
        self.config = dialog.saved_config
        self.translator.update_config(self.config)
        self.selection.update_config(self.config)

    @Slot()
    def _open_log(self) -> None:
        self._open_file(ensure_log_file())

    @Slot()
    def _open_history(self) -> None:
        self._open_file(ensure_history_file())

    @Slot()
    def _clear_log(self) -> None:
        try:
            clear_log_file()
        except OSError as exc:
            self.tray.notify_error(f"清除日志失败：{exc}")
            return
        self.tray.notify_info("日志已清除。")

    @Slot()
    def _clear_history(self) -> None:
        try:
            clear_history_file()
        except OSError as exc:
            self.tray.notify_error(f"清除历史记录失败：{exc}")
            return
        self.tray.notify_info("历史记录已清除。")

    def _open_file(self, path: Path) -> None:
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        if not opened:
            self.tray.notify_error(f"无法打开文件：{path}")

    @Slot()
    def quit(self) -> None:
        self.selection.stop()
        self.tray.quit()


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    apply_global_style(app)
    app.setQuitOnLastWindowClosed(False)
    controller = AppController()
    controller.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
