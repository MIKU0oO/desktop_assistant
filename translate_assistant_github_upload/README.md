# Translate Assistant

Windows desktop selection translation assistant powered by a local GGUF model.

The app runs in the system tray, listens for text selection, temporarily copies
the selected text, restores the original clipboard content, and shows a small
translation button near the cursor. Clicking the button runs local inference
through `llama-cpp-python` and displays the translated result.

## Features

- Windows system tray background app
- Global mouse selection listener
- Temporary `Ctrl+C` capture with clipboard restoration
- Floating translate button and result popup
- Local GGUF model inference through `llama-cpp-python`
- English to Simplified Chinese and Chinese to English auto target selection
- Configurable model path, context size, threads, GPU layers, max tokens, and temperature
- Log and translation history files under `%APPDATA%\TranslateAssistant`

## Project Layout

```text
translator/            Python source package
assets/                Tray and floating button icons
launcher/              Small C# launcher source for packaged builds
scripts/build/         Packaging script
run.py                 Python entry point
requirements.txt       Python dependencies
```

Generated files such as `translator_runtime/`, `release/`, `Translator.exe`, and
GGUF model files are intentionally ignored by Git.

## Model

This project expects a local model file named:

```text
Interpreter-Qwen3-1.7B.Q4_K_M.gguf
```

Place it in the project root, next to `run.py`, or set it in the app settings.
You can also override the path with:

```powershell
$env:TRANSLATOR_MODEL_PATH="D:\models\Interpreter-Qwen3-1.7B.Q4_K_M.gguf"
python -m translator.main
```

Model files are not included in this repository. The upstream
`Qwen/Qwen3-1.7B` model is published under Apache-2.0 on Hugging Face, but GGUF
quantized files may come from third-party publishers. Verify and follow the
license and attribution requirements of the exact model file you download.

## Development

```powershell
cd E:\demo\python\translate_assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m translator.main
```

With Conda or PyCharm, make sure `python` and `pip` point to the same
environment:

```powershell
python -c "import sys; print(sys.executable)"
python -m pip show PySide6 llama-cpp-python
```

## Packaging

Run the packaging script from the project root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build\build_translator.ps1
```

The script builds:

- `translator_runtime\translator_app.exe`
- `Translator.exe`

`Translator.exe` is a small launcher. It starts
`translator_runtime\translator_app.exe` and passes the local model path when the
default GGUF file exists beside it.

For a portable distribution, copy these together:

```text
Translator.exe
translator_runtime/
assets/
Interpreter-Qwen3-1.7B.Q4_K_M.gguf
README.md
```

## Runtime Files

Configuration:

```text
%APPDATA%\TranslateAssistant\config.json
```

Log:

```text
%APPDATA%\TranslateAssistant\app.log
```

Translation history:

```text
%APPDATA%\TranslateAssistant\history.txt
```

Logs record operational state only. Source text and translated text are written
to history, not to the log file.

## Notes

- This is a Windows desktop utility.
- OCR, image translation, browser extensions, and PDF-specific parsing are out
  of scope for the current version.
- The repository does not currently declare a software license for the app code.
  Add a `LICENSE` file before publishing it as an open-source project.
