$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$buildRoot = Join-Path $projectRoot "build_work"
$pyiWork = Join-Path $buildRoot "pyinstaller_work"
$pyiDist = Join-Path $buildRoot "pyinstaller_dist"
$runtimeDir = Join-Path $projectRoot "translator_runtime"
$launcherSrc = Join-Path $projectRoot "launcher\translator_bootstrap.cs"
$launcherExe = Join-Path $projectRoot "Translator.exe"
$appIcon = Join-Path $projectRoot "assets\app-icon.ico"
$entryScript = Join-Path $projectRoot "run.py"
$runtimeSource = Join-Path $pyiDist "translator_app"
$runtimeExe = Join-Path $runtimeDir "translator_app.exe"
$runtimeInternalDir = Join-Path $runtimeDir "_internal"

function Assert-UnderProject {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  $full = [System.IO.Path]::GetFullPath($Path)
  $root = [System.IO.Path]::GetFullPath($projectRoot)
  if (-not $full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to modify path outside project: $full"
  }
}

function Get-CscPath {
  $candidates = @(
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  throw "csc.exe not found."
}

function Remove-ProjectPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  Assert-UnderProject -Path $Path
  if (Test-Path $Path) {
    Remove-Item -LiteralPath $Path -Recurse -Force
  }
}

function Build-Runtime {
  $python = (Get-Command python -ErrorAction Stop).Source

  Remove-ProjectPath -Path $pyiWork
  Remove-ProjectPath -Path $pyiDist

  & $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --noconsole `
    --name translator_app `
    --icon "$appIcon" `
    --workpath "$pyiWork" `
    --distpath "$pyiDist" `
    --hidden-import llama_cpp `
    --hidden-import llama_cpp.llama `
    --hidden-import llama_cpp.llama_cpp `
    --hidden-import llama_cpp.llama_types `
    --hidden-import llama_cpp.llama_chat_format `
    --exclude-module pytest `
    --exclude-module unittest `
    --exclude-module test_local_model `
    --exclude-module test_response_parsing `
    --exclude-module llama_cpp.server `
    --exclude-module torch `
    --exclude-module torchvision `
    --exclude-module transformers `
    --exclude-module tensorflow `
    --exclude-module tensorboard `
    --exclude-module pandas `
    --exclude-module scipy `
    --exclude-module sklearn `
    --exclude-module cv2 `
    --exclude-module fastapi `
    --exclude-module uvicorn `
    --exclude-module starlette `
    --exclude-module gradio `
    --exclude-module matplotlib `
    "$entryScript"

  if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE."
  }

  if (-not (Test-Path (Join-Path $runtimeSource "translator_app.exe"))) {
    throw "Runtime executable not generated."
  }
}

function Stage-Runtime {
  Remove-ProjectPath -Path $runtimeDir
  New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
  Copy-Item -Path (Join-Path $runtimeSource "*") -Destination $runtimeDir -Recurse -Force

  if (-not (Test-Path $runtimeExe)) {
    throw "Runtime stage missing executable: $runtimeExe"
  }

  Copy-CondaRuntimeDlls
  Copy-LlamaCppPackage
}

function Copy-CondaRuntimeDlls {
  $pythonPrefix = & python -c "import sys; print(sys.prefix)"
  if ($LASTEXITCODE -ne 0 -or -not $pythonPrefix) {
    throw "Unable to resolve Python prefix."
  }

  $libraryBin = Join-Path $pythonPrefix "Library\bin"
  if (-not (Test-Path $libraryBin)) {
    return
  }

  if (-not (Test-Path $runtimeInternalDir)) {
    New-Item -ItemType Directory -Path $runtimeInternalDir -Force | Out-Null
  }

  $dllNames = @(
    "libexpat.dll",
    "expat.dll",
    "liblzma.dll",
    "libbz2.dll",
    "bzip2.dll",
    "ffi.dll",
    "ffi-8.dll",
    "zstd.dll",
    "libzstd.dll",
    "sqlite3.dll",
    "zlib.dll"
  )

  foreach ($dllName in $dllNames) {
    $source = Join-Path $libraryBin $dllName
    if (Test-Path $source) {
      Copy-Item -LiteralPath $source -Destination (Join-Path $runtimeInternalDir $dllName) -Force
    }
  }
}

function Copy-LlamaCppPackage {
  $llamaPackage = & python -c "import pathlib, llama_cpp; print(pathlib.Path(llama_cpp.__file__).resolve().parent)"
  if ($LASTEXITCODE -ne 0 -or -not $llamaPackage -or -not (Test-Path $llamaPackage)) {
    throw "Unable to resolve llama_cpp package path."
  }

  if (-not (Test-Path $runtimeInternalDir)) {
    New-Item -ItemType Directory -Path $runtimeInternalDir -Force | Out-Null
  }

  $target = Join-Path $runtimeInternalDir "llama_cpp"
  if (Test-Path $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
  }
  Copy-Item -LiteralPath $llamaPackage -Destination $target -Recurse -Force
}

function Build-Launcher {
  if (-not (Test-Path $launcherSrc)) {
    throw "Launcher source missing: $launcherSrc"
  }

  $csc = Get-CscPath
  $args = @(
    "/nologo",
    "/codepage:65001",
    "/target:winexe",
    "/optimize+",
    "/out:$launcherExe",
    "/r:System.dll",
    "/r:System.Windows.Forms.dll"
  )

  if (Test-Path $appIcon) {
    $args += "/win32icon:$appIcon"
  }

  $args += $launcherSrc
  & $csc @args

  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $launcherExe)) {
    throw "Launcher compile failed."
  }
}

function Refresh-DesktopShortcutIcon {
  $desktop = [Environment]::GetFolderPath("Desktop")
  if (-not $desktop) {
    return
  }

  $shortcutPath = Join-Path $desktop "划词翻译助手.lnk"
  if (-not (Test-Path $shortcutPath)) {
    return
  }

  $shell = New-Object -ComObject WScript.Shell
  $shortcut = $shell.CreateShortcut($shortcutPath)
  $shortcut.TargetPath = $launcherExe
  $shortcut.WorkingDirectory = $projectRoot
  if (Test-Path $appIcon) {
    $shortcut.IconLocation = "$appIcon,0"
  }
  else {
    $shortcut.IconLocation = "$launcherExe,0"
  }
  $shortcut.Save()
}

Set-Location $projectRoot
Build-Runtime
Stage-Runtime
Build-Launcher
Refresh-DesktopShortcutIcon

Write-Host "Build complete:"
Write-Host "  Launcher: $launcherExe"
Write-Host "  Runtime:  $runtimeExe"
Write-Host "  Model:    $(Join-Path $projectRoot 'Interpreter-Qwen3-1.7B.Q4_K_M.gguf')"
