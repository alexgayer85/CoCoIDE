"""Application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from cocoide.mainwindow import MainWindow
from cocoide.project import PROJECT_FILENAME, Project


def _load_stylesheet() -> str:
    qss = Path(__file__).with_name("style.qss")
    if qss.is_file():
        return qss.read_text(encoding="utf-8")
    return ""


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv
    app = QApplication(argv)
    app.setApplicationName("CoCoIDE")
    app.setOrganizationName("CoCoIDE")
    app.setStyle("Fusion")
    # Do NOT setStyleSheet on QApplication — that forces non-native QFileDialog
    # chrome with blank toolbar icons on Linux. Theme is applied on MainWindow.

    project: Project | None = None
    # Optional CLI: cocoide /path/to/project  or  cocoide /path/to/project.cocoide
    if len(argv) > 1:
        p = Path(argv[1]).expanduser().resolve()
        root = p.parent if p.name == PROJECT_FILENAME else p
        if (root / PROJECT_FILENAME).is_file():
            try:
                project = Project.load(root)
            except (OSError, ValueError) as exc:
                print(f"Could not load project: {exc}", file=sys.stderr)

    win = MainWindow(project=project)
    qss = _load_stylesheet()
    if qss:
        win.setStyleSheet(qss)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
