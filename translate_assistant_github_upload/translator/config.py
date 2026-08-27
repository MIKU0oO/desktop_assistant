from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


APP_NAME = "TranslateAssistant"
DEFAULT_MODEL_FILE = "Interpreter-Qwen3-1.7B.Q4_K_M.gguf"


def default_model_path() -> str:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates = [
            exe_dir / DEFAULT_MODEL_FILE,
            exe_dir.parent / DEFAULT_MODEL_FILE,
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return str(candidates[0])
    return str(Path(__file__).resolve().parent.parent / DEFAULT_MODEL_FILE)


@dataclass
class AppConfig:
    model_path: str = default_model_path()
    local_context_size: int = 4096
    local_threads: int = 0
    local_gpu_layers: int = 0
    local_max_tokens: int = 1024
    local_temperature: float = 0.2
    copy_delay_ms: int = 120
    copy_wait_ms: int = 180
    debounce_ms: int = 600
    min_drag_pixels: int = 8
    min_selection_chars: int = 2


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self.default_path()

    @staticmethod
    def default_path() -> Path:
        root = os.environ.get("APPDATA")
        base = Path(root) if root else Path.home() / "AppData" / "Roaming"
        return base / APP_NAME / "config.json"

    def load(self) -> AppConfig:
        config = AppConfig()

        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}

            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        config.model_path = os.environ.get("TRANSLATOR_MODEL_PATH", config.model_path)
        return config

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def as_display_path(self) -> str:
        return str(self.path)


def config_from_form_values(values: dict[str, Any], current: AppConfig) -> AppConfig:
    config = AppConfig(**asdict(current))
    for key, value in values.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config
