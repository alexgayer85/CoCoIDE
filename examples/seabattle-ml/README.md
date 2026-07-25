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
| **W S** | Move cursor up / down |
| **J L** or **D** | Move left / right (`A` = auto-place, not left) |
| **Space** or **Enter** | Fire (battle) / place ship |
| **R** | Rotate ship (placement) |
| **A** | Auto-place your remaining fleet |
| **F** | Full redraw (battle) |

Cursor moves **without** redrawing the whole screen (only the cursor cell).

After HIT / MISS / computer turn, press **any key** (or wait — there is a timeout so the game cannot freeze forever).

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
