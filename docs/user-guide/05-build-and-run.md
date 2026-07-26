# 05 — Build and Run

**Docs last updated:** 2026-07-12

## Build Disk

**Build → Build Disk** or **Ctrl+B** or toolbar **Build Disk**.

Pipeline:

1. Save dirty editor (if needed).  
2. Preprocess **entry** + `@include` graph → `build/<entry>.bas` (read-only).  
3. Preprocess each **@standalone** → `build/<name>.bas`.  
4. Assemble `src/**/*.asm` (skip `src/imported/`) → `build/*.bin`.  
5. Ensure `build/work.dsk` exists (`decb dskini` if missing).  
6. **Free-space pass:** `decb kill` every name this build will rewrite  
   (entry `.BAS`, standalones, ASM `.BIN`s) **before any copy**.  
   Toolshed `copy -r` still needs free granules *before* releasing the old  
   file (error **248** on full disks). Batch kill also stops one growing file  
   from eating room needed for the next BIN.  
7. Copy entry, standalones, and BINs onto the image.  
8. Run **diagnostics** → Problems panel.  
9. Refresh Disk panel.

**Full-disk tip:** kill only frees a file if the **DECB name matches**  
(`src/game.asm` → `GAME.BIN`). If the image has `ML.BIN` but you build  
`GAME.BIN`, rename the `.asm` to match or free space manually.

### Build log

**Build** tab shows:

- Preprocess messages  
- Artifact paths  
- `decb` copy results  
- Variable map (`score → SC`, …)  
- Free granules line  

### After a good build

- Disk list shows your `.BAS` files  
- **CoCo** toggle shows generated DECB text  
- Problems may still list **info** items (normal)

## Run in XRoar

**Build → Run in XRoar** or **Ctrl+R** or toolbar **▶ Run in XRoar**.

1. Performs a full **Build Disk**.  
2. Launches XRoar with roughly:

   - Machine from project target (`coco3`, `coco2bus`, …)  
   - `-ram <memory_kb>`  
   - `-load-fd0 build/work.dsk`  
   - **`-no-disk-write-back`** (emulator must not alter the project image)  
   - If **Auto-run** is on: `-type RUN"MAIN"\r` (name from entry stem)  

Exact command is appended to the **XRoar** tab.

Audio defaults: **Linux** `-ao pulse -ao-gain 0` (PipeWire/Pulse, full gain); **Windows/macOS** platform default module (gain still `0` unless overridden).  
See [Troubleshooting — No sound](10-troubleshooting.md#no-sound-in-xroar) if silent.

### Auto-run

| Auto-run | Behavior |
|----------|----------|
| **On** (default) | After BASIC is ready, types `RUN"ENTRY"` |
| **Off** | Disk mounted; you type at the `OK` prompt |

Toggle on the toolbar (saved into `project.cocoide`).

### Entry name

Entry `src/main.mbas` → disk / RUN name **`MAIN`**.  
Standalone utilities are **not** auto-run.

## Run Diagnostics only

**Build → Run Diagnostics** or **Ctrl+Shift+D**.

Runs a build and focuses the **Problems** tab.  
See [07 — Diagnostics](07-diagnostics.md).

## What not to do

- Do not rely on `SAVE` inside XRoar as your project save path.  
- Do not edit `build/*.bas` by hand (regenerated every build).  
- Do not expect write-back: disk changes in the emulator are discarded by design.

## Next

- [06 — Disk panel](06-disk-panel.md)  
- [10 — Troubleshooting](10-troubleshooting.md)  
