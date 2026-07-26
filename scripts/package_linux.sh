#!/usr/bin/env bash
# Build a Linux x86_64 portable zip: PyInstaller onedir + tools/ + licenses.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VER="$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"
NAME="CoCoIDE-${VER}-linux-x86_64"
STAGE="${ROOT}/dist/${NAME}"
TOOLS_SRC="${ROOT}/vendor/linux/tools"

if [[ ! -x "${TOOLS_SRC}/xroar" || ! -x "${TOOLS_SRC}/decb" || ! -x "${TOOLS_SRC}/lwasm" ]]; then
  echo "Tools missing; running scripts/fetch_tools_linux.sh …"
  "${ROOT}/scripts/fetch_tools_linux.sh"
fi

python3 -m pip install -q -r requirements.txt pyinstaller

# Clean previous freeze of this name
rm -rf "${ROOT}/dist/CoCoIDE" "${ROOT}/build/pyinstaller" "$STAGE"
mkdir -p "${ROOT}/build/pyinstaller" "$STAGE/tools" "$STAGE/licenses" "$STAGE/examples"

# Do not --collect-all PySide6 (pulls WebEngine/3D/etc. → huge zip).
# Hooks for QtCore/QtGui/QtWidgets/QtNetwork cover the IDE.
pyinstaller --noconfirm --clean \
  --name CoCoIDE \
  --onedir \
  --windowed \
  --distpath "${ROOT}/dist" \
  --workpath "${ROOT}/build/pyinstaller" \
  --specpath "${ROOT}/build/pyinstaller" \
  --paths "$ROOT" \
  --hidden-import cocoide \
  --hidden-import PySide6.QtCore \
  --hidden-import PySide6.QtGui \
  --hidden-import PySide6.QtWidgets \
  --hidden-import PySide6.QtNetwork \
  --exclude-module PySide6.QtWebEngine \
  --exclude-module PySide6.QtWebEngineCore \
  --exclude-module PySide6.QtWebEngineWidgets \
  --exclude-module PySide6.Qt3DCore \
  --exclude-module PySide6.QtBluetooth \
  --exclude-module PySide6.QtMultimedia \
  --add-data "${ROOT}/cocoide/style.qss:cocoide" \
  --add-data "${ROOT}/cocoide/assets:cocoide/assets" \
  "${ROOT}/cocoide/app.py"

# Assemble stage from onedir output
cp -a "${ROOT}/dist/CoCoIDE/." "$STAGE/"
cp -f "${TOOLS_SRC}/xroar" "${TOOLS_SRC}/decb" "${TOOLS_SRC}/lwasm" "$STAGE/tools/"
chmod +x "$STAGE/tools/xroar" "$STAGE/tools/decb" "$STAGE/tools/lwasm"
[[ -f "${TOOLS_SRC}/VERSIONS.txt" ]] && cp -f "${TOOLS_SRC}/VERSIONS.txt" "$STAGE/tools/"

cp -f "${ROOT}/LICENSE" "$STAGE/licenses/LICENSE-CoCoIDE.txt"
cp -f "${ROOT}/packaging/licenses/gpl-3.0.txt" "$STAGE/licenses/"
cp -f "${ROOT}/packaging/licenses/NOTICE-Toolshed.txt" "$STAGE/licenses/"
cp -f "${ROOT}/packaging/licenses/NOTICE-LWTOOLS.txt" "$STAGE/licenses/"
cp -f "${ROOT}/packaging/THIRD_PARTY.md" "$STAGE/"
cp -f "${ROOT}/packaging/README-PORTABLE.txt" "$STAGE/"

# User guide (Help → User Guide / F1)
if [[ -d "${ROOT}/docs/user-guide" ]]; then
  mkdir -p "${STAGE}/docs"
  rsync -a --exclude '__pycache__' \
    "${ROOT}/docs/user-guide/" "${STAGE}/docs/user-guide/"
fi

# Example projects (sources only)
# Ship user-facing demos (skip diag_fixture — internal test project)
for ex in hello seabattle seabattle-ml sudoku; do
  if [[ -d "${ROOT}/examples/${ex}" ]]; then
    mkdir -p "${STAGE}/examples/${ex}"
    rsync -a --exclude build --exclude '__pycache__' \
      "${ROOT}/examples/${ex}/" "${STAGE}/examples/${ex}/"
  fi
done

# ROM safety scan (names only; allow docs text)
if find "$STAGE" -type f \( -iname '*.rom' -o -iname 'coco3.rom' -o -iname 'bas13.rom' \) | grep -q .; then
  echo "error: ROM-like files found in stage — aborting" >&2
  find "$STAGE" -type f \( -iname '*.rom' -o -iname 'coco3.rom' -o -iname 'bas13.rom' \) >&2
  exit 1
fi

(
  cd "${ROOT}/dist"
  rm -f "${NAME}.zip"
  zip -r -q "${NAME}.zip" "$NAME"
)

echo "Built ${ROOT}/dist/${NAME}.zip"
ls -lh "${ROOT}/dist/${NAME}.zip"
