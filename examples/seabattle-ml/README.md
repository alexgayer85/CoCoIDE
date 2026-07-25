# Sea Battle ML — CoCoIDE hybrid example

**6809 machine-language** naval grid combat with a thin DECB BASIC loader.
Text-screen **dual boards** (your fleet | radar), playable on **CoCo 1 / 2 / 3**.

Companion to the modern-BASIC game in `examples/seabattle` (not affiliated with
Hasbro / Milton Bradley).

## Play

```bash
./run.sh examples/seabattle-ml
```

**Build Disk** → **Run in XRoar**. Default project: **CoCo 2 · 64K**.

Or change the green target chip to CoCo 3 if you prefer.

### Controls

1. Click the **XRoar** window for keyboard focus.  
2. **Enter** to continue prompts.  
3. Placement: type **A** (auto) or **M** (manual), then Enter.  
4. Manual: coordinate (`B3`), Enter, then **H** or **V**, Enter.  
5. Shots: `C7` or `J0` (0 = column 10), Enter.  
6. **F** then Enter pauses (boards stay visible).  

Glyphs: `.` water · `#` ship · `o` miss · `*` hit  

## Layout (battle)

```text
 YOUR FLEET          RADAR
 1234567890          1234567890
A ..###.....        A ...o.*....
...
E:xx Y:yy
```

## Sources

| File | Role |
|------|------|
| `src/main.bas` | `CLEAR200,&H3F00` · `LOADM"SEA"` · `EXEC` |
| `src/sea.asm` | Full game engine → `SEA.BIN` |

`preprocessor: false` · ML at `$3F00` · DECB disk.

## Notes

- Faster board redraws than the BASIC version (direct text RAM).  
- AI: random fire + neighbor hunt after a hit.  
- Design: `docs/superpowers/specs/2026-07-25-seabattle-ml-design.md`  
