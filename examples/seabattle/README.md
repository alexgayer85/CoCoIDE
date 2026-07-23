# Sea Battle — CoCoIDE example

Original **10×10 naval grid combat** for the Tandy Color Computer, written as a
CoCoIDE modern-BASIC example.

Inspired by the classic pegboard / electronic naval guessing game popularized
by Milton Bradley — **this is not that product**, and is not affiliated with
Hasbro or Milton Bradley.

## Play

```bash
./run.sh examples/seabattle
```

Then **Build Disk** → **Run in XRoar** (or use the toolbar).

### Rules (short)

| Ship        | Length |
|-------------|--------|
| Carrier     | 5      |
| Battleship  | 4      |
| Cruiser     | 3      |
| Submarine   | 3      |
| Destroyer   | 2      |

1. Click the **XRoar window** so it has keyboard focus.  
2. At prompts, type a response and press **Enter** (not only a letter key).  
3. Placement: `A` + Enter (auto) or `M` + Enter (manual).  
4. After Enter on the title, you should see **INITIALIZING…** then fleet placement  
   (if it sat still before, that was slow grid-clear loops — now removed).  
5. When asked **YOUR SHOT**, type a coordinate such as `C7` or `J10`  
   (use `0` for column 10, e.g. `A0`), then Enter.  
6. Type `F` then Enter to view your own fleet.  

Symbols: `.` unknown/water · `#` your ship · `o` miss · `*` hit  

## Sources

| File | Role |
|------|------|
| `src/main.mbas` | Entry |
| `src/ships.mbas` | Fleet data & placement |
| `src/grid.mbas` | UI, coords, deployment |
| `src/ai.mbas` | Shots, AI, win/lose |

`preprocessor: true` · target **CoCo 3** · **DECB** disk.

## Notes

- Uses `SOUND` for hit/miss feedback (needs working XRoar audio).  
- **Speed:** `POKE 65497,0` (CoCo 3 high speed) at start; grids draw with  
  one string/`PRINT` per row and glyph tables (`mid$`) instead of per-cell `PRINT`.  
- AI is intentionally simple (random + neighbor hunt after a hit).  
- Good playground for `@include`, multi-module modern BASIC, and full-disk builds.  
