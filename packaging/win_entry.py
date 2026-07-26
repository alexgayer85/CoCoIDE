"""PyInstaller entry point for the Windows freeze."""

from __future__ import annotations

from cocoide.app import main

if __name__ == "__main__":
    raise SystemExit(main())
