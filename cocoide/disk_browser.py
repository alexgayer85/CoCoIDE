"""Dialog: browse any DECB .dsk, import files, create project from disk."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from cocoide.dialogs import ensure_dir, get_existing_directory, get_open_file_name
from cocoide.disk_import import (
    DiskFile,
    copy_disk_into_project,
    create_project_around_imports,
    create_project_from_disk,
    import_files_to_directory,
    list_disk_files,
)
from cocoide.project import Project
from cocoide.tools import ToolPaths


class DiskBrowserDialog(QDialog):
    """Browse an external (or any) .dsk image."""

    # Emitted as soon as imports or a project succeed (parent can open files immediately)
    project_ready = Signal(object)  # Project
    files_imported = Signal(list)  # list[Path]

    def __init__(
        self,
        tools: ToolPaths,
        parent=None,
        *,
        project: Project | None = None,
        initial_disk: Path | None = None,
        prefer_new_project: bool = False,
    ) -> None:
        super().__init__(parent)
        self.tools = tools
        self.project = project
        self.disk_path: Path | None = initial_disk
        self.files: list[DiskFile] = []
        self.created_project: Project | None = None
        self.imported_paths: list[Path] = []
        self.last_import_dir: Path | None = None
        self.prefer_new_project = prefer_new_project
        self._file_by_row: dict[int, DiskFile] = {}

        self.setWindowTitle(
            "New project from disk" if prefer_new_project else "Disk image browser"
        )
        self.resize(580, 520)
        self._build_ui()
        if initial_disk:
            self._load_disk(initial_disk)
        elif prefer_new_project:
            # Nudge user to pick a disk first
            self.meta.setText("Open a .dsk image, then click “New project from disk…”.")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        self.path_label = QLabel("No disk open — click “Open .dsk…”")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #9aa3b2;")
        row.addWidget(self.path_label, stretch=1)
        btn_open = QPushButton("Open .dsk…")
        btn_open.clicked.connect(self._choose_disk)
        row.addWidget(btn_open)
        layout.addLayout(row)

        layout.addWidget(QLabel("Files on disk (select rows to import)"))
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list)

        self.meta = QLabel("")
        self.meta.setStyleSheet("color: #6b7380; font-size: 11px;")
        self.meta.setWordWrap(True)
        layout.addWidget(self.meta)

        opts = QVBoxLayout()
        self.chk_detok = QCheckBox(
            "Detokenize tokenized BASIC only (0xFF header → ASCII listing)"
        )
        self.chk_detok.setChecked(True)
        self.chk_detok.setToolTip(
            "Only applies to real tokenized .BAS programs.\n"
            "ASCII data, .DAT, .BIN, etc. are always copied as-is.\n"
            "Never renames .DAT → .bas."
        )
        self.chk_force_raw = QCheckBox("Force raw copy for everything (no detokenize)")
        self.chk_force_raw.setChecked(False)
        self.chk_force_raw.setToolTip(
            "Copy every file byte-for-byte from the disk image.\n"
            "Use if a BASIC program should stay tokenized."
        )
        self.chk_disasm = QCheckBox(
            "Disassemble .BIN / ML to .asm (best-effort 6809)"
        )
        self.chk_disasm.setChecked(True)
        self.chk_disasm.setToolTip(
            "After importing machine-language files, also write a .asm listing.\n"
            "Built-in disassembler (or f9dasm if installed).\n"
            "Expect to clean up before re-assembling with lwasm."
        )
        opts.addWidget(self.chk_detok)
        opts.addWidget(self.chk_force_raw)
        opts.addWidget(self.chk_disasm)
        layout.addLayout(opts)

        # Primary action first when creating a project
        actions2 = QHBoxLayout()
        self.btn_new_proj = QPushButton("New project from disk…")
        self.btn_new_proj.setObjectName("primaryButton")
        self.btn_new_proj.setToolTip(
            "Create project.cocoide, copy disk, import BASIC into src/imported/, open in IDE"
        )
        self.btn_new_proj.clicked.connect(self._new_project_from_disk)
        self.btn_use_project = QPushButton("Use as project disk")
        self.btn_use_project.setToolTip(
            "Copy this image over the current project's build/work.dsk"
        )
        self.btn_use_project.clicked.connect(self._use_as_project_disk)
        if self.prefer_new_project:
            actions2.addWidget(self.btn_new_proj)
            actions2.addWidget(self.btn_use_project)
        else:
            actions2.addWidget(self.btn_use_project)
            actions2.addWidget(self.btn_new_proj)
        layout.addLayout(actions2)

        actions = QHBoxLayout()
        self.btn_import_sel = QPushButton("Import selected…")
        self.btn_import_sel.clicked.connect(self._import_selected)
        self.btn_import_bas = QPushButton("Import all BASIC…")
        self.btn_import_bas.clicked.connect(self._import_all_basic)
        self.btn_import_all = QPushButton("Import all files…")
        self.btn_import_all.clicked.connect(self._import_all)
        actions.addWidget(self.btn_import_sel)
        actions.addWidget(self.btn_import_bas)
        actions.addWidget(self.btn_import_all)
        layout.addLayout(actions)

        if not self.project:
            self.btn_use_project.setEnabled(False)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn:
            close_btn.clicked.connect(self.accept)
        buttons.rejected.connect(self.accept)  # treat close as done; keep results
        layout.addWidget(buttons)

        self._set_actions_enabled(False)

    def _set_actions_enabled(self, on: bool) -> None:
        for b in (
            self.btn_import_sel,
            self.btn_import_bas,
            self.btn_import_all,
            self.btn_new_proj,
        ):
            b.setEnabled(on)
        if self.project:
            self.btn_use_project.setEnabled(on)

    def _choose_disk(self) -> None:
        start = (
            str(self.project.root)
            if self.project and self.project.root
            else str(Path.home())
        )
        path, _ = get_open_file_name(
            self,
            "Open DECB disk image",
            start,
            "Disk images (*.dsk *.DSK);;All (*.*)",
        )
        if path:
            self._load_disk(Path(path))

    def _load_disk(self, disk: Path) -> None:
        self.tools.resolve()
        disk = disk.expanduser().resolve()
        self.disk_path = disk
        self.path_label.setText(str(disk))
        self.files, raw = list_disk_files(self.tools, disk)
        self.list.clear()
        self._file_by_row.clear()
        if not self.files:
            self.meta.setText(
                "No files found (empty disk, wrong format, or decb could not read it).\n"
                f"Raw output: {(raw or '')[:200]}"
            )
            self._set_actions_enabled(False)
            return
        for i, f in enumerate(self.files):
            # Store index — UserRole + custom objects is unreliable across PySide
            label = f"{f.name:12}  type={f.type or '?'}  {f.raw}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.list.addItem(item)
            self._file_by_row[i] = f
        bas_n = sum(1 for f in self.files if f.is_basic)
        self.meta.setText(
            f"{len(self.files)} file(s), {bas_n} BASIC — "
            f"use “New project from disk…” to open in CoCoIDE, or Import to a folder."
        )
        self._set_actions_enabled(True)
        if bas_n:
            self.list.selectAll()

    def _selected_files(self) -> list[DiskFile]:
        out: list[DiskFile] = []
        for item in self.list.selectedItems():
            idx = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(idx, int) and idx in self._file_by_row:
                out.append(self._file_by_row[idx])
        return out

    def _default_import_dir(self) -> Path:
        if self.project and self.project.root:
            d = self.project.root / "src" / "imported"
            d.mkdir(parents=True, exist_ok=True)
            return d
        # No project: suggest a new folder next to the disk
        if self.disk_path:
            return self.disk_path.parent / f"{self.disk_path.stem}_import"
        return Path.home()

    def _pick_dest_dir(self, title: str) -> Path | None:
        start = ensure_dir(self._default_import_dir())
        path = get_existing_directory(self, title, start)
        return Path(path) if path else None

    def _import_selected(self) -> None:
        if not self.disk_path:
            return
        files = self._selected_files()
        if not files:
            QMessageBox.information(
                self, "Import", "Select one or more files in the list first."
            )
            return
        dest = self._pick_dest_dir("Import selected files into folder")
        if not dest:
            return
        self._run_import(files, dest)

    def _import_all_basic(self) -> None:
        if not self.disk_path:
            return
        files = [f for f in self.files if f.is_basic]
        if not files:
            QMessageBox.information(self, "Import", "No BASIC files on this disk.")
            return
        dest = self._pick_dest_dir("Import BASIC into folder")
        if not dest:
            return
        self._run_import(files, dest)

    def _import_all(self) -> None:
        if not self.disk_path:
            return
        if not self.files:
            QMessageBox.information(self, "Import", "Disk is empty.")
            return
        dest = self._pick_dest_dir("Import all files into folder")
        if not dest:
            return
        self._run_import(self.files, dest)

    def _run_import(self, files: list[DiskFile], dest: Path) -> None:
        assert self.disk_path
        dest = dest.expanduser().resolve()
        dest.mkdir(parents=True, exist_ok=True)
        res = import_files_to_directory(
            self.tools,
            self.disk_path,
            files,
            dest,
            basic_as_ascii=self.chk_detok.isChecked(),
            force_raw=self.chk_force_raw.isChecked(),
            disassemble_bin=self.chk_disasm.isChecked()
            and not self.chk_force_raw.isChecked(),
        )
        self.imported_paths.extend(res.paths)
        self.last_import_dir = dest
        self.files_imported.emit(list(res.paths))

        msg = "\n".join(res.messages) or "Done"
        msg += f"\n\nFolder:\n{dest}"

        if not res.ok:
            QMessageBox.warning(self, "Import finished with errors", msg)
            return

        # Always offer next step — this was the missing UX
        if self.project and self.project.root:
            # Prefer project-relative imports
            try:
                rel = dest.relative_to(self.project.root.resolve())
                msg += f"\n\n(Under project: {rel})"
            except ValueError:
                pass
            QMessageBox.information(
                self,
                "Import complete",
                msg
                + "\n\nFiles will open in the editor when you close this dialog "
                "(or were opened if already notified).",
            )
            return

        # No project open — offer to create one
        box = QMessageBox(self)
        box.setWindowTitle("Import complete")
        box.setText(
            msg
            + "\n\nNo CoCoIDE project is open.\n"
            "Create a project from these files so they appear in the IDE?"
        )
        btn_proj = box.addButton(
            "Create project & open", QMessageBox.ButtonRole.AcceptRole
        )
        box.addButton("Just keep files on disk", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() == btn_proj:
            self._create_project_from_import_dir(dest)

    def _create_project_from_import_dir(self, dest: Path) -> None:
        # If user imported to flat folder, use it as project root
        proj, res = create_project_around_imports(
            dest,
            source_disk=self.disk_path,
            name=dest.name,
        )
        if not proj:
            QMessageBox.warning(self, "Could not create project", "\n".join(res.messages))
            return
        self.created_project = proj
        self.project_ready.emit(proj)
        QMessageBox.information(
            self,
            "Project created",
            "\n".join(res.messages)
            + "\n\nThe project will open in CoCoIDE when you close this dialog.",
        )
        self.accept()

    def _use_as_project_disk(self) -> None:
        if not self.disk_path or not self.project:
            return
        if self.project.disk_path and self.project.disk_path.exists():
            r = QMessageBox.question(
                self,
                "Replace project disk",
                f"Replace the project disk image with a copy of\n{self.disk_path.name}?\n\n"
                "The previous project .dsk will be overwritten.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r != QMessageBox.StandardButton.Yes:
                return
        res = copy_disk_into_project(self.disk_path, self.project, replace=True)
        if res.ok:
            QMessageBox.information(self, "Project disk", "\n".join(res.messages))
            self.accept()
        else:
            QMessageBox.warning(self, "Project disk", "\n".join(res.messages))

    def _new_project_from_disk(self) -> None:
        if not self.disk_path:
            QMessageBox.information(
                self, "New project", "Open a .dsk image first (Open .dsk…)."
            )
            return

        dest = get_existing_directory(
            self,
            "Create new project in folder (empty folder recommended)",
            str(self.disk_path.parent),
        )
        if not dest:
            return
        root = Path(dest).expanduser().resolve()

        # Always use a dedicated subfolder if the chosen dir is not empty
        # (unless it already is a CoCoIDE project we can overwrite carefully)
        if (root / "project.cocoide").exists():
            r = QMessageBox.question(
                self,
                "Project exists",
                f"{root / 'project.cocoide'} already exists.\n\n"
                "Replace this project from the disk image?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r != QMessageBox.StandardButton.Yes:
                return
        elif any(root.iterdir()):
            sub = root / self.disk_path.stem
            r = QMessageBox.question(
                self,
                "New project",
                f"Folder is not empty.\n\nCreate project in:\n{sub}\n\n?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r == QMessageBox.StandardButton.Yes:
                root = sub
            else:
                QMessageBox.information(
                    self,
                    "New project",
                    "Cancelled. Pick an empty folder, or choose Yes to use a subfolder.",
                )
                return

        bas = [f for f in self.files if f.is_basic]
        entry_name: str | None = None
        if len(bas) > 1:
            pick = QDialog(self)
            pick.setWindowTitle("Entry program")
            pl = QVBoxLayout(pick)
            pl.addWidget(QLabel("Which BASIC file should be the project entry?"))
            combo = QComboBox()
            for f in bas:
                combo.addItem(f.name, f.name)
            pl.addWidget(combo)
            bb = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            bb.accepted.connect(pick.accept)
            bb.rejected.connect(pick.reject)
            pl.addWidget(bb)
            if pick.exec() != QDialog.DialogCode.Accepted:
                return
            entry_name = combo.currentData()

        self.tools.resolve()
        try:
            proj, res = create_project_from_disk(
                self.tools,
                self.disk_path,
                root,
                name=root.name,
                entry_coco_name=entry_name,
                import_all=True,
            )
        except OSError as exc:
            QMessageBox.critical(self, "New project failed", str(exc))
            return

        if not proj:
            QMessageBox.warning(self, "New project failed", "\n".join(res.messages))
            return

        cocoide_path = root / "project.cocoide"
        if not cocoide_path.is_file():
            QMessageBox.critical(
                self,
                "New project failed",
                "Project object created but project.cocoide was not written:\n"
                f"{cocoide_path}\n\n" + "\n".join(res.messages),
            )
            return

        self.created_project = proj
        self.imported_paths.extend(res.paths)
        self.project_ready.emit(proj)
        QMessageBox.information(
            self,
            "Project created",
            "\n".join(res.messages)
            + f"\n\nProject file:\n{cocoide_path}\n"
            "\nPreprocessor is off (classic line-numbered BASIC).\n"
            "Click OK to open the project in the IDE.",
        )
        self.accept()
