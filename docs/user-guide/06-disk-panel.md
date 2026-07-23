# 06 — Disk panel

**Docs last updated:** 2026-07-12

The right-hand **Disk** pane is a live Toolshed view of your project `.dsk`.

## Header

- Image name (e.g. `work.dsk`)  
- Geometry hint (currently **35T SS DECB** for new images)  
- **Free granules** `N / total`  
- **Bar graph** of used space (green → amber → red as it fills)  

## File list

One row per DECB file (name, type, ASCII/binary, granules).  
**Select** a row before Extract or Delete.

## Buttons

| Button | Action |
|--------|--------|
| **New** | Create a blank 35-track DECB image. Confirms if the image already exists (destroys contents). |
| **Add…** | Pick a host file and copy it onto the disk. |
| **Add cur** | Copy the **currently open** host file onto the disk. |
| **Extract** | Copy the selected disk file out to the host (save dialog). |
| **Delete** | Remove the selected file from the image (confirms). |
| **Mount…** | Browse **any** `.dsk` (import, use as project disk, new project). See [11 — Import disks](11-import-disks.md). |
| **↻** | Refresh directory and free bar. |

**Build Disk** also refreshes this panel after packaging programs.

## Adding files

### Type guessing

| Host extension | DECB type | Notes |
|----------------|-----------|--------|
| `.bas`, `.asc` | 0 BASIC | Tokenize when possible |
| `.bin`, `.rom` | 2 machine language | |
| `.dat` | 1 data | |
| `.txt`, `.asm` | 3 text | EOL translate when sensible |

Names are forced toward DECB **8.3** (`hello_test.bas` → `HELLOTES.BAS`).

Replacing a file that already exists on the image **deletes the old granule
allocation first**, then copies the new data. That avoids Toolshed error 248
when the disk is already full (overwrite-in-place would not free space in time).

### Modern BASIC (`.mbas`)

**Add cur** will **not** raw-copy `.mbas`.  
Use **Build Disk** so the preprocessor + tokenization run.  
Standalone modules with `@standalone` are included automatically on Build.

## New vs Build

| Action | Result |
|--------|--------|
| **New** | Empty disk only |
| **Build Disk** | Creates disk if needed **and** installs entry + standalones |

## Relation to XRoar

Run mounts this same image with **write-back disabled**.  
Use **Extract** if you need a host copy of something that only exists on the image; prefer keeping masters under `src/`.

## Next

- [05 — Build and Run](05-build-and-run.md)  
- [07 — Diagnostics](07-diagnostics.md)  
