from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from .config import AppConfig, ConfigStore, config_from_form_values
from .style import scaled


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, store: ConfigStore) -> None:
        super().__init__()
        self.setWindowTitle("翻译设置")
        self._current = config
        self._store = store
        self.saved_config: AppConfig | None = None

        self.model_path = QLineEdit(config.model_path)

        self.context_size = QSpinBox()
        self.context_size.setRange(512, 32768)
        self.context_size.setSingleStep(512)
        self.context_size.setValue(config.local_context_size)

        self.threads = QSpinBox()
        self.threads.setRange(0, 64)
        self.threads.setValue(config.local_threads)

        self.gpu_layers = QSpinBox()
        self.gpu_layers.setRange(0, 200)
        self.gpu_layers.setValue(config.local_gpu_layers)

        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(64, 4096)
        self.max_tokens.setSingleStep(64)
        self.max_tokens.setValue(config.local_max_tokens)

        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0, 2)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(config.local_temperature)

        self.copy_delay = QSpinBox()
        self.copy_delay.setRange(30, 1000)
        self.copy_delay.setValue(config.copy_delay_ms)

        self.copy_wait = QSpinBox()
        self.copy_wait.setRange(50, 1500)
        self.copy_wait.setValue(config.copy_wait_ms)

        form = QFormLayout()
        form.setHorizontalSpacing(scaled(12))
        form.setVerticalSpacing(scaled(10))
        form.addRow("模型文件", self.model_path)
        form.addRow("上下文长度", self.context_size)
        form.addRow("CPU 线程数（0=自动）", self.threads)
        form.addRow("GPU 层数", self.gpu_layers)
        form.addRow("最大输出 Token", self.max_tokens)
        form.addRow("温度", self.temperature)
        form.addRow("复制前等待（毫秒）", self.copy_delay)
        form.addRow("复制后等待（毫秒）", self.copy_wait)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        hint = QLabel(f"配置文件：{store.as_display_path()}")
        hint.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(scaled(14), scaled(14), scaled(14), scaled(14))
        layout.setSpacing(scaled(10))
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)
        self.resize(scaled(480), scaled(240))

    def _save(self) -> None:
        self.saved_config = config_from_form_values(
            {
                "model_path": self.model_path.text().strip(),
                "local_context_size": self.context_size.value(),
                "local_threads": self.threads.value(),
                "local_gpu_layers": self.gpu_layers.value(),
                "local_max_tokens": self.max_tokens.value(),
                "local_temperature": self.temperature.value(),
                "copy_delay_ms": self.copy_delay.value(),
                "copy_wait_ms": self.copy_wait.value(),
            },
            self._current,
        )
        self._store.save(self.saved_config)
        self.accept()
