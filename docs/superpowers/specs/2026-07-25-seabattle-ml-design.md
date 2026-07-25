# Sea Battle ML (hybrid) — design

**Date:** 2026-07-25  
**Status:** Approved for implementation  
**Location:** `examples/seabattle-ml`

## Goals

- Hybrid **DECB BASIC loader + 6809 ML** game engine.
- **Text screen** (32×16 VDG), **dual side-by-side boards** like the physical game.
- Compatible with **CoCo 1/2/3** (default project: CoCo 2 · 64K · DECB).
- Full gameplay parity with `examples/seabattle` (modern BASIC).

## Non-goals (v1)

- PMODE / SG graphics, CoCo 3 HSCREEN.
- Replacing BASIC `examples/seabattle`.
- Network / two-player hotseat.

## Architecture

| Piece | Role |
|-------|------|
| `src/main.bas` | Thin loader: `CLEAR`, `LOADM"SEA"`, `EXEC` |
| `src/sea.asm` | Full game → `SEA.BIN` via lwasm `--format=decb` |
| `project.cocoide` | `preprocessor: false`, `target: coco2`, `memory_kb: 64` |

### Load address

- ML `org $3F00`
- BASIC: `CLEAR 200,&H3F00` so HIMEM protects the binary.

### Screen

- Text RAM `$0400` (32×16).
- **Battle layout:** left = your fleet (`PS`), right = radar (`RD`).
- Glyphs: `.` water · `#` ship · `o` miss · `*` hit.
- Placement may show fleet full-width or dual with empty radar.

### Data (100-byte grids, row-major, 0-based)

| Grid | Meaning |
|------|---------|
| `PS` | Player ships: 0 empty, 1–5 id, 6 miss, 7 hit |
| `ES` | Enemy ships (same encoding; hidden except via radar) |
| `RD` | Radar / player shots: 0 unknown, 1 miss, 2 hit |
| `AK` | Attacks on player: 0 unshot, 1 miss, 2 hit |

Ship lengths: 5,4,3,3,2 · `PH`/`EH` start at 17.

### Flow

1. Title → wait Enter  
2. Place player (A auto / M manual)  
3. Auto-place enemy  
4. Battle: dual draw → player shot (or F fleet-only pause) → AI shot → until PH or EH 0  
5. Game over → wait Enter → RTS to BASIC  

### I/O

- Keyboard via ROM **POLCAT** (`[$A000]`); line buffer for coords.
- Coords: `A1`–`J10` (`0` = column 10); case-insensitive.
- Sound: short 6-bit DAC tones at `$FF20` (hit/miss).

### AI

Port of BASIC: random fire; after hit, hunt orthogonal neighbors; clear hunt on sink.

## Success criteria

- Builds with CoCoIDE / `lwasm` + `decb`.
- Playable under XRoar `coco2` and `coco3`.
- Dual boards visible during combat.
- Noticeably faster redraw than BASIC Sea Battle.
