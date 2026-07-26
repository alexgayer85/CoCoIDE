# Build a Windows x86_64 PyInstaller onedir portable zip.
# Run on Windows (or GitHub Actions windows-latest).
#
# Prerequisites:
#   - Python 3.10+ on PATH as `python`
#   - vendor\windows\tools\{xroar,decb,lwasm}.exe
#     (scripts\fetch_tools_windows.ps1 or scripts\fetch_tools_windows.sh)
#
# Output:
#   dist\CoCoIDE-<ver>-windows-x86_64\CoCoIDE.exe
#   dist\CoCoIDE-<ver>-windows-x86_64.zip

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$pyproject = Get-Content -Raw "pyproject.toml"
if ($pyproject -match 'version\s*=\s*"([^"]+)"') {
    $Ver = $Matches[1]
} else {
    throw "Could not parse version from pyproject.toml"
}

$Name = "CoCoIDE-$Ver-windows-x86_64"
$Stage = Join-Path $Root "dist\$Name"
$ToolsSrc = Join-Path $Root "vendor\windows\tools"
$PyDist = Join-Path $Root "dist\CoCoIDE"

foreach ($t in @("xroar.exe", "decb.exe", "lwasm.exe")) {
    $p = Join-Path $ToolsSrc $t
    if (-not (Test-Path $p)) {
        Write-Host "Tools missing; running fetch_tools_windows.ps1 …"
        & (Join-Path $Root "scripts\fetch_tools_windows.ps1")
        break
    }
}
foreach ($t in @("xroar.exe", "decb.exe", "lwasm.exe")) {
    $p = Join-Path $ToolsSrc $t
    if (-not (Test-Path $p)) {
        throw "Missing $p — stage Windows tools first"
    }
}

Write-Host "==> pip install"
python -m pip install -U pip
python -m pip install -q -r requirements.txt pyinstaller

if (Test-Path $PyDist) { Remove-Item -Recurse -Force $PyDist }
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
$work = Join-Path $Root "build\pyinstaller"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }

Write-Host "==> PyInstaller onedir (windowed)"
# Absolute --add-data paths: with --specpath under build/, relative cocoide\…
# is resolved against the work dir and fails on CI.
$StyleQss = Join-Path $Root "cocoide\style.qss"
$AssetsDir = Join-Path $Root "cocoide\assets"
$Entry = Join-Path $Root "packaging\win_entry.py"
if (-not (Test-Path $StyleQss)) { throw "missing $StyleQss" }
if (-not (Test-Path $AssetsDir)) { throw "missing $AssetsDir" }
if (-not (Test-Path $Entry)) { throw "missing $Entry" }

# Do not --collect-all PySide6 (WebEngine bloat).
python -m PyInstaller --noconfirm --clean `
  --name CoCoIDE `
  --onedir `
  --windowed `
  --distpath (Join-Path $Root "dist") `
  --workpath $work `
  --specpath $work `
  --paths $Root `
  --hidden-import cocoide `
  --hidden-import cocoide.app `
  --hidden-import cocoide.mainwindow `
  --hidden-import cocoide.tools `
  --hidden-import cocoide.build `
  --hidden-import cocoide.project `
  --hidden-import cocoide.dialogs `
  --hidden-import cocoide.diagnostics `
  --hidden-import cocoide.asm `
  --hidden-import cocoide.preprocessor `
  --hidden-import cocoide.disk_browser `
  --hidden-import cocoide.disk_import `
  --hidden-import cocoide.disasm6809 `
  --hidden-import PySide6.QtCore `
  --hidden-import PySide6.QtGui `
  --hidden-import PySide6.QtWidgets `
  --hidden-import PySide6.QtNetwork `
  --exclude-module PySide6.QtWebEngine `
  --exclude-module PySide6.QtWebEngineCore `
  --exclude-module PySide6.QtWebEngineWidgets `
  --exclude-module PySide6.Qt3DCore `
  --exclude-module PySide6.QtBluetooth `
  --exclude-module PySide6.QtMultimedia `
  --add-data "$StyleQss;cocoide" `
  --add-data "$AssetsDir;cocoide\assets" `
  $Entry

if (-not (Test-Path (Join-Path $PyDist "CoCoIDE.exe"))) {
    throw "PyInstaller did not produce dist\CoCoIDE\CoCoIDE.exe"
}

Write-Host "==> Assemble portable stage"
New-Item -ItemType Directory -Force -Path `
    (Join-Path $Stage "tools"), `
    (Join-Path $Stage "licenses"), `
    (Join-Path $Stage "examples"), `
    (Join-Path $Stage "docs") | Out-Null

Copy-Item -Recurse -Force (Join-Path $PyDist "*") $Stage
Copy-Item -Force (Join-Path $ToolsSrc "xroar.exe") (Join-Path $Stage "tools")
Copy-Item -Force (Join-Path $ToolsSrc "decb.exe") (Join-Path $Stage "tools")
Copy-Item -Force (Join-Path $ToolsSrc "lwasm.exe") (Join-Path $Stage "tools")
if (Test-Path (Join-Path $ToolsSrc "VERSIONS.txt")) {
    Copy-Item -Force (Join-Path $ToolsSrc "VERSIONS.txt") (Join-Path $Stage "tools")
}

Copy-Item -Force "LICENSE" (Join-Path $Stage "licenses\LICENSE-CoCoIDE.txt")
Copy-Item -Force (Join-Path $Root "packaging\licenses\*") (Join-Path $Stage "licenses")
Copy-Item -Force (Join-Path $Root "packaging\THIRD_PARTY.md") $Stage
Copy-Item -Force (Join-Path $Root "packaging\README-PORTABLE.txt") $Stage

@"
CoCoIDE $Ver — Windows (PyInstaller)
====================================

1. Unzip this folder anywhere.
2. Double-click CoCoIDE.exe
3. Help / F1 for the user guide.
4. Open examples\hello or create a new project.

Bundled tools are in tools\ (xroar.exe, decb.exe, lwasm.exe).

ROMs are NOT included. Place legal dumps in:
  %USERPROFILE%\.xroar\roms\
(e.g. coco3.rom, disk11.rom)

If SmartScreen warns, use More info → Run anyway only for official
GitHub Releases builds.

See THIRD_PARTY.md (XRoar is GPL-3+).
"@ | Set-Content -Path (Join-Path $Stage "README-WINDOWS.txt") -Encoding UTF8

$guideSrc = Join-Path $Root "docs\user-guide"
if (Test-Path $guideSrc) {
    $guideDest = Join-Path $Stage "docs\user-guide"
    New-Item -ItemType Directory -Force -Path $guideDest | Out-Null
    Copy-Item -Recurse -Force (Join-Path $guideSrc "*") $guideDest
}

foreach ($ex in @("hello", "seabattle-ml")) {
    $src = Join-Path $Root "examples\$ex"
    if (Test-Path $src) {
        $dest = Join-Path $Stage "examples\$ex"
        robocopy $src $dest /E /XD build __pycache__ /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy failed for $ex code $LASTEXITCODE" }
    }
}

# Refuse ROMs in the stage
$roms = Get-ChildItem -Path $Stage -Recurse -Filter *.rom -ErrorAction SilentlyContinue
if ($roms) {
    throw "ROM files found in stage — aborting: $($roms.FullName -join ', ')"
}

$zipPath = Join-Path $Root "dist\$Name.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
# Compress-Archive can struggle with very long paths; prefer tar if available
if (Get-Command tar -ErrorAction SilentlyContinue) {
    Push-Location (Join-Path $Root "dist")
    tar -a -cf "$Name.zip" $Name
    Pop-Location
} else {
    Compress-Archive -Path $Stage -DestinationPath $zipPath -CompressionLevel Optimal
}

Write-Host "Built $zipPath"
Get-Item $zipPath | Format-List FullName, Length
