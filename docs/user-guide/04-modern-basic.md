# 04 — Modern BASIC

**Docs last updated:** 2026-07-12

When the project has `"preprocessor": true` (default), you edit **modern** sources (`.mbas`). CoCoIDE expands them to classic DECB text, then tokenizes onto the disk.

Deep reference: [../preprocessor.md](../preprocessor.md).

## Why modern BASIC?

Color BASIC only treats the **first two characters** of a variable name as significant (`SCORE` ≡ `SC`). Line numbers are mandatory. Modern mode lets you write clearer source; the preprocessor produces legal CoCo BASIC.

## Directives

Place at the top of a file (or near the top):

| Directive | Meaning |
|-----------|---------|
| `@target coco3, 512k, decb` | Documents intent (for you / future checks) |
| `@start 100` | First generated line number |
| `@step 10` | Line number step |
| `@include "other.mbas"` | Pull another file into **this** program |
| `@standalone` | This file is its **own** DECB program |
| `@standalone CLOCK.BAS` | Standalone with explicit disk name |

Comments: `'` or `REM` at the start of a line.

## Procedures and parameters

```basic
procedure Greet(who$)
  print "HELLO, "; who$
end

procedure Main()
  cls
  title$ = "COCOIDE"
  print title$
  Greet("WORLD")
end
```

Expands roughly to:

- Parameter assign + `GOSUB` (e.g. `WH$="WORLD"` then `GOSUB …`)  
- Each procedure ends with `RETURN`  
- A leading `GOTO` skips procedure bodies so `RUN` does not hit `?RG ERROR`  
- Entry calls `Main` (or runs top-level code) then `END`  

**Limits (current):**

- Parameters are **globals**, not a stack (not re-entrant / not recursive-safe).  
- Call arguments: strings, numbers, simple identifiers.  
- Wrong argument counts → diagnostics warnings.

## Multi-file layout (Option C)

| Role | How | On disk |
|------|-----|---------|
| **Entry** | `project.cocoide` → `entry` | One program, e.g. `MAIN.BAS` |
| **Library modules** | `@include "enemies.mbas"` from entry | Merged into entry program |
| **Utilities** | `@standalone` (or `project.standalone`) | Separate files, e.g. `CLOCK.BAS` |
| **Orphans** | Neither include nor standalone | **Not** on disk; **LNK001** warning |

### Include example

`src/main.mbas`:

```basic
@include "greet.mbas"

procedure Main()
  Greet("WORLD")
end
```

`src/greet.mbas`:

```basic
procedure Greet(who$)
  print "HELLO, "; who$
end
```

### Standalone example

`src/util_clock.mbas`:

```basic
@standalone CLOCK.BAS

procedure Main()
  print "CLOCK UTILITY"
end
```

After Build: disk has `MAIN.BAS` **and** `CLOCK.BAS`. Auto-run still runs the **entry** only (`RUN"MAIN"`). Manually `RUN"CLOCK"` in the emulator for the utility.

If a file is both `@include`'d and `@standalone`, you get a warning (merged into MAIN *and* copied separately).

## Labels

```basic
waitkey:
  k$ = inkey$
  if k$ = "" then goto waitkey
```

`goto name` becomes a numeric `GOTO` after layout.

## What is not DECB

These are **not** translated and will fail on a real CoCo / DECB:

- `WHILE` / `WEND`, `DO` / `LOOP`, etc.  
- Diagnostics flag them (**SYN001**).

Use classic `IF … THEN GOTO` patterns instead.

## CoCo 3-only features

On a **CoCo 1/2** project target, diagnostics error on Super Extended features such as:

- `HSCREEN`, `HPRINT`, `WIDTH`, `PALETTE`, …  
- `ON ERR GOTO`, `ON BRK GOTO`  

Use target `coco3` for those programs.

## CoCo stack rules (avoid `?RG ERROR`)

Color BASIC will throw **`?RG ERROR` (RETURN without GOSUB)** if you:

1. **`RETURN` from inside a `FOR`/`NEXT`** — always finish or force the loop variable to the end, then `NEXT`; never `RETURN` out of a `FOR`.  
2. **`CLEAR` while inside a `GOSUB`** — `CLEAR` wipes the GOSUB stack. Put `CLEAR` only at the very start of `Main`. CoCoIDE enters `Main` with **`GOTO`** (and ends it with **`END`**), so `CLEAR` at the top of `Main` is safe; nested procedures still use `GOSUB`/`RETURN`.

## Classic mode

If `"preprocessor": false`, CoCoIDE treats your entry file as already-CoCo source (still copied to disk). Prefer modern mode for new work.

## Next

- [05 — Build and Run](05-build-and-run.md)  
