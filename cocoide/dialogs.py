"""File/folder dialogs that match CoCoIDE’s dark theme and stay readable.

Qt’s stock toolbar uses icon-only toolbuttons; without a working icon theme they
look blank. We force a non-native dialog, apply the same dark amber palette as
the main window, and use **short text labels** (with tooltips for the full name)
so nothing is truncated into \"F…d\" / \"N…r\".
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from cocoide.project import Project

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


# ── Project settings (target machine / RAM) ─────────────────────────

_DIALOG_STYLE = """
QDialog {
    background-color: #1a1d23;
    color: #e8eaed;
    font-size: 13px;
}
QLabel { color: #c8cdd6; }
QComboBox {
    background-color: #161920;
    color: #e8eaed;
    border: 1px solid #3a4150;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 200px;
}
QComboBox:hover { border-color: #f48c06; }
QComboBox QAbstractItemView {
    background-color: #161920;
    color: #e8eaed;
    selection-background-color: rgba(232, 93, 4, 0.35);
}
QPushButton {
    background-color: #2a2f3a;
    color: #e8eaed;
    border: 1px solid #3a4150;
    border-radius: 5px;
    padding: 5px 14px;
}
QPushButton:hover { border-color: #f48c06; }
QPushButton:default {
    background-color: #e85d04;
    color: #1a1008;
    font-weight: 600;
    border: none;
}
"""


def edit_project_settings(
    parent: QWidget | None,
    project: "Project",
) -> bool:
    """Show project target / RAM dialog. Returns True if the project was changed and saved."""
    from cocoide.tools import MACHINE_PROFILES, normalize_target_ram

    dlg = QDialog(parent)
    dlg.setWindowTitle("Project settings")
    dlg.setModal(True)
    dlg.setStyleSheet(_DIALOG_STYLE)
    dlg.setMinimumWidth(400)

    layout = QVBoxLayout(dlg)
    intro = QLabel(
        "Bootable machine + RAM for diagnostics, Build, and XRoar.\n"
        "Only combinations that match real CoCo configs are listed.\n"
        "Saved to project.cocoide."
    )
    intro.setWordWrap(True)
    intro.setStyleSheet("color: #9aa3b2; margin-bottom: 8px;")
    layout.addWidget(intro)

    form = QFormLayout()
    form.setSpacing(10)

    # Normalize current project so invalid pairs (e.g. coco2·128K) open cleanly
    cur_target, cur_mem = normalize_target_ram(
        project.target, int(project.memory_kb or 64)
    )

    combo_target = QComboBox()
    for key, prof in MACHINE_PROFILES.items():
        combo_target.addItem(str(prof["label"]), key)
    idx = combo_target.findData(cur_target)
    if idx < 0:
        idx = combo_target.findData("coco3")
    combo_target.setCurrentIndex(max(0, idx))
    form.addRow("Machine:", combo_target)

    combo_mem = QComboBox()
    combo_mem.setEditable(False)
    form.addRow("Memory:", combo_mem)

    blurb = QLabel("")
    blurb.setWordWrap(True)
    blurb.setStyleSheet("color: #6b7380; font-size: 11px;")

    def _refill_memory(target_key: str, prefer_kb: int | None = None) -> None:
        prof = MACHINE_PROFILES.get(target_key) or MACHINE_PROFILES["coco3"]
        choices = list(prof["ram_choices"])
        want = prefer_kb if prefer_kb is not None else int(prof["default_ram"])
        combo_mem.blockSignals(True)
        combo_mem.clear()
        for kb in choices:
            combo_mem.addItem(f"{kb}K", int(kb))
        # clamp prefer into choices
        if want not in choices:
            want = int(prof["default_ram"])
        midx = combo_mem.findData(want)
        combo_mem.setCurrentIndex(max(0, midx))
        combo_mem.blockSignals(False)
        blurb.setText(str(prof.get("blurb") or ""))

    _refill_memory(cur_target, cur_mem)

    def _on_target_changed(_i: int = 0) -> None:
        key = str(combo_target.currentData() or "coco3")
        # Keep current selection if still legal; else default for machine
        prev = combo_mem.currentData()
        _refill_memory(key, int(prev) if prev is not None else None)

    combo_target.currentIndexChanged.connect(_on_target_changed)

    dialect_lab = QLabel((project.dialect or "decb").upper() + " (Disk Extended BASIC)")
    dialect_lab.setStyleSheet("color: #9aa3b2;")
    form.addRow("Dialect:", dialect_lab)

    layout.addLayout(form)
    layout.addWidget(blurb)

    hint = QLabel(
        "XRoar needs ROMs in ~/.xroar/roms (bas13+extbas+disk11, or coco3+disk11). "
        "CoCo 3 keywords (HSCREEN, WIDTH, …) require CoCo 3."
    )
    hint.setWordWrap(True)
    hint.setStyleSheet("color: #6b7380; font-size: 11px; margin-top: 8px;")
    layout.addWidget(hint)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return False

    new_target = str(combo_target.currentData() or "coco3")
    new_mem = int(combo_mem.currentData() or cur_mem)
    new_target, new_mem = normalize_target_ram(new_target, new_mem)
    if new_target == project.target and new_mem == project.memory_kb:
        return False

    project.target = new_target
    project.memory_kb = new_mem
    project.save()
    return True
