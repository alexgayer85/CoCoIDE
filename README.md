# CoCoIDE

Open-source **Tandy Color Computer** IDE — disk-first DECB workflow, modern BASIC, XRoar, Toolshed, and LWTOOLS.

## Downloads

**→ [GitHub Releases](https://github.com/alexgayer85/CoCoIDE/releases)** for portable builds.

| Package | Contents |
|---------|----------|
| **Linux x86_64 portable** | App + `tools/{xroar,decb,lwasm}` + examples + user guide |
| **Windows x86_64 portable** | Embeddable Python + PySide6 + `tools\*.exe` + examples + user guide |
| **Source** | This repository (`pip` / `./run.sh`) |

**CoCo ROM images are not included** (copyright). Configure legal dumps for XRoar before Run (see [Troubleshooting](docs/user-guide/10-troubleshooting.md)).

Portable packages redistribute XRoar under **GPL-3+** and other FOSS tools; see `packaging/THIRD_PARTY.md`.

## User documentation

**→ [User Guide](docs/user-guide/README.md)** — install, modern BASIC, build disks, run XRoar, disk panel, diagnostics.

| Quick links | |
|-------------|--|
| [Getting started](docs/user-guide/01-getting-started.md) | First run |
| [Modern BASIC](docs/user-guide/04-modern-basic.md) | `.mbas`, includes, standalone |
| [Build and Run](docs/user-guide/05-build-and-run.md) | Disk + XRoar |
| [Troubleshooting](docs/user-guide/10-troubleshooting.md) | Common issues |
| [Documentation map](docs/DOCUMENTATION.md) | All docs |

## Product focus

| Focus | Choice |
|-------|--------|
| Media | Disk-first (DECB `.dsk`) |
| BASIC | Disk Extended Color BASIC |
| Machine | CoCo 3 priority (1/2 supported) |
| Layout | Comfortable three-pane |
| Emulator | [XRoar](https://www.6809.org.uk/xroar/) |
| Disk tools | [Toolshed](https://sourceforge.net/projects/toolshed/) `decb` |
| Assembler | [LWTOOLS](https://www.lwtools.ca/) `lwasm` |

## Features (current)

- Three-pane UI: **project tree · editor · disk image**
- Modern BASIC (`.mbas`) preprocessor → read-only CoCo artifacts
- Multi-file: `@include` (merge) + `@standalone` (separate DECB files)
- **Build Disk** / **Run in XRoar** (write-back off, optional auto-run)
- Diagnostics (Problems panel)
- Disk panel: New / Add / Extract / Delete + free-granule bar
- **Browse any `.dsk`**: import (detokenize BASIC), use as project disk, **New Project from Disk**
- **6809 ASM** via `lwasm` → DECB `.BIN` on disk; **best-effort disassembly** of imported BINs
- Portable layout: prefers `tools/` next to the app, then `PATH` / `COCOIDE_*` env overrides

## Requirements

### Portable zip

- Linux (glibc ≈ Ubuntu 22.04+) or Windows 10+
- CoCo ROMs for XRoar (you supply)
- Bundled tools — no separate install of xroar/decb/lwasm

### From source

- Python 3.10+
- PySide6
- `xroar`, `decb` on `PATH` (or under `./tools/`)
- Optional: `lwasm`
- CoCo ROMs for XRoar

## Quick start (source)

```bash
cd CoCoIDE
./run.sh examples/hello
```

Or:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python -m cocoide.app
```

Full setup: [Getting started](docs/user-guide/01-getting-started.md).

### Override tool paths

```bash
export COCOIDE_XROAR=/path/to/xroar
export COCOIDE_DECB=/path/to/decb
export COCOIDE_LWASM=/path/to/lwasm
```

## Building portable packages

```bash
# Linux portable (uses tools on PATH → vendor/linux/tools)
./scripts/fetch_tools_linux.sh
./scripts/package_linux.sh
# → dist/CoCoIDE-*-linux-x86_64.zip

# Windows portable (embeddable CPython — build from Linux without a Windows host)
./scripts/fetch_tools_windows.sh      # needs mingw-w64 for decb.exe
./scripts/package_windows_from_linux.sh
# → dist/CoCoIDE-*-windows-x86_64.zip (CoCoIDE.vbs / .bat)

# Windows portable — full PyInstaller freeze (run on Windows or GitHub Actions)
#   scripts/fetch_tools_windows.ps1
#   scripts/package_windows.ps1
# → dist/CoCoIDE-*-windows-x86_64.zip with CoCoIDE.exe
# CI: Actions workflow "Windows PyInstaller" (workflow_dispatch or tag v*)
```

Details: `packaging/THIRD_PARTY.md`.

## Project layout

```text
mygame/
  project.cocoide      # machine, entry, disk, auto_run, …
  src/main.mbas        # modern BASIC (edit this)
  src/other.mbas       # @include from main
  build/main.bas       # read-only CoCo artifact
  build/work.dsk       # DECB disk image
```

## License

MIT (see [LICENSE](LICENSE)). Bundled third-party tools: [packaging/THIRD_PARTY.md](packaging/THIRD_PARTY.md).
