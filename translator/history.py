from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .config import ConfigStore


def history_path() -> Path:
    return ConfigStore.default_path().with_name("history.txt")


def ensure_history_file() -> Path:
    path = history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return path


def clear_history_file() -> None:
    ensure_history_file().write_text("", encoding="utf-8")


def append_history(source: str, result: str) -> None:
    path = ensure_history_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{timestamp}]\n"
        "原文:\n"
        f"{source.strip()}\n\n"
        "译文:\n"
        f"{result.strip()}\n\n"
        + "-" * 60
        + "\n\n"
    )
    path.open("a", encoding="utf-8").write(entry)
