# CoCoIDE

Open-source **Tandy Color Computer** IDE for Linux (KDE/GNOME) with a path to Windows later.

## User documentation

**→ [User Guide](docs/user-guide/README.md)** — how to install, write modern BASIC, build disks, run XRoar, use the disk panel, and read diagnostics.

| Quick links | |
|-------------|--|
| [Getting started](docs/user-guide/01-getting-started.md) | First run |
| [Modern BASIC](docs/user-guide/04-modern-basic.md) | `.mbas`, includes, standalone |
| [Build and Run](docs/user-guide/05-build-and-run.md) | Disk + XRoar |
| [Troubleshooting](docs/user-guide/10-troubleshooting.md) | Common issues |
| [Documentation map](docs/DOCUMENTATION.md) | All docs + how we keep them updated |

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

## Requirements

- Python 3.10+
- PySide6
- `xroar`, `decb` on `PATH` (and CoCo ROMs for XRoar)
- Optional: `lwasm`

## Quick start

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

Full setup notes: [Getting started](docs/user-guide/01-getting-started.md).

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

MIT (see [LICENSE](LICENSE)).
