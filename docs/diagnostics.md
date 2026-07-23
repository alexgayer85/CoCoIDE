# Diagnostics (reference)

**User-oriented instructions:** [user-guide/07-diagnostics.md](user-guide/07-diagnostics.md)

Run via **Build → Build Disk** (Ctrl+B), **Build → Run Diagnostics** (Ctrl+Shift+D), or **Run in XRoar**.

Results appear in the **Problems** panel (color-coded). Click a row to open the file and jump to the line when possible.

**Docs last updated:** 2026-07-12

| Code | Severity | Meaning |
|------|----------|---------|
| VAR001 | error | Two long names mapped to the same 2-char short name |
| VAR002 | info | Modern names share a 2-letter prefix (would alias without remap) |
| VAR003 | info | Summary of long→short remaps |
| VAR004 | warning | BASIC keyword used as a variable |
| SYN001 | error | Construct not in DECB / not translated (`while`, etc.) |
| TGT001 | error | CoCo 3 keyword on CoCo 1/2 target |
| TGT002 | error | CoCo 3 phrase on CoCo 1/2 (`ON ERR GOTO`, `ON BRK GOTO`) |
| MEM001–MEM009 | mixed | `PCLEAR` / `CLEAR` / high `POKE`·`EXEC` vs RAM |
| LN001–LN003 | error | Duplicate / missing line numbers in generated BASIC |
| RG001 | error | First executable is `RETURN` (?RG ERROR) |
| DSK001–DSK003 | mixed | Disk full / nearly full |
| LNK001 | warning | `.mbas` not in include graph and not `@standalone` |
| PP000 | warning | Preprocessor message |

Fixture project: `examples/diag_fixture` (CoCo 2 + intentional issues).
