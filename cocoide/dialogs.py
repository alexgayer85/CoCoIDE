"""File/folder dialogs that match CoCoIDE’s dark theme and stay readable.

Qt’s stock toolbar uses icon-only toolbuttons; without a working icon theme they
look blank. We force a non-native dialog, apply the same dark amber palette as
the main window, and use **short text labels** (with tooltips for the full name)
so nothing is truncated into \"F…d\" / \"N…r\".
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QStyle, QToolButton, QWidget

# objectName → (short label, full tooltip, theme icons, standard pixmap)
_TOOLBAR_BUTTONS: dict[
    str, tuple[str, str, list[str], QStyle.StandardPixmap | None]
] = {
    "backButton": (
        "Back",
        "Back",
        ["go-previous", "arrow-left"],
        QStyle.StandardPixmap.SP_ArrowBack,
    ),
    "forwardButton": (
        "Fwd",
        "Forward",
        ["go-next", "arrow-right"],
        QStyle.StandardPixmap.SP_ArrowForward,
    ),
    "toParentButton": (
        "Up",
        "Parent directory",
        ["go-up", "arrow-up"],
        QStyle.StandardPixmap.SP_FileDialogToParent,
    ),
    "newFolderButton": (
        "New",
        "Create new folder",
        ["folder-new", "folder_new"],
        QStyle.StandardPixmap.SP_FileDialogNewFolder,
    ),
    "listModeButton": (
        "List",
        "List view",
        ["view-list-icons", "view-list"],
        QStyle.StandardPixmap.SP_FileDialogListView,
    ),
    "detailModeButton": (
        "Detail",
        "Detail view",
        ["view-list-details", "view-detailed"],
        QStyle.StandardPixmap.SP_FileDialogDetailedView,
    ),
}

# Same dark amber language as style.qss (main window)
_DIALOG_QSS = """
QFileDialog {
    background-color: #1a1d23;
    color: #e8eaed;
    font-size: 13px;
}
QFileDialog QWidget {
    background-color: #1a1d23;
    color: #e8eaed;
}
QFileDialog QLabel {
    background: transparent;
    color: #9aa3b2;
}
QFileDialog QToolButton {
    background-color: #2a2f3a;
    color: #e8eaed;
    border: 1px solid #3a4150;
    border-radius: 4px;
    padding: 3px 6px;
    margin: 1px;
    min-height: 22px;
    max-height: 28px;
    font-size: 12px;
}
QFileDialog QToolButton:hover {
    border-color: #f48c06;
    background-color: #323844;
}
QFileDialog QToolButton:pressed,
QFileDialog QToolButton:checked {
    background-color: rgba(232, 93, 4, 0.25);
    border-color: #e85d04;
}
QFileDialog QLineEdit,
QFileDialog QComboBox,
QFileDialog QSpinBox {
    background-color: #161920;
    color: #e8eaed;
    border: 1px solid #3a4150;
    border-radius: 4px;
    padding: 4px 6px;
    min-height: 22px;
}
QFileDialog QComboBox QAbstractItemView {
    background-color: #22262e;
    color: #e8eaed;
    selection-background-color: rgba(232, 93, 4, 0.35);
}
QFileDialog QTreeView,
QFileDialog QListView {
    background-color: #161920;
    color: #c8cdd6;
    border: 1px solid #2e3440;
    border-radius: 4px;
    alternate-background-color: #1e222a;
}
QFileDialog QTreeView::item:selected,
QFileDialog QListView::item:selected {
    background-color: rgba(232, 93, 4, 0.25);
    color: #f48c06;
}
QFileDialog QHeaderView::section {
    background-color: #22262e;
    color: #9aa3b2;
    border: none;
    border-right: 1px solid #2e3440;
    padding: 4px 6px;
}
QFileDialog QPushButton {
    background-color: #2a2f3a;
    color: #e8eaed;
    border: 1px solid #3a4150;
    border-radius: 5px;
    padding: 5px 12px;
    min-width: 4.5em;
}
QFileDialog QPushButton:hover {
    border-color: #f48c06;
    background-color: #323844;
}
QFileDialog QPushButton:default {
    background-color: #e85d04;
    color: #1a1008;
    border: none;
    font-weight: 600;
}
QFileDialog QSplitter::handle {
    background-color: #2e3440;
    width: 2px;
}
QFileDialog QScrollBar:vertical {
    background: #161920;
    width: 10px;
}
QFileDialog QScrollBar::handle:vertical {
    background: #3a4150;
    border-radius: 4px;
    min-height: 20px;
}
"""


def _icon_for(
    theme_names: list[str],
    std: QStyle.StandardPixmap | None,
    style: QStyle,
) -> QIcon:
    for name in theme_names:
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
    if std is not None:
        icon = style.standardIcon(std)
        if not icon.isNull():
            return icon
    return QIcon()


def _label_file_dialog_toolbar(dlg: QFileDialog) -> None:
    """Short text labels + tooltips; compact so six buttons fit in one row."""
    style = dlg.style()
    assert style is not None
    for btn in dlg.findChildren(QToolButton):
        name = btn.objectName()
        if name not in _TOOLBAR_BUTTONS:
            if not btn.text() and btn.toolTip():
                tip = btn.toolTip().split("\n")[0]
                btn.setText(tip[:8])
                btn.setToolTip(tip)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            continue

        short, tip, themes, std = _TOOLBAR_BUTTONS[name]
        icon = _icon_for(themes, std, style)
        btn.setIcon(icon)
        btn.setText(short)
        btn.setToolTip(tip)
        btn.setAutoRaise(False)
        # Text only is more reliable and compact than icon+truncated on narrow bars
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        btn.setIconSize(QSize(16, 16))
        # Let layout size to text — avoid fixed huge min-width
        btn.setMinimumWidth(0)
        btn.setMaximumWidth(16777215)
        btn.updateGeometry()


def _make_dialog(parent: QWidget | None, caption: str, directory: str) -> QFileDialog:
    dlg = QFileDialog(parent, caption, directory)
    dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dlg.setStyleSheet(_DIALOG_QSS)
    # A bit wider so the toolbar row is not crushed
    dlg.resize(780, 480)
    return dlg


def _prepare(dlg: QFileDialog) -> None:
    _label_file_dialog_toolbar(dlg)


def get_open_file_name(
    parent: QWidget | None,
    caption: str,
    directory: str = "",
    file_filter: str = "All files (*.*)",
) -> tuple[str, str]:
    dlg = _make_dialog(parent, caption, directory)
    dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
    dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
    dlg.setNameFilter(file_filter)
    _prepare(dlg)
    if dlg.exec():
        files = dlg.selectedFiles()
        return (files[0] if files else "", dlg.selectedNameFilter())
    return ("", "")


def get_save_file_name(
    parent: QWidget | None,
    caption: str,
    directory: str = "",
    file_filter: str = "All files (*.*)",
) -> tuple[str, str]:
    dlg = _make_dialog(parent, caption, directory)
    dlg.setFileMode(QFileDialog.FileMode.AnyFile)
    dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dlg.setNameFilter(file_filter)
    dlg.setOption(QFileDialog.Option.DontConfirmOverwrite, False)
    _prepare(dlg)
    if dlg.exec():
        files = dlg.selectedFiles()
        return (files[0] if files else "", dlg.selectedNameFilter())
    return ("", "")


def get_existing_directory(
    parent: QWidget | None,
    caption: str,
    directory: str = "",
) -> str:
    dlg = _make_dialog(parent, caption, directory)
    dlg.setFileMode(QFileDialog.FileMode.Directory)
    dlg.setOption(QFileDialog.Option.ShowDirsOnly, True)
    _prepare(dlg)
    if dlg.exec():
        files = dlg.selectedFiles()
        return files[0] if files else ""
    return ""


def ensure_dir(path: str | Path) -> str:
    """Create directory if needed; return path string for dialog start dir."""
    p = Path(path)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError:
        return str(Path.home())
    return str(p)
