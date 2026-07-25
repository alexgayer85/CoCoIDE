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
| Empty / dot | Water / unknown |
| Solid block | Your ship (left) or hit |
| Small block | Miss |

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
| `src/main.bas` | `CLEAR` / `PCLEAR4` / `PMODE4,1` / `SCREEN1,1` / `LOADM"SEA"` / `EXEC` |
| `src/sea.asm` | Game + PMODE 4 draw + **matrix keyboard** (not POLCAT) |

ML load address **`$3F00`**. Graphics page **`$0E00`** (standard after `PCLEAR 4`).

## Why matrix keys?

`JSR [$A000]` (POLCAT) is often unreliable under XRoar after `EXEC`. This build reads the keyboard **PIA matrix** directly and times out so “press any key” cannot hang the game.
