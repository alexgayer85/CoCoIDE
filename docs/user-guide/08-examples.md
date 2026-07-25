# 08 — Examples

**Docs last updated:** 2026-07-25

Sample projects ship under `examples/`.

## `examples/hello`

Friendly first project.

| File | Role |
|------|------|
| `src/main.mbas` | Entry — title, calls `Greet` |
| `src/greet.mbas` | `@include` module |
| `src/util_clock.mbas` | `@standalone CLOCK.BAS` utility |

**Try:**

```bash
./run.sh examples/hello
```

Then **Build Disk** → Disk list should show `MAIN.BAS` and `CLOCK.BAS` → **Run in XRoar**.

## `examples/diag_fixture`

CoCo **2** project with deliberate issues for the Problems panel:

- CoCo 3 keyword (`hscreen`)  
- `PCLEAR` info  
- Variables sharing a 2-letter prefix  
- Orphan `src/orphan.mbas` (LNK001)  

**Try:**

```bash
./run.sh examples/diag_fixture
```

**Build Disk** and open **Problems**.

## `examples/seabattle`

**Sea Battle** — original 10×10 naval combat (genre homage to the classic
pegboard game; not a Hasbro product).

```bash
./run.sh examples/seabattle
```

Auto or manual fleet placement, coordinate shots (`C7`), simple computer AI.
Multi-file modern BASIC (`@include`). See `examples/seabattle/README.md`.

## `examples/seabattle-ml`

**Sea Battle ML** — hybrid **PMODE 4** game: thin `MAIN.BAS` loader + **6809**
`SEA.BIN`. Dual boards (fleet | radar), cursor controls (WASD/Space). Target
**CoCo 2 · 64K** (CoCo 1/3 fine). See `examples/seabattle-ml/README.md`.

```bash
./run.sh examples/seabattle-ml
```

## Making your own from an example

1. Copy the example folder.  
2. Edit `project.cocoide` `name` and paths if needed.  
3. Replace `src/` contents.  
4. Open with CoCoIDE and Build.

## Next

- [01 — Getting started](01-getting-started.md)  
