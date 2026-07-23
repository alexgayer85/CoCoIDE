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
| `target` | Machine | `"coco1"`, `"coco2"`, `"coco3"` |
| `memory_kb` | RAM for XRoar / checks | `64`, `128`, `512` |
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

- XRoar machine (`coco3`, `coco2bus`, …) and `-ram`  
- Diagnostics (e.g. CoCo 3-only keywords on a CoCo 2 project)

See [Diagnostics](07-diagnostics.md).

## Next

- [03 — Main window](03-main-window.md)  
