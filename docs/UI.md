# CoCoIDE — UI Sketch / product decisions

**Status:** design history (not the end-user manual)  
**User guide:** [user-guide/README.md](user-guide/README.md)  
**Open sketches:** [ui-sketches/index.html](ui-sketches/index.html) (open in a browser)

## Product locks

| Decision | Choice |
|----------|--------|
| Name | **CoCoIDE** (no Color Computer product owns this name; unrelated “CocoIDE” exists for a teaching CPU toolkit) |
| Media | Disk-first (DECB `.dsk`) |
| Dialect | Disk Extended Color BASIC |
| Machine priority | CoCo 3 (128K / 512K), CoCo 1/2 supported |
| Weight | **Comfortable three-pane** default; lighter layout still available later |
| License | Open source (exact license TBD) |
| Preprocessor | Optional modern BASIC → CoCo BASIC |
| CoCo output | **Read-only build artifact** (not hand-edited in the IDE) |
| Run in XRoar | Mount disk + optional auto-keystroke launch (**default on**) |
| Multi-file modern BASIC | **Option C (hybrid)** — multi-file edit, linked entry program for Run |

## Design principles

1. **Disk is first-class** — the active `.dsk` is a side panel (or drawer), not a buried dialog.
2. **Target is always visible** — chip shows `CoCo 3 · 512K · DECB` + image name.
3. **One primary action** — **Run in XRoar** (rebuild artifacts → mount disk → optional type-in RUN).
4. **Modern source is the only edit surface** when preprocessor is on; CoCo text is a **read-only** build view.
5. **Comfortable three-pane** default (project | editor | disk); lighter layout optional later.
6. **Honest about tools** — status of `xroar` / `decb` / `lwasm` is plain and fixable in Preferences.
7. **Source of truth is the project tree**, not the emulator — XRoar is for testing, not for saving programs back.

## Screens

### 1. Main window (comfortable)

```
┌─ title: project — CoCoIDE ─────────────────────────────────────┐
│ [Open] [Save] │ [Build Disk] [▶ Run in XRoar] │ [Preprocess]…  │
│                              [CoCo 3·512K·DECB] [work.dsk]     │
├──────────┬───────────────────────────────────┬─────────────────┤
│ Project  │ main.bas          [Modern|CoCo]   │ Disk            │
│ tree     │ line gutter + editor              │ free granules   │
│          │                                   │ file list       │
│          ├───────────────────────────────────┤ Add Extract …   │
│          │ Problems | Build | XRoar          │                 │
├──────────┴───────────────────────────────────┴─────────────────┤
│ tools OK · Ln,Col · Modern BASIC · 2 problems · tokens on build│
└────────────────────────────────────────────────────────────────┘
```

**Columns**

| Pane | Role |
|------|------|
| Left · Project | `src/`, `build/`, `project.cocoide`, ASM files |
| Center · Editor | Tabs, Modern/CoCo toggle, diagnostics underlay |
| Right · Disk | Live DECB directory via Toolshed `decb` |
| Bottom | Problems / Build log / XRoar stdout |

### 2. Lighter layout (editor focus)

- Project tree and Disk panel hidden by default.
- Tab-bar toggles: **Files** · **Disk** (draw drawers).
- Toolbar collapses Disk ops under **Disk ▾**.
- Preference: Comfortable | Compact | Editor focus.

### 3. New project wizard

1. **Name + folder**
2. **Target** — Machine (CoCo 3 selected) · RAM · Dialect/media (DECB .dsk default)
3. **Options** — blank disk, preprocessor on, optional ASM stub, template

Defaults:

- CoCo 3, 512K, DECB  
- `build/work.dsk` 35-track  
- Preprocessor **enabled**

### 4. Preprocessor preview

Side-by-side or toggle:

| Modern (edit) | CoCo (read-only artifact) |
|---------------|---------------------------|
| No required line numbers | Numbered lines |
| Long names, `procedure` | 2-char vars, `GOSUB`/`RETURN` |
| `@target`, `@start`, `@step` | Plain DECB |

- CoCo view is **read-only** in the editor (toggle Modern | CoCo still useful for inspection).
- Rebuild overwrites `build/*.bas` artifacts; no round-trip “edit CoCo → modern.”
- Toolbar: variable map, line step; build copies tokenized program onto disk.

### 5. Preferences

- **Tools** — paths + found/missing for xroar, decb, lwasm, (optional os9)
- **ROMs** — user-supplied paths + checksum status (never shipped)
- **Editor** — font, tab size, Color BASIC keyword colors
- **Preprocessor** — default on/off, naming strategy, line step
- **XRoar** — extra flags, scale, TV/RGB, joysticks, **auto-run keystrokes** (default on)
- **Appearance** — system theme or CoCoIDE dark amber

## Key interactions

### Run pipeline (disk-first)

1. Save modern source (if dirty).
2. If preprocessor on → expand to **read-only** CoCo BASIC under `build/`.
3. Tokenize / `decb copy -t …` into the **project disk image** as the entry program (e.g. `MAIN.BAS`).
4. Assemble ASM → copy type-2 binaries if needed.
5. Launch XRoar with project machine/RAM and the disk mounted.
6. **Auto-run (default on, optional):** after boot, inject keystrokes so DECB loads and runs the entry program, e.g. type `RUN"MAIN"` + Enter (exact sequence TBD with XRoar’s type-in / `-type` / paste mechanism). User can disable for manual `OK` control.
7. Emulator session is for **observation/testing**. Prefer not treating the `.dsk` inside XRoar as a place to `SAVE` permanent changes back into the project; the IDE rebuilds the image from source on each Build/Run. (If XRoar or the host can mark the image read-only or use a temp copy, we should — details at implementation.)

### Multi-file modern BASIC — Option C (hybrid) ✅

Edit many modern sources; **Run builds one linked CoCo program** from an entry file + includes. DECB stays a single-program-in-RAM model.

**Example project tree**

```text
src/
  main.mbas          ' entry (project.cocoide → entry: main.mbas)
  enemies.mbas       ' @include'd from main — not a separate disk program
  hud.mbas
  util_format.mbas   ' marked standalone → also copied as FORMAT.BAS
build/
  main.bas           ' read-only linked CoCo artifact
  util_format.bas    ' read-only artifact for standalone only
work.dsk             ' MAIN.BAS (+ FORMAT.BAS if standalone)
```

**Rules**

1. **Entry file** — one modern source named in `project.cocoide` (default `src/main.mbas`). Auto-run uses its disk name (e.g. `RUN"MAIN"`).
2. **`@include "…"`** — pulls another modern file into the same link unit (shared line numbers, one variable map, procedures → `GOSUB`s). Include graph must be acyclic; diagnostics on missing/circular includes.
3. **Linked output** — preprocessor emits a single read-only CoCo program under `build/`, then tokenizes onto the disk as the entry `.BAS`.
4. **Standalone files** — `@standalone` / `@standalone NAME.BAS` and/or `project.standalone[]` → separate DECB programs on disk (not merged into entry).
5. **Orphan sources** — modern files not reachable from entry includes and not marked standalone: warn at build (“not in link graph; will not be on disk”).
6. **ASM** — unchanged: separate `lwasm` → type-2 `.BIN` on disk; BASIC calls via `LOADM`/`EXEC` as the author writes.

Rejected alternatives (for history): pure single-blob with implicit concat of all files (A); one `.BAS` per source with `LOAD` chaining as the default model (B).

### Disk panel actions ✅

- Refresh directory (`decb dir`)
- **New** blank disk (`decb dskini`, confirm overwrite)
- **Add…** host file / **Add cur** open file (`decb copy` with type 0–3)
- **Extract** selected → host (`decb copy` off image)
- **Delete** selected (`decb kill`, confirm)
- Free granule meter

### Diagnostics (Problems)

Examples tied to UI underlines:

- 2-char variable collisions (or “will be remapped”)
- CoCo 3-only keywords on CoCo 2 target
- `PCLEAR` / `CLEAR` memory impact
- Missing `GOTO`/`GOSUB` targets (post-expand)
- Disk full / granule estimate

## Visual language (proposal)

- **Dark UI** default (fits KDE/dev tools; light theme later).
- **Accent:** warm amber/orange (nod to CoCo / amber CRT), not generic blue-only.
- **Mono editor** for BASIC/ASM; UI sans for chrome.
- **Chips** for target state; **severity** for warnings, not modal spam.

## Resolved UI decisions

| Topic | Decision |
|-------|----------|
| Layout default | **Comfortable three-pane** |
| CoCo expanded source | **Read-only artifact** (inspect via Modern \| CoCo toggle; edit modern only) |
| XRoar launch | Mount project disk; **auto keystrokes to RUN entry program, default on**, user-disableable |
| Emulator vs project | Source of truth = IDE project; XRoar is not the save path for program text |
| Multi-file modern BASIC | **Option C** — entry + `@include` → one `MAIN.BAS`; optional `@standalone` extras |

## Still open

1. Dock bottom panel vs separate XRoar log emphasis (minor).
2. Exact XRoar type-in mechanism (`-type`, paste, startup script) — spike during integration.
3. Preprocessor surface syntax details (`@include`, `@standalone`, procedures, var map).

## Next steps after sketch review

- [x] Layout default: comfortable three-pane
- [x] CoCo output: read-only artifact
- [x] Auto-run keystrokes: optional, default on
- [x] Multi-file packaging: Option C (hybrid)
- [ ] Lock preprocessor surface syntax (minimal `@` directives + procedures + include/standalone)
- [ ] Scaffold PySide6 shell matching Main window wireframe
- [ ] Wire Run → detect xroar/decb → mount + optional type-in
