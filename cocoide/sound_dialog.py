"""SFX Lab — design short DAC sound effects and export 6809 player code."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cocoide.sound import (
    WAVE_KINDS,
    SfxPatch,
    export_project_sfx,
    generate_table,
    list_sfx_dir,
    save_sfx,
)

_DIALOG_STYLE = """
QDialog { background-color: #1a1d23; color: #e8eaed; }
QLabel { color: #9aa3b2; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QListWidget {
    background-color: #12151a; color: #e8eaed;
    border: 1px solid #3a4150; border-radius: 4px; padding: 4px;
}
QPushButton {
    background-color: #2a2f3a; color: #e8eaed;
    border: 1px solid #3a4150; border-radius: 4px; padding: 6px 12px;
}
QPushButton:hover { background-color: #353b48; }
QPushButton#primary {
    background-color: #c4782a; color: #1a1d23; border-color: #e09a40; font-weight: bold;
}
"""


class WaveformView(QWidget):
    """Simple 256-sample plot (0–63)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._table = bytes(256)
        self.setMinimumHeight(100)
        self.setMinimumWidth(280)

    def set_table(self, data: bytes) -> None:
        self._table = data if data else bytes(256)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#12151a"))
        w, h = self.width(), self.height()
        pen = QPen(QColor("#6b7380"))
        pen.setWidth(1)
        p.setPen(pen)
        mid = h // 2
        p.drawLine(0, mid, w, mid)
        if not self._table:
            return
        pen = QPen(QColor("#e09a40"))
        pen.setWidth(2)
        p.setPen(pen)
        n = len(self._table)
        pts = []
        for i, b in enumerate(self._table):
            x = int(i * (w - 1) / max(1, n - 1))
            y = h - 2 - int(b * (h - 4) / 63)
            pts.append((x, y))
        for i in range(1, len(pts)):
            p.drawLine(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1])
        p.end()


class SoundDialog(QDialog):
    """Author SFX patches and export sfx.asm + sfx_tables.bin."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        project_root: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sound / SFX Lab")
        self.setMinimumSize(720, 480)
        self.setStyleSheet(_DIALOG_STYLE)
        self._root = project_root
        self._patches: list[SfxPatch] = []
        self._current: SfxPatch | None = None
        self._build_ui()
        self._reload_list()

    def _sfx_dir(self) -> Path | None:
        if self._root is None:
            return None
        return self._root / "src" / "sfx"

    def _src_dir(self) -> Path | None:
        if self._root is None:
            return None
        return self._root / "src"

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(10)

        path_lab = QLabel(
            f"Project: {self._root}" if self._root else "No project open — export picks a folder."
        )
        path_lab.setWordWrap(True)
        root.addWidget(path_lab)

        body = QHBoxLayout()
        # list
        left = QVBoxLayout()
        left.addWidget(QLabel("Effects"))
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._on_select)
        left.addWidget(self.list, stretch=1)
        row = QHBoxLayout()
        b_new = QPushButton("New")
        b_new.clicked.connect(self._new_patch)
        b_del = QPushButton("Delete")
        b_del.clicked.connect(self._delete_patch)
        row.addWidget(b_new)
        row.addWidget(b_del)
        left.addLayout(row)
        body.addLayout(left, stretch=1)

        # form
        right = QVBoxLayout()
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.wave_combo = QComboBox()
        for w in WAVE_KINDS:
            if w != "custom":
                self.wave_combo.addItem(w)
        self.pitch_spin = QSpinBox()
        self.pitch_spin.setRange(1, 255)
        self.pend_spin = QSpinBox()
        self.pend_spin.setRange(1, 255)
        self.len_spin = QSpinBox()
        self.len_spin.setRange(16, 8000)
        self.vol_spin = QSpinBox()
        self.vol_spin.setRange(0, 63)
        self.duty_spin = QDoubleSpinBox()
        self.duty_spin.setRange(0.05, 0.95)
        self.duty_spin.setSingleStep(0.05)
        form.addRow("Name", self.name_edit)
        form.addRow("Wave", self.wave_combo)
        form.addRow("Pitch", self.pitch_spin)
        form.addRow("Pitch end (slide)", self.pend_spin)
        form.addRow("Length (ticks)", self.len_spin)
        form.addRow("Volume (0–63)", self.vol_spin)
        form.addRow("Duty (square)", self.duty_spin)
        right.addLayout(form)

        self.wave_view = WaveformView()
        right.addWidget(self.wave_view)
        for w in (
            self.name_edit,
            self.wave_combo,
            self.pitch_spin,
            self.pend_spin,
            self.len_spin,
            self.vol_spin,
            self.duty_spin,
        ):
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(self._on_form_changed)  # type: ignore[attr-defined]
            if hasattr(w, "currentIndexChanged"):
                w.currentIndexChanged.connect(self._on_form_changed)  # type: ignore[attr-defined]
            if hasattr(w, "textChanged"):
                w.textChanged.connect(self._on_form_changed)  # type: ignore[attr-defined]

        btn_row = QHBoxLayout()
        b_save = QPushButton("Save patch")
        b_save.clicked.connect(self._save_current)
        b_export = QPushButton("Export ASM to project")
        b_export.setObjectName("primary")
        b_export.clicked.connect(self._export)
        btn_row.addWidget(b_save)
        btn_row.addWidget(b_export)
        right.addLayout(btn_row)
        hint = QLabel(
            "Export writes src/sfx.asm + src/sfx_tables.bin. "
            "Build Disk to assemble SFX.BIN. Call SoundInit / PlaySfx (A=id)."
        )
        hint.setWordWrap(True)
        right.addWidget(hint)
        body.addLayout(right, stretch=2)
        root.addLayout(body)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn:
            close_btn.clicked.connect(self.accept)
        root.addWidget(buttons)

    def _reload_list(self) -> None:
        self.list.clear()
        sdir = self._sfx_dir()
        if sdir and sdir.is_dir():
            self._patches = list_sfx_dir(sdir)
        else:
            self._patches = []
        for p in self._patches:
            self.list.addItem(f"{p.id}: {p.name} ({p.wave})")
        if self._patches:
            self.list.setCurrentRow(0)
        else:
            self._current = None

    def _on_select(self, row: int) -> None:
        if row < 0 or row >= len(self._patches):
            self._current = None
            return
        self._current = self._patches[row]
        self._fill_form(self._current)

    def _fill_form(self, p: SfxPatch) -> None:
        self.name_edit.setText(p.name)
        idx = self.wave_combo.findText(p.wave)
        self.wave_combo.setCurrentIndex(max(0, idx))
        self.pitch_spin.setValue(p.pitch)
        self.pend_spin.setValue(p.pitch_end)
        self.len_spin.setValue(p.length)
        self.vol_spin.setValue(p.volume)
        self.duty_spin.setValue(p.duty)
        self._update_plot()

    def _read_form(self) -> SfxPatch:
        base = self._current or SfxPatch()
        base.name = self.name_edit.text().strip() or "sfx"
        base.wave = self.wave_combo.currentText()
        base.pitch = self.pitch_spin.value()
        base.pitch_end = self.pend_spin.value()
        base.length = self.len_spin.value()
        base.volume = self.vol_spin.value()
        base.duty = self.duty_spin.value()
        return base.clamp()

    def _on_form_changed(self, *_args) -> None:
        self._update_plot()

    def _update_plot(self) -> None:
        p = self._read_form()
        t = generate_table(p.wave, volume=p.volume, duty=p.duty, custom=p.table)
        self.wave_view.set_table(t)

    def _new_patch(self) -> None:
        n = len(self._patches)
        p = SfxPatch(name=f"sfx{n}", id=n, wave="square", pitch=32, pitch_end=32, length=200, volume=48)
        self._patches.append(p)
        self.list.addItem(f"{p.id}: {p.name} ({p.wave})")
        self.list.setCurrentRow(n)
        self._save_current()

    def _delete_patch(self) -> None:
        row = self.list.currentRow()
        if row < 0 or row >= len(self._patches):
            return
        p = self._patches[row]
        sdir = self._sfx_dir()
        if sdir:
            path = sdir / f"{p.name}.sfx.json"
            if path.is_file():
                path.unlink()
        del self._patches[row]
        self._reload_list()

    def _save_current(self) -> None:
        p = self._read_form()
        sdir = self._sfx_dir()
        if sdir is None:
            QMessageBox.information(self, "SFX Lab", "Open a project to save patches under src/sfx/.")
            return
        sdir.mkdir(parents=True, exist_ok=True)
        # rename file if name changed
        if self._current and self._current.name != p.name:
            old = sdir / f"{self._current.name}.sfx.json"
            if old.is_file():
                old.unlink()
        row = self.list.currentRow()
        if row >= 0:
            p.id = row
        save_sfx(sdir / f"{p.name}.sfx.json", p)
        self._reload_list()
        # reselect by name
        for i, q in enumerate(self._patches):
            if q.name == p.name:
                self.list.setCurrentRow(i)
                break

    def _export(self) -> None:
        # ensure current form saved into list
        if self._patches or self._current is not None:
            try:
                self._save_current()
            except Exception:
                pass
        sdir = self._sfx_dir()
        src = self._src_dir()
        if src is None:
            QMessageBox.information(self, "SFX Lab", "Open a project first.")
            return
        patches = list_sfx_dir(sdir) if sdir else []
        if not patches:
            # use form as single patch
            patches = [self._read_form()]
            patches[0].id = 0
            if sdir:
                sdir.mkdir(parents=True, exist_ok=True)
                save_sfx(sdir / f"{patches[0].name}.sfx.json", patches[0])
        try:
            written = export_project_sfx(src, patches, include_demo_loop=True)
        except Exception as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
            return
        names = ", ".join(p.name for p in written)
        QMessageBox.information(
            self,
            "Exported",
            f"Wrote {names}\n\nBuild Disk to assemble SFX.BIN, then Run in XRoar.\n"
            f"BASIC: CLEAR200,&H3F00 : AUDIO ON : LOADM\"SFX\":EXEC",
        )
