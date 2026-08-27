# Custom Floating Icon

Put your custom floating translate icon here:

```text
translate_assistant/assets/translate_icon.png
```

Recommended image:

- Format: PNG with transparent background
- Canvas: 64x64 px or 128x128 px
- Visible glyph area: keep 8-12 px transparent padding around the artwork
- Style: simple filled or outlined symbol, high contrast
- Avoid: detailed photos, tiny text, very thin strokes

The app scales the image through `FLOAT_ICON_SIZE` in `translator/style.py`.

## App / Shortcut Icon

Put your Windows app icon here:

```text
translate_assistant/assets/app-icon.ico
```

Recommended ICO:

- Include sizes: 16x16, 32x32, 48x48, 256x256
- Background: transparent
- Format: `.ico`, not `.png`

After replacing it, rebuild with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build\build_translator.ps1
```

The build script embeds this icon into `Translator.exe` and refreshes the desktop shortcut icon.

## System Tray Icon

Put your tray icon here:

```text
translate_assistant/assets/tray_icon.png
```

Recommended PNG:

- Canvas: 64x64 px or 128x128 px
- Background: transparent
- Shape: simple and high contrast, because Windows tray renders it very small
