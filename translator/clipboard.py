from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QByteArray, QMimeData, QUrl
from PySide6.QtGui import QColor, QGuiApplication, QImage


@dataclass
class ClipboardSnapshot:
    mime_data: QMimeData


class ClipboardManager:
    """Small Qt clipboard wrapper that preserves common MIME formats."""

    def __init__(self) -> None:
        self.clipboard = QGuiApplication.clipboard()

    def snapshot(self) -> ClipboardSnapshot:
        current = self.clipboard.mimeData()
        return ClipboardSnapshot(self._clone_mime_data(current))

    def restore(self, snapshot: ClipboardSnapshot) -> None:
        self.clipboard.setMimeData(self._clone_mime_data(snapshot.mime_data))

    def clear(self) -> None:
        self.clipboard.clear()

    def text(self) -> str:
        return self.clipboard.text()

    def _clone_mime_data(self, source: QMimeData) -> QMimeData:
        clone = QMimeData()

        if source.hasText():
            clone.setText(source.text())
        if source.hasHtml():
            clone.setHtml(source.html())
        if source.hasUrls():
            clone.setUrls([QUrl(url) for url in source.urls()])
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage):
                clone.setImageData(QImage(image))
            else:
                clone.setImageData(image)
        if source.hasColor():
            color = source.colorData()
            clone.setColorData(QColor(color) if isinstance(color, QColor) else color)

        for fmt in source.formats():
            if fmt in clone.formats():
                continue
            clone.setData(fmt, QByteArray(source.data(fmt)))

        return clone

