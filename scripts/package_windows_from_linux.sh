#!/usr/bin/env bash
# Build a Windows x86_64 portable zip from Linux (no Windows host required).
#
# Layout:
#   CoCoIDE-<ver>-windows-x86_64/
#     CoCoIDE.bat / CoCoIDE.vbs   launchers
#     python/                    embeddable CPython + PySide6 + cocoide
#     tools/                     xroar.exe decb.exe lwasm.exe
#     docs/user-guide/
#     examples/
#     licenses/ THIRD_PARTY.md README-PORTABLE.txt
#
# Prerequisites: curl, unzip, zip, python3; scripts/fetch_tools_windows.sh deps
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VER="$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"
NAME="CoCoIDE-${VER}-windows-x86_64"
STAGE="${ROOT}/dist/${NAME}"
CACHE="${ROOT}/vendor/windows/cache"
TOOLS_SRC="${ROOT}/vendor/windows/tools"
PY_VER="${COCOIDE_WIN_PYTHON_VER:-3.12.10}"
PY_URL="${COCOIDE_WIN_PYTHON_URL:-https://www.python.org/ftp/python/${PY_VER}/python-${PY_VER}-embed-amd64.zip}"
# Major.minor for pythonXY.zip / ._pth (3.12.10 → 312)
PY_MM="$(echo "$PY_VER" | awk -F. '{print $1$2}')"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "error: missing command: $1" >&2
    exit 1
  }
}
need curl
need unzip
need zip
need python3

if [[ ! -x "${TOOLS_SRC}/xroar.exe" || ! -f "${TOOLS_SRC}/decb.exe" || ! -f "${TOOLS_SRC}/lwasm.exe" ]]; then
  echo "Windows tools missing; running scripts/fetch_tools_windows.sh …"
  chmod +x "${ROOT}/scripts/fetch_tools_windows.sh"
  "${ROOT}/scripts/fetch_tools_windows.sh"
fi

echo "==> Preparing stage ${STAGE}"
rm -rf "$STAGE"
mkdir -p "$STAGE/python" "$STAGE/tools" "$STAGE/licenses" "$STAGE/examples" "$STAGE/docs" "$CACHE"

echo "==> Embeddable Python ${PY_VER}"
PY_ZIP="${CACHE}/python-${PY_VER}-embed-amd64.zip"
if [[ ! -f "$PY_ZIP" ]]; then
  curl -fsSL -o "$PY_ZIP" "$PY_URL"
fi
unzip -q -o "$PY_ZIP" -d "$STAGE/python"

# Enable site-packages + isolated layout
PTH="$(echo "$STAGE/python"/python*._pth)"
# Prefer exact python312._pth
if [[ -f "${STAGE}/python/python${PY_MM}._pth" ]]; then
  PTH="${STAGE}/python/python${PY_MM}._pth"
fi
cat >"$PTH" <<EOF
python${PY_MM}.zip
.
Lib/site-packages
import site
EOF

mkdir -p "$STAGE/python/Lib/site-packages"

echo "==> Downloading Windows PySide6 (Essentials only)"
WHEEL_DIR="${CACHE}/wheels-win-amd64"
mkdir -p "$WHEEL_DIR"
python3 -m pip download -q \
  PySide6_Essentials shiboken6 \
  -d "$WHEEL_DIR" \
  --platform win_amd64 \
  --python-version "${PY_MM:0:1}.${PY_MM:1}" \
  --only-binary=:all:

echo "==> Extracting wheels into embeddable Python"
python3 - <<PY
import zipfile
from pathlib import Path
wheel_dir = Path("${WHEEL_DIR}")
dest = Path("${STAGE}/python/Lib/site-packages")
for whl in sorted(wheel_dir.glob("*.whl")):
    print("  ", whl.name)
    with zipfile.ZipFile(whl) as zf:
        zf.extractall(dest)
PY

echo "==> Installing CoCoIDE package sources"
# Pure-Python package — copy tree
mkdir -p "$STAGE/python/Lib/site-packages/cocoide"
# Copy package modules (not __pycache__)
rsync -a --exclude '__pycache__' --exclude '*.pyc' \
  "${ROOT}/cocoide/" "$STAGE/python/Lib/site-packages/cocoide/"

echo "==> Launchers"
# Console-friendly batch (shows errors)
cat >"$STAGE/CoCoIDE.bat" <<'BAT'
@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHONHOME="
set "PYTHONPATH="
cd /d "%ROOT%"
"%ROOT%python\python.exe" -m cocoide.app %*
if errorlevel 1 pause
BAT

# Windowed launcher via pythonw (no console flash when OK)
cat >"$STAGE/CoCoIDE.vbs" <<'VBS'
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root
pyw = root & "\python\pythonw.exe"
If Not fso.FileExists(pyw) Then
  pyw = root & "\python\python.exe"
End If
sh.Run """" & pyw & """ -m cocoide.app", 0, False
VBS

# Convenience: also name matching Linux-style
cp -f "$STAGE/CoCoIDE.bat" "$STAGE/run.bat"

echo "==> Tools, docs, examples, licenses"
cp -f "${TOOLS_SRC}/xroar.exe" "${TOOLS_SRC}/decb.exe" "${TOOLS_SRC}/lwasm.exe" "$STAGE/tools/"
[[ -f "${TOOLS_SRC}/VERSIONS.txt" ]] && cp -f "${TOOLS_SRC}/VERSIONS.txt" "$STAGE/tools/"
[[ -f "${TOOLS_SRC}/COPYING-XRoar.txt" ]] && cp -f "${TOOLS_SRC}/COPYING-XRoar.txt" "$STAGE/licenses/"

cp -f "${ROOT}/LICENSE" "$STAGE/licenses/LICENSE-CoCoIDE.txt"
cp -f "${ROOT}/packaging/licenses/gpl-3.0.txt" "$STAGE/licenses/"
cp -f "${ROOT}/packaging/licenses/NOTICE-Toolshed.txt" "$STAGE/licenses/"
cp -f "${ROOT}/packaging/licenses/NOTICE-LWTOOLS.txt" "$STAGE/licenses/"
cp -f "${ROOT}/packaging/THIRD_PARTY.md" "$STAGE/"
cp -f "${ROOT}/packaging/README-PORTABLE.txt" "$STAGE/"

# Windows-specific quick start
cat >"$STAGE/README-WINDOWS.txt" <<EOF
CoCoIDE ${VER} — Windows portable
================================

1. Unzip this folder anywhere (avoid needing admin rights).
2. Double-click CoCoIDE.vbs  (no console window)
   or CoCoIDE.bat            (console; shows errors)
3. Help → User Guide (F1) for documentation.
4. Open examples\\hello or create a new project.

Tools are in tools\\ (xroar.exe, decb.exe, lwasm.exe).

ROMs are NOT included. Place legal CoCo ROM dumps where XRoar looks:
  %USERPROFILE%\\.xroar\\roms\\
Typical files: coco3.rom, disk11.rom (CoCo 3); bas13.rom, extbas10.rom, disk11.rom (CoCo 1/2).

If Windows SmartScreen warns on first run, choose "More info" → "Run anyway"
for builds you obtained from the official GitHub Releases page.

See THIRD_PARTY.md and licenses\\ for attribution (XRoar is GPL-3+).
EOF

if [[ -d "${ROOT}/docs/user-guide" ]]; then
  rsync -a --exclude '__pycache__' \
    "${ROOT}/docs/user-guide/" "$STAGE/docs/user-guide/"
fi

for ex in hello seabattle-ml; do
  if [[ -d "${ROOT}/examples/${ex}" ]]; then
    mkdir -p "${STAGE}/examples/${ex}"
    rsync -a --exclude build --exclude '__pycache__' \
      "${ROOT}/examples/${ex}/" "${STAGE}/examples/${ex}/"
  fi
done

# ROM safety
if find "$STAGE" -type f \( -iname '*.rom' \) | grep -q .; then
  echo "error: ROM-like files found in stage — aborting" >&2
  find "$STAGE" -type f -iname '*.rom' >&2
  exit 1
fi

echo "==> Zipping"
(
  cd "${ROOT}/dist"
  rm -f "${NAME}.zip"
  zip -r -q "${NAME}.zip" "$NAME"
)

echo "Built ${ROOT}/dist/${NAME}.zip"
ls -lh "${ROOT}/dist/${NAME}.zip"
echo "Contents top-level:"
ls -la "$STAGE" | head -20
