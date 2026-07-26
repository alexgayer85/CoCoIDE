# Build a Windows x86_64 portable zip (run on Windows with Python 3.10+).
# Prerequisites:
#   - vendor\windows\tools\{xroar,decb,lwasm}.exe  (see scripts/fetch_tools_windows.sh)
#   - pip install -r requirements.txt pyinstaller

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

foreach ($t in @("xroar.exe", "decb.exe", "lwasm.exe")) {
    $p = Join-Path $ToolsSrc $t
    if (-not (Test-Path $p)) {
        throw "Missing $p — stage Windows tools first (see packaging/THIRD_PARTY.md)"
    }
}

python -m pip install -q -r requirements.txt pyinstaller

$DistCoCo = Join-Path $Root "dist\CoCoIDE"
if (Test-Path $DistCoCo) { Remove-Item -Recurse -Force $DistCoCo }
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }

# Avoid --collect-all PySide6 (WebEngine/3D bloat). Widgets + Gui suffice.
python -m PyInstaller --noconfirm --clean `
  --name CoCoIDE `
  --onedir `
  --windowed `
  --distpath (Join-Path $Root "dist") `
  --workpath (Join-Path $Root "build\pyinstaller") `
  --specpath (Join-Path $Root "build\pyinstaller") `
  --paths $Root `
  --hidden-import cocoide `
  --hidden-import PySide6.QtCore `
  --hidden-import PySide6.QtGui `
  --hidden-import PySide6.QtWidgets `
  --hidden-import PySide6.QtNetwork `
  --exclude-module PySide6.QtWebEngine `
  --exclude-module PySide6.QtWebEngineCore `
  --exclude-module PySide6.QtWebEngineWidgets `
  --add-data "cocoide\style.qss;cocoide" `
  --add-data "cocoide\assets;cocoide\assets" `
  "cocoide\app.py"

New-Item -ItemType Directory -Force -Path (Join-Path $Stage "tools") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Stage "licenses") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Stage "examples") | Out-Null

Copy-Item -Recurse -Force (Join-Path $DistCoCo "*") $Stage
Copy-Item -Force (Join-Path $ToolsSrc "*.exe") (Join-Path $Stage "tools")
if (Test-Path (Join-Path $ToolsSrc "VERSIONS.txt")) {
    Copy-Item -Force (Join-Path $ToolsSrc "VERSIONS.txt") (Join-Path $Stage "tools")
}

Copy-Item -Force "LICENSE" (Join-Path $Stage "licenses\LICENSE-CoCoIDE.txt")
Copy-Item -Force "packaging\licenses\*" (Join-Path $Stage "licenses")
Copy-Item -Force "packaging\THIRD_PARTY.md" $Stage
Copy-Item -Force "packaging\README-PORTABLE.txt" $Stage

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
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Get-ChildItem $src -Recurse | Where-Object {
            $_.FullName -notmatch '\\build\\' -and $_.FullName -notmatch '__pycache__'
        } | ForEach-Object {
            $rel = $_.FullName.Substring($src.Length).TrimStart('\')
            $target = Join-Path $dest $rel
            if ($_.PSIsContainer) {
                New-Item -ItemType Directory -Force -Path $target | Out-Null
            } else {
                $parent = Split-Path $target -Parent
                if (-not (Test-Path $parent)) {
                    New-Item -ItemType Directory -Force -Path $parent | Out-Null
                }
                Copy-Item $_.FullName $target -Force
            }
        }
    }
}

$zipPath = Join-Path $Root "dist\$Name.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path $Stage -DestinationPath $zipPath
Write-Host "Built $zipPath"
