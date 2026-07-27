"""SFX Lab — design short DAC sound effects and export 6809 player code."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
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
    play_pcm_host,
    render_pcm_preview,
    save_sfx,
    _seed_for,
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
QPushButton#play {
    background-color: #2d6a4f; color: #e8eaed; border-color: #40916c; font-weight: bold;
}
"""


class WaveformView(QWidget):
    """Plot either a cycle table or a full rendered SFX envelope."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._samples: list[int] = []  # signed PCM or 0..63 table scaled
        self._title = ""
        self.setMinimumHeight(120)
        self.setMinimumWidth(320)

    def set_pcm(self, pcm: bytes, title: str = "") -> None:
        """pcm = s16le mono."""
        self._title = title
        self._samples = []
        if pcm and len(pcm) >= 2:
            # downsample for draw
            step = max(1, len(pcm) // 2 // 400)
            for i in range(0, len(pcm) - 1, 2 * step):
                v = int.from_bytes(pcm[i : i + 2], "little", signed=True)
                self._samples.append(v)
        self.update()

    def set_table(self, data: bytes, title: str = "") -> None:
        self._title = title
        self._samples = [((b - 32) * 500) for b in data] if data else []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#12151a"))
        w, h = max(1, self.width()), max(1, self.height())
        pen = QPen(QColor("#3a4150"))
        p.setPen(pen)
        mid = h // 2
        p.drawLine(0, mid, w, mid)
        if self._title:
            p.setPen(QColor("#9aa3b2"))
            p.drawText(8, 14, self._title)
        if len(self._samples) < 2:
            p.setPen(QColor("#6b7380"))
            p.drawText(8, mid, "(no waveform)")
            p.end()
            return
        pen = QPen(QColor("#e09a40"))
        pen.setWidth(1)
        p.setPen(pen)
        n = len(self._samples)
        peak = max(1, max(abs(s) for s in self._samples))
        prev = None
        for i, s in enumerate(self._samples):
            x = int(i * (w - 1) / max(1, n - 1))
            y = mid - int(s * (h // 2 - 4) / peak)
            y = max(1, min(h - 2, y))
            if prev is not None:
                p.drawLine(prev[0], prev[1], x, y)
            prev = (x, y)
        p.end()


class SoundDialog(QDialog):
    """Author SFX patches, preview on host speakers, export ASM."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        project_root: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Sound / SFX Lab")
        self.setMinimumSize(780, 520)
        self.setStyleSheet(_DIALOG_STYLE)
        self._root = project_root
        self._patches: list[SfxPatch] = []
        self._current: SfxPatch | None = None
        self._filling = False
        self._status = QLabel("")
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
            f"Project: {self._root}"
            if self._root
            else "No project open — open a project to save under src/sfx/."
        )
        path_lab.setWordWrap(True)
        root.addWidget(path_lab)

        body = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("Effects (select to edit / preview)"))
        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._on_select)
        left.addWidget(self.list, stretch=1)
        row = QHBoxLayout()
        b_new = QPushButton("New")
        b_new.clicked.connect(self._new_patch)
        b_del = QPushButton("Delete")
        b_del.clicked.connect(self._delete_patch)
        b_play = QPushButton("▶ Preview")
        b_play.setObjectName("play")
        b_play.setToolTip("Play on this computer’s speakers (no XRoar)")
        b_play.clicked.connect(self._preview)
        row.addWidget(b_new)
        row.addWidget(b_del)
        row.addWidget(b_play)
        left.addLayout(row)
        body.addLayout(left, stretch=1)

        right = QVBoxLayout()
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.wave_combo = QComboBox()
        for w in WAVE_KINDS:
            if w != "custom":
                self.wave_combo.addItem(w)
        self.wave_combo.setToolTip(
            "sine/square/saw = tones; noise = static; whoosh = breathy (missile shoo)"
        )
        self.pitch_spin = QSpinBox()
        self.pitch_spin.setRange(1, 255)
        self.pitch_spin.setToolTip("Phase step — higher = higher pitch (f ≈ Fs×pitch/256)")
        self.pend_spin = QSpinBox()
        self.pend_spin.setRange(1, 255)
        self.pend_spin.setToolTip("Pitch slides toward this over the effect")
        self.len_spin = QSpinBox()
        self.len_spin.setRange(16, 12000)
        self.vol_spin = QSpinBox()
        self.vol_spin.setRange(0, 63)
        self.vend_spin = QSpinBox()
        self.vend_spin.setRange(0, 63)
        self.vend_spin.setToolTip("Volume fades toward this (use low end for whoosh/decay)")
        self.duty_spin = QDoubleSpinBox()
        self.duty_spin.setRange(0.05, 0.95)
        self.duty_spin.setSingleStep(0.05)
        form.addRow("Name", self.name_edit)
        form.addRow("Wave", self.wave_combo)
        form.addRow("Pitch", self.pitch_spin)
        form.addRow("Pitch end", self.pend_spin)
        form.addRow("Length (samples)", self.len_spin)
        form.addRow("Volume start", self.vol_spin)
        form.addRow("Volume end", self.vend_spin)
        form.addRow("Duty (square)", self.duty_spin)
        right.addLayout(form)

        self.wave_view = WaveformView()
        right.addWidget(self.wave_view)
        self.cycle_lab = QLabel("Cycle table:")
        right.addWidget(self.cycle_lab)
        self.cycle_view = WaveformView()
        self.cycle_view.setMinimumHeight(64)
        right.addWidget(self.cycle_view)

        for w in (
            self.name_edit,
            self.wave_combo,
            self.pitch_spin,
            self.pend_spin,
            self.len_spin,
            self.vol_spin,
            self.vend_spin,
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
        self._status.setWordWrap(True)
        right.addWidget(self._status)
        hint = QLabel(
            "▶ Preview simulates the same PlaySfx loop as the CoCo (phase, volume steps, LFSR). "
            "Export → Build Disk for XRoar/hardware."
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
        self.list.blockSignals(True)
        self.list.clear()
        sdir = self._sfx_dir()
        if sdir and sdir.is_dir():
            self._patches = list_sfx_dir(sdir)
        else:
            self._patches = []
        for p in self._patches:
            self.list.addItem(f"{p.id}: {p.summary()}")
        self.list.blockSignals(False)
        if self._patches:
            self.list.setCurrentRow(0)
        else:
            self._current = None
            self._update_plot()

    def _on_select(self, row: int) -> None:
        if row < 0 or row >= len(self._patches):
            self._current = None
            return
        self._current = self._patches[row]
        self._fill_form(self._current)

    def _fill_form(self, p: SfxPatch) -> None:
        self._filling = True
        self.name_edit.setText(p.name)
        idx = self.wave_combo.findText(p.wave)
        self.wave_combo.setCurrentIndex(max(0, idx))
        self.pitch_spin.setValue(p.pitch)
        self.pend_spin.setValue(p.pitch_end)
        self.len_spin.setValue(p.length)
        self.vol_spin.setValue(p.volume)
        self.vend_spin.setValue(p.volume_end)
        self.duty_spin.setValue(p.duty)
        self._filling = False
        self._update_plot()

    def _read_form(self) -> SfxPatch:
        base = self._current or SfxPatch()
        base.name = self.name_edit.text().strip() or "sfx"
        base.wave = self.wave_combo.currentText()
        base.pitch = self.pitch_spin.value()
        base.pitch_end = self.pend_spin.value()
        base.length = self.len_spin.value()
        base.volume = self.vol_spin.value()
        base.volume_end = self.vend_spin.value()
        base.duty = self.duty_spin.value()
        return base.clamp()

    def _on_form_changed(self, *_args) -> None:
        if self._filling:
            return
        self._update_plot()
        # live-update list label for current
        row = self.list.currentRow()
        if 0 <= row < len(self._patches):
            p = self._read_form()
            p.id = row
            self.list.item(row).setText(f"{p.id}: {p.summary()}")

    def _update_plot(self) -> None:
        p = self._read_form()
        # Full rendered SFX (what you'll hear)
        pcm = render_pcm_preview(p)
        self.wave_view.set_pcm(pcm, title=f"Preview: {p.summary()}")
        # One cycle of the wavetable (shape)
        t = generate_table(
            p.wave,
            volume=p.volume,
            duty=p.duty,
            custom=p.table,
            seed=_seed_for(p),
        )
        self.cycle_view.set_table(t, title=f"Wavetable cycle ({p.wave})")

    def _preview(self) -> None:
        p = self._read_form()
        # Cap preview length so UI stays responsive
        if p.length > 8000:
            p = SfxPatch(**{**p.__dict__, "length": 8000}).clamp()
        pcm = render_pcm_preview(p)
        msg = play_pcm_host(pcm)
        self._status.setText(msg)

    def _new_patch(self) -> None:
        n = len(self._patches)
        p = SfxPatch(
            name=f"sfx{n}",
            id=n,
            wave="square",
            pitch=40,
            pitch_end=40,
            length=2000,
            volume=48,
            volume_end=48,
        )
        self._patches.append(p)
        self.list.addItem(f"{p.id}: {p.summary()}")
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
            QMessageBox.information(
                self, "SFX Lab", "Open a project to save patches under src/sfx/."
            )
            return
        sdir.mkdir(parents=True, exist_ok=True)
        if self._current and self._current.name != p.name:
            old = sdir / f"{self._current.name}.sfx.json"
            if old.is_file():
                old.unlink()
        row = self.list.currentRow()
        if row >= 0:
            p.id = row
        save_sfx(sdir / f"{p.name}.sfx.json", p)
        self._reload_list()
        for i, q in enumerate(self._patches):
            if q.name == p.name:
                self.list.setCurrentRow(i)
                break
        self._status.setText(f"Saved {p.name}.sfx.json")

    def _export(self) -> None:
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
        self._status.setText(f"Exported {names} — Build Disk for XRoar")
        QMessageBox.information(
            self,
            "Exported",
            f"Wrote {names}\n\n"
            f"Use ▶ Preview for PC speakers.\n"
            f"Build Disk → Run in XRoar for CoCo hardware path.\n"
            f"BASIC: CLEAR200,&H3F00 : AUDIO ON : LOADM\"SFX\":EXEC",
        )
