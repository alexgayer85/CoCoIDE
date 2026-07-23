# Modern BASIC preprocessor (reference)

**User-oriented instructions:** [user-guide/04-modern-basic.md](user-guide/04-modern-basic.md)

Source of truth: `*.mbas` (and includes).  
Output: read-only `build/*.bas` → tokenized onto the DECB disk.

**Docs last updated:** 2026-07-12

## Directives

| Directive | Meaning |
|-----------|---------|
| `@target coco3, 512k, decb` | Documented target (diagnostics later) |
| `@start 100` | First line number |
| `@step 10` | Line number increment |
| `@include "file.mbas"` | Merge into this **link unit** (Option C) |
| `@standalone` | Build as its **own** DECB program (not merged into entry) |
| `@standalone CLOCK.BAS` | Same, with explicit disk name |

### `@standalone` (Option C)

```basic
@standalone CLOCK.BAS

procedure Main()
  print "UTILITY"
end
```

- Produces `build/util_clock.bas` (read-only) and copies **`CLOCK.BAS`** onto the disk beside `MAIN.BAS`.
- Not part of the entry `RUN"MAIN"` image.
- May use its own `@include` graph.
- Also listable in `project.cocoide` → `"standalone": ["src/util_clock.mbas"]` or `"src/foo.mbas:FOO.BAS"`.
- Files that are neither included nor standalone get **LNK001** (orphan warning).
- If a file is both `@include`'d and `@standalone`, you get a warning (merged into MAIN *and* copied separately).

## Procedures and parameters

```basic
procedure Greet(who$)
  print "HELLO, "; who$
end

procedure Main()
  Greet("WORLD")
end
```

Expands roughly to:

```basic
… GOTO entry …
REM PROC GREET
PRINT "HELLO, "; WH$
RETURN
REM PROC MAIN
WH$="WORLD"
GOSUB <greet>
RETURN
REM ENTRY
GOSUB <main>
END
```

**Semantics (v0.2):**

- Parameters are **globals** assigned immediately before `GOSUB` (not a stack).
- Nested/recursive calls that share parameter names will clobber values.
- Argument count mismatches produce build warnings.
- String literals, numbers, and simple identifiers are valid arguments.

## Labels

```basic
waitkey:
  k$ = inkey$
  if k$ = "" then goto waitkey
```

`goto name` becomes a line-number `GOTO` after layout.

## Layout rules

1. Header / file REMs  
2. `GOTO entry` (skips procedure bodies — avoids `?RG ERROR`)  
3. Procedures ending in `RETURN`  
4. Entry (`Main` or top-level code)  
5. `END`

## Not DECB

`while` / `wend` / `do` / `loop` etc. are flagged as warnings; they are not expanded to legal CoCo BASIC yet.
