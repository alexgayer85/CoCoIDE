# 01 — Getting started

**Docs last updated:** 2026-07-12

## What CoCoIDE is

CoCoIDE is a desktop IDE for **Tandy Color Computer** development:

- Edit **modern BASIC** (optional) or classic sources  
- Build a **Disk Extended BASIC** (DECB) disk image  
- Run it in **XRoar**  
- Warn about common CoCo footguns  

It is **disk-first**, defaults to **CoCo 3** + **Disk Extended BASIC**, and targets Linux (KDE/GNOME); Windows is planned later.

## What you need

| Component | Role | Notes |
|-----------|------|--------|
| Python 3.10+ | Runs CoCoIDE | |
| PySide6 | GUI | Installed via `requirements.txt` / venv |
| [XRoar](https://www.6809.org.uk/xroar/) | Emulator | On `PATH` as `xroar` |
| [Toolshed](https://sourceforge.net/projects/toolshed/) `decb` | Disk images | On `PATH` as `decb` |
| CoCo ROMs | XRoar needs them | You supply legal dumps; CoCoIDE does not ship ROMs |
| Optional: `lwasm` | Assembler | Detected but not fully wired yet |

Check the status bar after launch: it shows `xroar=OK · decb=OK · lwasm=…`.

### Override tool paths

If a tool is not on `PATH`:

```bash
export COCOIDE_XROAR=/path/to/xroar
export COCOIDE_DECB=/path/to/decb
export COCOIDE_LWASM=/path/to/lwasm
```

## Install and launch

From a source checkout:

```bash
cd CoCoIDE
./run.sh
```

First run creates `.venv` and installs PySide6 if needed.

Manual setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python -m cocoide.app
```

Open a project folder as an argument:

```bash
./run.sh examples/hello
```

## Five-minute first run

1. **Launch** `./run.sh`.  
2. **File → Open Project…** and choose `examples/hello/project.cocoide`  
   (or run `./run.sh examples/hello`).  
3. Read `src/main.mbas` in the center editor.  
4. Click **Build Disk** (or Ctrl+B).  
5. Check the **Disk** panel: you should see `MAIN.BAS` and `CLOCK.BAS`, plus the free-granule bar.  
6. Open the **Problems** tab for infos/warnings.  
7. Click **▶ Run in XRoar** (or Ctrl+R).  
   - With **Auto-run** checked (default), XRoar should type `RUN"MAIN"`.  
   - Disk write-back is off so the emulator does not dirty your project image.  

If XRoar fails to boot BASIC, configure ROMs for XRoar first (see [Troubleshooting](10-troubleshooting.md)).

## Mental model

```text
  You edit          CoCoIDE builds           CoCo / XRoar runs
 ───────────       ────────────────         ─────────────────
  src/*.mbas   →   build/*.bas (read-only)
               →   build/work.dsk      →   XRoar + RUN"…"
```

- **Source of truth:** files under `src/` and `project.cocoide`.  
- **Do not hand-edit** `build/*.bas` in the IDE (read-only artifacts).  
- Prefer **Build / Run** over `SAVE` from inside the emulator.

## Import an existing `.dsk`

**File → New Project from Disk…** or **Browse Disk Image…** — open a DECB image, import programs (detokenized), or generate a full project.  
See [11 — Browse & import disks](11-import-disks.md).

## Next

- [02 — Projects](02-projects.md)  
- [04 — Modern BASIC](04-modern-basic.md)  
- [11 — Browse & import disks](11-import-disks.md)  
