# 02 — Projects

**Docs last updated:** 2026-07-12

## Creating a project

**File → New Project…** → choose a folder.

CoCoIDE creates:

```text
your-folder/
  project.cocoide
  src/main.mbas      # starter modern BASIC
  build/             # artifacts appear after Build
```

Defaults: **CoCo 3**, **512K**, **DECB**, preprocessor **on**, auto-run **on**.

## Opening a project

**File → Open Project…** → select `project.cocoide`  
(or the folder that contains it).

CLI:

```bash
./run.sh /path/to/project
```

## `project.cocoide`

JSON settings for the project. Important fields:

| Field | Meaning | Example |
|-------|---------|---------|
| `name` | Display name | `"hello"` |
| `target` | Machine | `"coco1"`, `"coco2"`, `"coco3"` (bootable profiles only) |
| `memory_kb` | RAM for XRoar / checks | CoCo 1/2: `16`/`32`/`64` · CoCo 3: `128`/`512` |
| `dialect` | BASIC dialect | `"decb"` |
| `entry` | Main modern source | `"src/main.mbas"` |
| `disk_image` | DECB image path | `"build/work.dsk"` |
| `auto_run` | Type `RUN"…"` in XRoar | `true` / `false` |
| `preprocessor` | Modern → CoCo expand | `true` / `false` |
| `standalone` | Extra programs (optional) | `["src/util.mbas"]` |

Example:

```json
{
  "name": "hello",
  "target": "coco3",
  "memory_kb": 512,
  "dialect": "decb",
  "entry": "src/main.mbas",
  "disk_image": "build/work.dsk",
  "auto_run": true,
  "preprocessor": true,
  "standalone": [],
  "roms": {}
}
```

The toolbar **Auto-run** checkbox writes `auto_run` when toggled.

The green **target chip** (`CoCo 3 · 512K · DECB`) is a **button**: click it (or **File → Project Settings…**, **Ctrl+,**) to change `target` and `memory_kb` without editing JSON by hand.

### Standalone list forms

```json
"standalone": [
  "src/util_clock.mbas",
  "src/format.mbas:FORMAT.BAS"
]
```

Files can also declare `@standalone` in source (see [Modern BASIC](04-modern-basic.md)); you do not need both.

## Recommended layout

```text
mygame/
  project.cocoide
  src/
    main.mbas          # entry (linked program)
    enemies.mbas       # @include from main
    util_clock.mbas    # @standalone → own DECB file
  build/               # generated — safe to delete and rebuild
    main.bas
    util_clock.bas
    work.dsk
```

Keep `src/` in version control. Treat `build/` as disposable (often gitignored).

## Targets and diagnostics

Changing `target` / `memory_kb` changes:

- XRoar machine (`coco3`, `coco2bus`, `cocous`, …) and `-ram`  
- Diagnostics (e.g. CoCo 3-only keywords on a CoCo 2 project)

**Sane pairs only** (invalid combos are clamped on load/save/Run):

| Machine | XRoar profile | Allowed RAM |
|---------|---------------|-------------|
| CoCo 1 (NTSC) | `cocous` | 16K, 32K, 64K (+ matching `-ram-org`) |
| CoCo 2 (NTSC) | `coco2bus` | 32K, 64K (+ matching `-ram-org`) |
| CoCo 3 (NTSC) | `coco3` | 128K, 512K |

Needs ROMs under `~/.xroar/roms` (e.g. `bas13`+`extbas`+`disk11`, or `coco3`+`disk11`). Odd XRoar clones / PAL-only machines are not offered in the UI.

See [Diagnostics](07-diagnostics.md).

## Next

- [03 — Main window](03-main-window.md)  
