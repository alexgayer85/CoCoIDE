# 07 — Diagnostics

**Docs last updated:** 2026-07-12

CoCoIDE analyzes your project on **Build**, **Run**, and **Run Diagnostics**.

Full code table: [../diagnostics.md](../diagnostics.md).

## Problems panel

- Color: **red** error · **amber** warning · **blue** info  
- Tab badge: `Problems (errors/warnings/infos)`  
- **Click** a row: open file and jump to line when possible  
  - Modern sources: file line number  
  - Generated `.bas`: searches for CoCo line number text  

## When analysis runs

| Action | Diagnostics |
|--------|-------------|
| Build Disk (Ctrl+B) | Yes |
| Run in XRoar (Ctrl+R) | Yes (after build) |
| Run Diagnostics (Ctrl+Shift+D) | Yes + focus Problems |

Hard **errors** are shown clearly but do not always block writing the disk (you can still inspect). Prefer fixing errors before relying on Run.

## What gets checked

### Variables (2-character rule)

- Long names remapped (`title` → `TI`) — **info**  
- Two names that would alias without remapping — **info**  
- Keyword used as a variable — **warning**  
- True short-name collision — **error**  

### Target / dialect

- CoCo 3 keywords on CoCo 1/2 (`HSCREEN`, `WIDTH`, …) — **error**  
- `ON ERR GOTO` / `ON BRK GOTO` on CoCo 1/2 — **error**  
- Non-DECB constructs (`WHILE`, …) — **error**  

### Memory

- `PCLEAR` page cost — **info** / tight RAM **warning**  
- Large or tiny `CLEAR` string space — **warning** / **info**  
- High `POKE` / `EXEC` vs target RAM — **warning**  

### Generated lines

- `GOTO` / `GOSUB` to missing lines — **error**  
- Duplicate line numbers — **error**  
- First executable is bare `RETURN` — **error** (?RG)  

### Disk and packaging

- No free granules — **error**  
- Almost full — **warning**  
- Orphan `.mbas` (not included, not standalone) — **warning**  

### Preprocessor

- Arity mismatches, circular includes, etc. — **warning**  

## Tips

- **Infos** about remapping are normal with modern BASIC.  
- Use `examples/diag_fixture` to see a dense set of intentional findings.  
- Change `target` in `project.cocoide` if you meant CoCo 3 features on a CoCo 2 project.

## Next

- [08 — Examples](08-examples.md)  
- [10 — Troubleshooting](10-troubleshooting.md)  
