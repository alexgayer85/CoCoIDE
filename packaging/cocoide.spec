# -*- mode: python ; coding: utf-8 -*-
# Optional shared PyInstaller spec. Prefer scripts/package_linux.sh /
# package_windows.ps1 which pass equivalent CLI flags.
# Usage: pyinstaller packaging/cocoide.spec

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).resolve().parent.parent
entry = str(root / "cocoide" / "app.py")

datas = [
    (str(root / "cocoide" / "style.qss"), "cocoide"),
    (str(root / "cocoide" / "assets"), "cocoide/assets"),
]

a = Analysis(
    [entry],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=["cocoide"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CoCoIDE",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CoCoIDE",
)
