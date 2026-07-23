# Documentation map

**Docs last updated:** 2026-07-12

## For users (how to operate CoCoIDE)

Start at **[user-guide/README.md](user-guide/README.md)**.

That tree is the **instruction manual**. Update it whenever user-visible behavior changes.

## For contributors / design

| Path | Purpose |
|------|---------|
| [user-guide/](user-guide/) | End-user instructions (keep current) |
| [UI.md](UI.md) | UX/product decisions, wireframe notes |
| [preprocessor.md](preprocessor.md) | Preprocessor reference |
| [diagnostics.md](diagnostics.md) | Diagnostic code reference |
| [ui-sketches/](ui-sketches/) | HTML wireframes |
| [DOCUMENTATION.md](DOCUMENTATION.md) | This map |
| [../README.md](../README.md) | Repo overview, quick start, license |

## Rule for feature work

When you add or change a feature:

1. Implement the code.  
2. Update the matching **user-guide** page (or add one + link from the index).  
3. Update reference pages (`preprocessor.md`, `diagnostics.md`) if codes/directives change.  
4. Set **Docs last updated** on touched guide pages.  
5. Mention docs in the commit/PR.

Do **not** leave behavior only in chat history or design notes—users need the guide.
