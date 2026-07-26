CoCoIDE — portable package
==========================

Quick start
-----------
1. Unzip this folder anywhere (path without exotic permissions is fine).
2. Run CoCoIDE:
   - Linux:   ./CoCoIDE
   - Windows: double-click CoCoIDE.vbs (or CoCoIDE.bat for a console)
3. Open examples/hello (File → Open Project) or create a new project.
4. Build Disk, then Run in XRoar.

Bundled tools
-------------
This package includes third-party binaries under tools/:

  xroar   — emulator (GNU GPL v3+)
  decb    — Toolshed DECB disk utility (public domain)
  lwasm   — LWTOOLS assembler

CoCoIDE looks for tools/ next to the app before searching PATH.
Help → About shows which paths were resolved.

User guide
----------
Help → User Guide (or F1) opens docs/user-guide/README.md from this folder.
You can also browse docs/user-guide/ in any markdown viewer.

CoCo ROMs (required for the emulator — not in this zip)
-------------------------------------------------------
This package does NOT include Color Computer ROM images (copyright).

XRoar still loads ROMs from *your user account*, not from the zip:

  Linux/macOS: ~/.xroar/roms/
  Windows:     %USERPROFILE%\.xroar\roms\

If you already use XRoar on this machine, portable CoCoIDE will usually
boot "out of the box" because those home-directory ROMs are found
automatically. On a clean PC with an empty roms folder you get a black
screen until you install legal dumps.

Typical files:
  CoCo 1/2: bas13.rom, extbas10.rom (or 1.1), disk11.rom
  CoCo 3:   coco3.rom, disk11.rom

See the XRoar manual: https://www.6809.org.uk/xroar/doc/

Licenses
--------
  licenses/LICENSE-CoCoIDE.txt  — CoCoIDE (MIT)
  licenses/gpl-3.0.txt          — GNU GPL v3 (XRoar)
  licenses/NOTICE-*.txt         — Toolshed / LWTOOLS notices
  THIRD_PARTY.md                — full attribution + GPL source offer

XRoar source: https://www.6809.org.uk/xroar/

Support
-------
https://github.com/alexgayer85/CoCoIDE
