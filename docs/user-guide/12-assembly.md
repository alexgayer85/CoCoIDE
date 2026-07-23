# 12 — 6809 assembly (lwasm) & BIN disassembly

**Docs last updated:** 2026-07-12

## Assemble with LWTOOLS

CoCoIDE uses **[lwasm](https://www.lwtools.ca/)** (must be on `PATH` as `lwasm`).

### Sources

| Location | Behavior |
|----------|----------|
| `src/**/*.asm` (also `.a`, `.s`) | Auto-discovered on **Build Disk** |
| `project.cocoide` → `"asm_sources": ["src/foo.asm"]` | Optional explicit list (still also scans `src/`) |

### Build

**Build Disk** (Ctrl+B) or **Build → Assemble ASM only** (Ctrl+Shift+A):

1. `lwasm -9 --format=decb -o build/<name>.bin src/<name>.asm`  
2. Listing → `build/<name>.lst`  
3. Copy onto the project disk as **type 2** ML, e.g. `BEEP.BIN`  
4. Build **kills all rewrite targets first** (BAS + BINs), then copies —  
   needed on packed game disks (error 248).  
5. **Name must match** the file on the image: `src/game.asm` → `GAME.BIN`.  
   If the disk has `ML.BIN` but you build `GAME.BIN`, kill cannot free space  
   for the new name — rename the `.asm` (or free granules / use a bigger disk).

### Sample

`examples/hello/src/beep.asm` → `BEEP.BIN`.

From DECB BASIC (sound path must be on):

```basic
10 AUDIO ON
20 LOADM"BEEP"
30 EXEC
```

Auto-run only runs your entry `.BAS`, not the ML — type the above at `OK` or put it in your program.

### Writing ASM

- Use standard lwasm / 6809 syntax  
- Prefer `org $xxxx` and `end START` for DECB LOADM  
- Output format is **DECB** (CoCo `LOADM` headers), not raw unless you change the tool flags in code  

### Status bar

`lwasm=OK` / `missing` appears with the other tools.

---

## Disassemble BINs (best-effort)

Machine code cannot be perfectly “decompiled” back to the original source. CoCoIDE offers a **practical disassembly** for study and light edits.

### How to test (hello sample)

```bash
./run.sh examples/hello
```

1. **Build Disk** (or **Assemble ASM only**) so `build/beep.bin` exists.  
2. Either:
   - **Double-click** `build/beep.bin` in the project tree → choose **Yes** to disassemble, or  
   - **Build → Disassemble BIN file…** → pick `examples/hello/build/beep.bin`  
3. CoCoIDE writes `src/imported/beep.asm` and opens it in the editor.  
4. Check the **Build** log for “Disassembled with built-in…”.

**Do not** expect double-click alone to open a `.bin` as text — that used to throw a UTF-8 error in the console. Binary files are detected and offered for disassembly.

### When importing a disk

In **Browse Disk Image…**, enable:

**Disassemble .BIN / ML to .asm (best-effort 6809)** (default on)

Imported `FOO.BIN` also produces `foo.asm` next to it.

### Manual

**Build → Disassemble BIN file…** → pick a `.bin` → writes `.asm` under `src/imported/` (if a project is open) and opens it.

### How good is it?

| Method | Notes |
|--------|--------|
| **Built-in 6809 disassembler** | Always available. Parses DECB LOADM segments; emits `org`, labels on their own lines, TFR/EXG register pairs, PSHS/PULS register lists, full RMW memory ops, and force-sync at branch targets so lwasm can reassemble clean code. |
| **f9dasm** (if installed on `PATH`) | Used automatically when present; often higher quality for mixed code/data. |

**Expectations:**

- Pure code (or mostly code) DECB BINs often **round-trip** with lwasm (`--format=decb`) after a re-disassemble.  
- **Data tables mixed into code** may still decode as nonsense instructions — mark those regions as `fcb`/`fdb` by hand.  
- Older listings from an earlier CoCoIDE build may show **bad operand** errors (`TFR #$98`, stuck labels). Re-run **Build → Disassemble BIN file…** to regenerate.  
- If reassembly still fails, check the first lwasm error lines, or install **f9dasm**.  

True high-level decompilation (C/BASIC from ML) is **out of scope**.

---

## Related

- [05 — Build and Run](05-build-and-run.md)  
- [11 — Import disks](11-import-disks.md)  
