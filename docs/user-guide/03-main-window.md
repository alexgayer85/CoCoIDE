# 03 — Main window

**Docs last updated:** 2026-07-12

CoCoIDE uses a **comfortable three-pane** layout.

```text
┌─────────────────────────────────────────────────────────────┐
│ Toolbar: Open Save | Build Disk | ▶ Run | Auto-run | chips  │
├──────────┬──────────────────────────────┬───────────────────┤
│ Project  │ Editor                       │ Disk              │
│ tree     │ Modern | CoCo toggle         │ free granules bar │
│          │                              │ file list         │
│          ├──────────────────────────────┤ New Add Extract…  │
│          │ Problems | Build | XRoar     │                   │
├──────────┴──────────────────────────────┴───────────────────┤
│ Status: tools · cursor · messages                           │
└─────────────────────────────────────────────────────────────┘
```

## Left — Project tree

- Shows the project folder (`src/`, `build/`, `project.cocoide`, …).  
- **Double-click** a file to open it.  
- `build/*.bas` artifacts open **read-only**.

## Center — Editor

| Control | Purpose |
|---------|---------|
| **Modern** | Edit source (`.mbas` or classic text). |
| **CoCo** | View generated DECB text after Build (read-only). |
| File label | Path; may show `[read-only artifact]`. |

### Bottom tabs

| Tab | Contents |
|-----|----------|
| **Problems** | Diagnostics (errors / warnings / infos). Click a row to jump. |
| **Build** | Build log, variable map, copy messages. |
| **XRoar** | Launch command line used for the emulator. |

Tab title may show counts: `Problems (0/1/2)` = errors / warnings / infos.

## Right — Disk panel

Live view of the project `.dsk` via Toolshed `decb`.  
See [06 — Disk panel](06-disk-panel.md).

## Toolbar

| Control | Action |
|---------|--------|
| **Open** | Open project |
| **Save** | Save current editor file |
| **Build Disk** | Preprocess → artifacts → copy onto `.dsk` |
| **▶ Run in XRoar** | Build, then launch emulator |
| **Auto-run** | When checked, inject `RUN"ENTRY"` after mount (default on) |
| Target chip | e.g. `CoCo 3 · 512K · DECB` |
| Disk chip | Image filename, e.g. `work.dsk` |

## Menus

- **File** — New Project, **New Project from Disk**, Open Project, Save, **Browse Disk Image**, Quit  
- **Build** — Build Disk, Run in XRoar, Run Diagnostics  
- **Help** — User Guide (F1), About (tool detection + guide path)  

Shortcuts: [09 — Shortcuts](09-shortcuts.md).

## Status bar

- Tool detection (`xroar=OK · decb=OK · …`)  
- Cursor line/column  
- Last action (build result, disk ops, …)  

## Next

- [04 — Modern BASIC](04-modern-basic.md)  
- [05 — Build and Run](05-build-and-run.md)  
