# Changelog

## 0.1.0 — 2026-07-26

First public release.

### Highlights

- Disk-first Tandy Color Computer IDE (DECB `.dsk`) with three-pane UI
- Modern BASIC (`.mbas`) preprocessor → CoCo artifacts
- Build Disk / Run in XRoar (write-back off, optional auto-run)
- Diagnostics (Problems panel)
- Disk panel: New / Add / Extract / Delete + free granules
- Browse / import existing `.dsk` images; New Project from Disk
- 6809 assembly via `lwasm` → DECB `.BIN`; best-effort disassembly of imported BINs
- Machine/RAM targeter with sane CoCo 1/2/3 sizes and XRoar `-ram-org` for 16K/32K
- Examples: `hello`, Sea Battle (BASIC + ML), Sudoku import sample

### Packaging

- Prefer bundled `tools/` binaries (portable layout) over system `PATH`
- Platform-aware XRoar audio default (Pulse on Linux; native/default on Windows)
- Linux portable zip script (`scripts/package_linux.sh`) with XRoar, `decb`, `lwasm`
- Windows portable packaging script (`scripts/package_windows.ps1`) — binaries staged separately
- Third-party attribution (`packaging/THIRD_PARTY.md`); **no CoCo ROMs** shipped

### Notes

- You must supply legal CoCo ROM dumps for XRoar
- XRoar is GPL-3+; source links in `THIRD_PARTY.md`
