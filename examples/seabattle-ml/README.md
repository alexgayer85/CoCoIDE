# Sea Battle ML — CoCoIDE hybrid example

**6809** naval combat with **PMODE 4** dual boards (your fleet | radar).
Works on **CoCo 1 / 2 / 3** (ECB graphics, not CoCo‑3 only).

Companion to the text/BASIC game in `examples/seabattle`.

## Play

```bash
./run.sh examples/seabattle-ml
```

**Build Disk** → **Run in XRoar**. Default: **CoCo 2 · 64K**.

Click the **XRoar window** so it has keyboard focus.

### Controls (cursor — no typing coordinates)

| Key | Action |
|-----|--------|
| **W A S D** | Move (standard WASD — **A is left**) |
| **I/K J/L** | Alternate up/down left/right |
| **Space** / **Enter** | Place ship or fire |
| **R** | Rotate ship (placement) |
| **P** or **0** | Auto-place fleet (not A!) |
| **F** | Full redraw |

Cursor moves only touch one cell. Labels use **pre-baked 8×8 glyphs** (8 byte stores per character, not per-pixel Plot2).

After a result message, press a key to continue.

### Glyphs (graphics)

| Cell | Meaning |
|------|---------|
| Hollow box | Water / unknown |
| Mini hull shapes | Your ships (left board; size/style by type) |
| Small blob | Miss |
| X | Hit |

## Layout

```text
  YOUR FLEET              RADAR
  ┌──────────┐         ┌──────────┐
  │  ships   │         │  shots   │
  └──────────┘         └──────────┘
  E:nn Y:nn
```

## Sources

| File | Role |
|------|------|
| `src/main.bas` | Loader: `PMODE4` → `LOADM"NAVAL"` → `LOADM"SEA"` → `EXEC` |
| `src/naval.asm` | Splash LOADM image → **`$0E00`** (full PMODE 4 page) |
| `src/naval_pmode4.bin` | Raw **6144-byte** PMODE 4 framebuffer (included by `naval.asm` + embedded fallback in `sea.asm`) |
| `src/sea.asm` | Game ML at **`$3F00`** |

Replace the splash by overwriting `src/naval_pmode4.bin` (exactly 6144 bytes) and rebuilding.

## Why matrix keys?

`JSR [$A000]` (POLCAT) is often unreliable under XRoar after `EXEC`. This build reads the keyboard **PIA matrix** directly and times out so “press any key” cannot hang the game.
