# CoCoIDE User Guide

Instructions for **using** CoCoIDE day to day.  
If you are changing the product, also update this guide (see [Keeping docs current](#keeping-docs-current)).

| Audience | Start here |
|----------|------------|
| New user | [01 — Getting started](01-getting-started.md) |
| Writing programs | [04 — Modern BASIC](04-modern-basic.md) |
| Build / emulator | [05 — Build and Run](05-build-and-run.md) |
| Disk images | [06 — Disk panel](06-disk-panel.md) |
| Warnings | [07 — Diagnostics](07-diagnostics.md) |
| Import disks | [11 — Browse & import disks](11-import-disks.md) |
| Assembly | [12 — Assembly & BIN disassembly](12-assembly.md) |

## Contents

1. [Getting started](01-getting-started.md) — install tools, launch, first project  
2. [Projects](02-projects.md) — `project.cocoide`, folders, targets  
3. [Main window](03-main-window.md) — three panes, toolbar, menus  
4. [Modern BASIC](04-modern-basic.md) — `.mbas`, procedures, includes, standalone  
5. [Build and Run](05-build-and-run.md) — disk build, XRoar, auto-run  
6. [Disk panel](06-disk-panel.md) — New / Add / Extract / Delete  
7. [Diagnostics](07-diagnostics.md) — Problems panel and codes  
8. [Examples](08-examples.md) — sample projects in the repo  
9. [Keyboard shortcuts](09-shortcuts.md)  
10. [Troubleshooting](10-troubleshooting.md)  
11. [Browse & import disks](11-import-disks.md) — external `.dsk`, import, new project from disk  
12. [Assembly & BIN disassembly](12-assembly.md) — lwasm, LOADM, best-effort decompile  

## Related (not the user manual)

| Doc | Role |
|-----|------|
| [../UI.md](../UI.md) | Design decisions / wireframe notes |
| [../preprocessor.md](../preprocessor.md) | Preprocessor reference (deeper) |
| [../diagnostics.md](../diagnostics.md) | Diagnostic code table (reference) |
| [../ui-sketches/index.html](../ui-sketches/index.html) | Interactive UI sketches |
| [../../README.md](../../README.md) | Project overview / license |

## Keeping docs current

Whenever you **add, change, or remove** a user-visible feature:

1. Update the relevant page under `docs/user-guide/`.  
2. If it is a new topic, add a page and link it from this index.  
3. Bump the **“Docs last updated”** line at the bottom of the changed page.  
4. Mention the doc change in the PR or commit message.

This guide is the source of truth for **how to operate** CoCoIDE. Design history stays in `docs/UI.md`.

---

*CoCoIDE is open source (MIT). External tools (XRoar, Toolshed, ROMs) have their own licenses and requirements.*
