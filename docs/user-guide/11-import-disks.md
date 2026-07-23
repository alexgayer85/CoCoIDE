# 11 — Browse & import disk images

**Docs last updated:** 2026-07-12

One of CoCoIDE’s strongest workflows: **open any DECB `.dsk`**, pull programs off it for editing, and optionally **spin up a whole project** from that image.

## Important: Import vs New project

| Goal | Use this button |
|------|-----------------|
| Open disk in CoCoIDE as a full project (`project.cocoide` + editor) | **New project from disk…** |
| Only copy files to a folder (then optionally create a project) | **Import selected / all BASIC…** |

**Import alone** writes files to disk. If no project is open, CoCoIDE now asks: **Create project & open** so the IDE loads them. Prefer **New project from disk…** when that is what you wanted.

## Open the disk browser

| Action | How |
|--------|-----|
| Menu | **File → Browse Disk Image…** |
| Shortcut | **Ctrl+Shift+O** |
| Disk panel | **Mount…** |
| New project | **File → New Project from Disk…** (same dialog, ready to open a `.dsk`) |

Requires Toolshed **`decb`** on `PATH`.

## What you can do

### 1. Open any `.dsk`

**Open .dsk…** → directory listing (name, type, granules).

### 2. Import files for tweaking

| Button | Effect |
|--------|--------|
| **Import selected…** | Selected files → choose host folder |
| **Import all BASIC…** | Every type-0 / `.BAS` file |
| **Import all files…** | Entire directory |

**Detokenize tokenized BASIC only** (default on):

- Runs `decb list -t` **only** when the file looks like tokenized DECB BASIC  
  (leading `0xFF` byte), typically real `.BAS` programs  
- **Does not** detokenize `.DAT`, `.BIN`, ASCII text, or other data — those are  
  copied as-is  
- **Keeps the original extension** (`SCORES.DAT` → `scores.dat`, not `.bas`)  

**Force raw copy for everything**: never detokenize; byte-for-byte extract  
(useful if you want tokenized BASIC left binary).

**Suggested destination when a project is open:**  
`your-project/src/imported/` (offered by default).

Then edit in CoCoIDE, and either:

- **Add…** / **Add cur** back onto the project disk, or  
- **Build Disk** if the file is the project entry / classic source setup  

### 3. Use as project disk

**Use as project disk** copies the opened image over the current project’s `build/work.dsk` (confirms overwrite).

Useful to:

- Try a downloaded game disk under your machine settings  
- Swap media without creating a new project  

Emulator write-back stays off on Run; the copy is yours to rebuild/replace.

### 4. New project from disk (killer path)

**New project from disk…** (in the browser, or **File → New Project from Disk…**):

1. Open the `.dsk`  
2. Choose a folder for the new project  
3. If several BASIC programs exist, pick the **entry** program  
4. CoCoIDE will:

   - Copy the image → `build/work.dsk`  
   - Import files → `src/imported/` (BASIC detokenized)  
   - Write `project.cocoide` with **`preprocessor: false`** (classic line numbers)  
   - Set **entry** to the chosen/first `.bas`  
   - Open the project for you  

You can tweak sources, then **Build Disk** when you want the image regenerated from host files—or keep using the original copied disk until then.

```text
my-imported-game/
  project.cocoide          # preprocessor: false
  src/imported/
    game.bas               # detokenized, editable
    sprites.bin
    README.txt
  build/work.dsk           # copy of the original image
```

## Tips

- **Multi-select** files in the list (Ctrl/Shift-click) before Import selected.  
- Imported BASIC is **classic**, not modern `.mbas`. To modernize later, restructure by hand or start a new modern project and port logic.  
- Orphan modern rules (`@include` / `@standalone`) do not apply to classic imports.  
- Legal: only use disk images you have the right to copy.

## Related

- [06 — Disk panel](06-disk-panel.md) — project disk only  
- [02 — Projects](02-projects.md) — `project.cocoide` fields  
- [05 — Build and Run](05-build-and-run.md)  
