"""Main window — comfortable three-pane layout."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import (
    QAction,
    QFont,
    QKeySequence,
    QCloseEvent,
    QDesktopServices,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cocoide import __version__
from cocoide.build import build_project, disk_listing, ensure_disk, run_project
from cocoide.dialogs import (
    edit_project_settings,
    get_existing_directory,
    get_open_file_name,
    get_save_file_name,
)
from cocoide.diagnostics import Diagnostic
from cocoide.project import PROJECT_FILENAME, Project
from cocoide.tools import (
    ToolPaths,
    decb_copy_to_disk,
    decb_dskini,
    decb_extract,
    decb_kill,
    guess_decb_type,
    host_to_coco_name,
    parse_decb_dir,
    parse_granule_usage,
)


class MainWindow(QMainWindow):
    def __init__(self, project: Project | None = None) -> None:
        super().__init__()
        self.tools = ToolPaths().resolve()
        self.project = project
        self._current_file: Path | None = None
        self._dirty = False
        self._diagnostics: list[Diagnostic] = []

        self.setWindowTitle(self._title())
        self.resize(1180, 720)
        self._build_ui()
        self._apply_project()

    # ── UI construction ──────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_menus()
        self._build_toolbar()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: project tree
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(4, 4, 4, 4)
        left_l.addWidget(self._section_label("Project"))
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemDoubleClicked.connect(self._on_tree_open)
        left_l.addWidget(self.tree)
        splitter.addWidget(left)

        # Center: editor + bottom tabs
        center = QWidget()
        center_l = QVBoxLayout(center)
        center_l.setContentsMargins(4, 4, 4, 4)

        mode_row = QHBoxLayout()
        self.file_label = QLabel("No file open")
        self.file_label.setStyleSheet("color: #9aa3b2;")
        mode_row.addWidget(self.file_label)
        mode_row.addStretch()
        self.view_modern = QPushButton("Modern")
        self.view_coco = QPushButton("CoCo")
        self.view_modern.setCheckable(True)
        self.view_coco.setCheckable(True)
        self.view_modern.setChecked(True)
        self.view_modern.clicked.connect(lambda: self._set_view_mode("modern"))
        self.view_coco.clicked.connect(lambda: self._set_view_mode("coco"))
        mode_row.addWidget(self.view_modern)
        mode_row.addWidget(self.view_coco)
        center_l.addLayout(mode_row)

        center_split = QSplitter(Qt.Orientation.Vertical)
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("editor")
        self.editor.setPlaceholderText("Open or create a project to edit modern BASIC…")
        self.editor.textChanged.connect(self._on_text_changed)
        mono = QFont("Ubuntu Mono")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(11)
        self.editor.setFont(mono)
        center_split.addWidget(self.editor)

        self.bottom = QTabWidget()
        self.problems = QListWidget()
        self.problems.setObjectName("problemsList")
        self.problems.itemDoubleClicked.connect(self._on_problem_activated)
        self.problems.itemClicked.connect(self._on_problem_activated)
        self.build_log = QPlainTextEdit()
        self.build_log.setReadOnly(True)
        self.xroar_log = QPlainTextEdit()
        self.xroar_log.setReadOnly(True)
        self.bottom.addTab(self.problems, "Problems")
        self.bottom.addTab(self.build_log, "Build")
        self.bottom.addTab(self.xroar_log, "XRoar")
        center_split.addWidget(self.bottom)
        center_split.setSizes([480, 160])
        center_l.addWidget(center_split)
        splitter.addWidget(center)

        # Right: disk panel
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(4, 4, 4, 4)
        right_l.addWidget(self._section_label("Disk"))
        self.disk_meta = QLabel("No disk")
        self.disk_meta.setWordWrap(True)
        self.disk_meta.setStyleSheet("color: #9aa3b2; font-size: 11px;")
        right_l.addWidget(self.disk_meta)

        free_row = QHBoxLayout()
        self.disk_free_label = QLabel("Free granules —")
        self.disk_free_label.setStyleSheet("color: #9aa3b2; font-size: 11px;")
        free_row.addWidget(self.disk_free_label)
        free_row.addStretch()
        right_l.addLayout(free_row)

        # Used-space bar (matches UI sketch meter); green→amber by fill level
        self.disk_bar = QProgressBar()
        self.disk_bar.setObjectName("diskBar")
        self.disk_bar.setRange(0, 100)
        self.disk_bar.setValue(0)
        self.disk_bar.setTextVisible(False)
        self.disk_bar.setFixedHeight(10)
        self.disk_bar.setToolTip("Disk space used (granules)")
        right_l.addWidget(self.disk_bar)

        self.disk_list = QListWidget()
        self.disk_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.disk_list.setToolTip("Select a file for Extract / Delete")
        right_l.addWidget(self.disk_list)

        disk_btns = QHBoxLayout()
        for label, slot, tip in (
            ("New", self.disk_new, "Blank project disk"),
            ("Add…", self.disk_add_file, "Add host file to project disk"),
            ("Add cur", self.disk_add_current, "Add open file to project disk"),
            ("Extract", self.disk_extract, "Extract selected from project disk"),
            ("Delete", self.disk_delete, "Delete selected from project disk"),
            ("Mount…", lambda: self.browse_disk_image(), "Browse any .dsk — import or new project"),
            ("↻", self.refresh_disk, "Refresh directory"),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            btn.setToolTip(tip)
            disk_btns.addWidget(btn)
        right_l.addLayout(disk_btns)
        splitter.addWidget(right)

        splitter.setSizes([200, 680, 260])
        self.setCentralWidget(splitter)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_tools = QLabel(self.tools.status_line())
        self.status_pos = QLabel("Ln 1, Col 1")
        self.status_extra = QLabel("")
        sb.addWidget(self.status_tools)
        sb.addWidget(self.status_pos)
        sb.addPermanentWidget(self.status_extra)
        self.editor.cursorPositionChanged.connect(self._update_cursor_pos)

    def _section_label(self, text: str) -> QLabel:
        lab = QLabel(text.upper())
        lab.setStyleSheet(
            "color: #6b7380; font-size: 11px; letter-spacing: 1px; padding: 2px 0;"
        )
        return lab

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        act_new = QAction("New Project…", self)
        act_new.triggered.connect(self.new_project)
        file_menu.addAction(act_new)
        act_from_disk = QAction("New Project from Disk…", self)
        act_from_disk.triggered.connect(lambda: self.browse_disk_image(prefer_new_project=True))
        file_menu.addAction(act_from_disk)
        act_open = QAction("Open Project…", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self.open_project)
        file_menu.addAction(act_open)
        act_save = QAction("Save", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self.save_current)
        file_menu.addAction(act_save)
        act_settings = QAction("Project Settings…", self)
        act_settings.setShortcut("Ctrl+,")
        act_settings.triggered.connect(self.edit_project_settings)
        file_menu.addAction(act_settings)
        file_menu.addSeparator()
        act_browse_dsk = QAction("Browse Disk Image…", self)
        act_browse_dsk.setShortcut("Ctrl+Shift+O")
        act_browse_dsk.triggered.connect(lambda: self.browse_disk_image())
        file_menu.addAction(act_browse_dsk)
        file_menu.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        build_menu = self.menuBar().addMenu("&Build")
        act_build = QAction("Build Disk", self)
        act_build.setShortcut("Ctrl+B")
        act_build.triggered.connect(self.do_build)
        build_menu.addAction(act_build)
        act_run = QAction("Run in XRoar", self)
        act_run.setShortcut("Ctrl+R")
        act_run.triggered.connect(self.do_run)
        build_menu.addAction(act_run)
        build_menu.addSeparator()
        act_asm = QAction("Assemble ASM only", self)
        act_asm.setShortcut("Ctrl+Shift+A")
        act_asm.triggered.connect(self.do_assemble_only)
        build_menu.addAction(act_asm)
        act_disasm = QAction("Disassemble BIN file…", self)
        act_disasm.triggered.connect(self.do_disassemble_bin)
        build_menu.addAction(act_disasm)
        build_menu.addSeparator()
        act_diag = QAction("Run Diagnostics", self)
        act_diag.setShortcut("Ctrl+Shift+D")
        act_diag.triggered.connect(self.do_diagnostics)
        build_menu.addAction(act_diag)

        help_menu = self.menuBar().addMenu("&Help")
        act_guide = QAction("User Guide…", self)
        act_guide.setShortcut(QKeySequence(Qt.Key.Key_F1))
        act_guide.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        act_guide.triggered.connect(self._open_user_guide)
        help_menu.addAction(act_guide)
        # Ensure F1 works even when a child widget has focus
        self.addAction(act_guide)
        act_about = QAction("About CoCoIDE", self)
        act_about.triggered.connect(self._about)
        help_menu.addAction(act_about)
        self._help_dialog: QDialog | None = None

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        btn_open = QPushButton("Open")
        btn_open.clicked.connect(self.open_project)
        tb.addWidget(btn_open)

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_current)
        tb.addWidget(btn_save)

        tb.addSeparator()

        btn_build = QPushButton("Build Disk")
        btn_build.clicked.connect(self.do_build)
        tb.addWidget(btn_build)

        btn_run = QPushButton("▶ Run in XRoar")
        btn_run.setObjectName("primaryButton")
        btn_run.clicked.connect(self.do_run)
        tb.addWidget(btn_run)

        tb.addSeparator()

        self.chk_autorun = QCheckBox("Auto-run")
        self.chk_autorun.setChecked(True)
        self.chk_autorun.setToolTip(
            "When on, XRoar types RUN\"…\" after mount (default on)"
        )
        self.chk_autorun.toggled.connect(self._on_autorun_toggled)
        tb.addWidget(self.chk_autorun)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        self.chip_target = QPushButton("No project")
        self.chip_target.setObjectName("chip")
        self.chip_target.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chip_target.setToolTip(
            "Click to set bootable machine + RAM (CoCo 1/2/3 only) — saved to project.cocoide"
        )
        self.chip_target.setEnabled(False)
        self.chip_target.clicked.connect(self.edit_project_settings)
        tb.addWidget(self.chip_target)
        self.chip_disk = QLabel("—")
        self.chip_disk.setObjectName("chipDisk")
        tb.addWidget(self.chip_disk)

    # ── Project lifecycle ────────────────────────────────────────

    def _title(self) -> str:
        if self.project:
            dirty = " *" if self._dirty else ""
            return f"{self.project.name}{dirty} — CoCoIDE"
        return f"CoCoIDE {__version__}"

    def _apply_project(self) -> None:
        if not self.project:
            self.chip_target.setText("No project")
            self.chip_target.setEnabled(False)
            self.chip_disk.setText("—")
            return
        self.chk_autorun.setChecked(self.project.auto_run)
        self.chip_target.setText(self.project.target_chip)
        self.chip_target.setEnabled(True)
        disk_name = Path(self.project.disk_image).name
        self.chip_disk.setText(disk_name)
        self.setWindowTitle(self._title())
        self._rebuild_tree()
        # Open entry file
        if self.project.entry_path and self.project.entry_path.is_file():
            self._open_file(self.project.entry_path)
        self.refresh_disk()
        self.status_tools.setText(self.tools.status_line())

    def edit_project_settings(self) -> None:
        """Change machine target and RAM (toolbar chip or File → Project Settings)."""
        if not self.project:
            QMessageBox.information(
                self,
                "No project",
                "Open or create a project first, then set the machine target.",
            )
            return
        try:
            changed = edit_project_settings(self, self.project)
        except OSError as exc:
            QMessageBox.critical(self, "Project settings", str(exc))
            return
        if not changed:
            return
        self.chip_target.setText(self.project.target_chip)
        self.status_extra.setText(
            f"Target: {self.project.target_chip} · saved project.cocoide"
        )
        # Refresh tree so project.cocoide mtime/view is current
        self._rebuild_tree()

    def _rebuild_tree(self) -> None:
        self.tree.clear()
        if not self.project or not self.project.root:
            return
        root = self.project.root
        top = QTreeWidgetItem([root.name])
        top.setData(0, Qt.ItemDataRole.UserRole, str(root))
        self.tree.addTopLevelItem(top)

        def add_dir(parent: QTreeWidgetItem, path: Path) -> None:
            try:
                entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except OSError:
                return
            for p in entries:
                if p.name.startswith(".") or p.name == "__pycache__":
                    continue
                item = QTreeWidgetItem([p.name])
                item.setData(0, Qt.ItemDataRole.UserRole, str(p))
                parent.addChild(item)
                if p.is_dir():
                    add_dir(item, p)

        add_dir(top, root)
        top.setExpanded(True)
        for i in range(top.childCount()):
            ch = top.child(i)
            if ch and ch.text(0) in ("src", "build"):
                ch.setExpanded(True)

    def new_project(self) -> None:
        path = get_existing_directory(self, "Create project in folder")
        if not path:
            return
        root = Path(path)
        name = root.name or "untitled"
        # If folder empty-ish, use it; else make subfolder
        if any(root.iterdir()) and not (root / PROJECT_FILENAME).exists():
            root = root / name
        try:
            proj = Project.create_new(root, name)
        except OSError as exc:
            QMessageBox.critical(self, "New project", str(exc))
            return
        # Create disk if possible
        from cocoide.build import ensure_disk

        rep = ensure_disk(self.tools, proj)
        if rep.messages:
            self._log_build(rep.messages)
        self.project = proj
        self._apply_project()

    def browse_disk_image(self, prefer_new_project: bool = False) -> None:
        """Browse any .dsk: import files, mount as project disk, or new project."""
        from cocoide.disk_browser import DiskBrowserDialog

        self.tools.resolve()
        if not self.tools.decb:
            QMessageBox.warning(
                self,
                "decb missing",
                "Toolshed `decb` is required to browse disk images.\n\n"
                "Install Toolshed on PATH, place decb in tools/ next to CoCoIDE, "
                "or set COCOIDE_DECB.",
            )
            return
        # Prefer not preloading project disk when creating a brand-new project
        initial = None
        if (
            not prefer_new_project
            and self.project
            and self.project.disk_path
            and self.project.disk_path.is_file()
        ):
            initial = self.project.disk_path

        dlg = DiskBrowserDialog(
            self.tools,
            self,
            project=self.project,
            initial_disk=initial,
            prefer_new_project=prefer_new_project,
        )
        dlg.project_ready.connect(self._on_disk_browser_project)
        dlg.files_imported.connect(self._on_disk_browser_imports)

        dlg.exec()

        # Always apply results (even if user closed the window after import)
        if dlg.created_project:
            self._load_project_object(dlg.created_project)
        elif dlg.imported_paths:
            self._open_imported_paths(dlg.imported_paths)
            if self.project:
                self.refresh_disk()
                self._rebuild_tree()
        elif self.project:
            self.refresh_disk()
            self._rebuild_tree()
        self.status_extra.setText("Disk browser closed")

    def _on_disk_browser_project(self, proj: Project) -> None:
        self._load_project_object(proj)

    def _on_disk_browser_imports(self, paths: list) -> None:
        self._open_imported_paths(paths)
        if self.project:
            self._rebuild_tree()

    def _load_project_object(self, proj: Project) -> None:
        self.project = proj
        self._apply_project()
        self._log_build(
            [
                f"Opened project: {proj.root}",
                f"Entry: {proj.entry}",
                f"project.cocoide: {proj.root / PROJECT_FILENAME if proj.root else '?'}",
            ]
        )
        if proj.entry_path and proj.entry_path.is_file():
            self._open_file(proj.entry_path)
        self.status_extra.setText(f"Project: {proj.name}")

    def _open_imported_paths(self, paths: list) -> None:
        path_list = [Path(p) for p in paths if p]
        for p in path_list:
            self._log_build([f"Imported: {p}"])
        bas = next(
            (p for p in path_list if p.suffix.lower() in (".bas", ".mbas") and p.is_file()),
            None,
        )
        if bas:
            self._open_file(bas)
        elif path_list and path_list[0].is_file():
            self._open_file(path_list[0])

    def open_project(self) -> None:
        path, _ = get_open_file_name(
            self,
            "Open project.cocoide",
            str(Path.home()),
            "CoCoIDE project (project.cocoide);;All (*.*)",
        )
        if not path:
            return
        p = Path(path)
        root = p.parent if p.name == PROJECT_FILENAME else p
        if (root / PROJECT_FILENAME).is_file():
            root = root
        elif p.is_file():
            root = p.parent
        try:
            self.project = Project.load(root)
        except (OSError, ValueError, KeyError) as exc:
            QMessageBox.critical(self, "Open project", str(exc))
            return
        self._apply_project()

    def _on_tree_open(self, item: QTreeWidgetItem, _col: int) -> None:
        path_s = item.data(0, Qt.ItemDataRole.UserRole)
        if not path_s:
            return
        path = Path(path_s)
        if path.is_file():
            self._open_file(path)

    def _open_file(self, path: Path) -> None:
        if self._dirty and not self._confirm_discard():
            return
        # Machine code is not text — offer disassembly instead of UTF-8 blow-up
        if path.suffix.lower() in (".bin", ".raw", ".rom"):
            r = QMessageBox.question(
                self,
                "Binary file",
                f"{path.name} looks like machine code, not text.\n\n"
                "Disassemble to 6809 assembly (.asm) for viewing/editing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r == QMessageBox.StandardButton.Yes:
                self._disassemble_path(path)
            return
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            QMessageBox.warning(
                self,
                "Open file",
                f"Cannot open {path.name} as text (not UTF-8).\n"
                "For .BIN files use Build → Disassemble BIN file…",
            )
            return
        except OSError as exc:
            QMessageBox.warning(self, "Open file", str(exc))
            return
        self._current_file = path
        # build/*.bas artifacts are read-only in the editor
        is_artifact = "build" in path.parts and path.suffix.lower() == ".bas"
        self.editor.blockSignals(True)
        self.editor.setPlainText(text)
        self.editor.blockSignals(False)
        self.editor.setReadOnly(is_artifact)
        self._dirty = False
        if self.project and self.project.root:
            try:
                label = str(path.relative_to(self.project.root))
            except ValueError:
                label = str(path)
        else:
            label = str(path)
        if is_artifact:
            label += "  [read-only artifact]"
        self.file_label.setText(label)
        if is_artifact:
            self.view_coco.setChecked(True)
            self.view_modern.setChecked(False)
        else:
            self.view_modern.setChecked(True)
            self.view_coco.setChecked(False)
        self.setWindowTitle(self._title())

    def _set_view_mode(self, mode: str) -> None:
        if not self.project or not self.project.root:
            return
        if mode == "modern":
            self.view_modern.setChecked(True)
            self.view_coco.setChecked(False)
            entry = self.project.entry_path
            if entry and entry.is_file():
                self._open_file(entry)
        else:
            self.view_coco.setChecked(True)
            self.view_modern.setChecked(False)
            art = self.project.root / "build" / (Path(self.project.entry).stem + ".bas")
            if art.is_file():
                self._open_file(art)
            else:
                self.problems.setPlainText(
                    "No CoCo artifact yet — run Build Disk to generate the read-only output."
                )
                self.bottom.setCurrentWidget(self.problems)

    def save_current(self) -> None:
        if not self._current_file or self.editor.isReadOnly():
            return
        try:
            self._current_file.write_text(self.editor.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Save", str(exc))
            return
        self._dirty = False
        self.setWindowTitle(self._title())
        self.status_extra.setText("Saved")
        self._rebuild_tree()

    def _on_text_changed(self) -> None:
        if self.editor.isReadOnly():
            return
        self._dirty = True
        self.setWindowTitle(self._title())

    def _on_autorun_toggled(self, checked: bool) -> None:
        if self.project:
            self.project.auto_run = checked
            try:
                self.project.save()
            except OSError:
                pass

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        r = QMessageBox.question(
            self,
            "Unsaved changes",
            "Discard unsaved changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return r == QMessageBox.StandardButton.Yes

    def _update_cursor_pos(self) -> None:
        c = self.editor.textCursor()
        self.status_pos.setText(f"Ln {c.blockNumber() + 1}, Col {c.columnNumber() + 1}")

    # ── Build / Run ──────────────────────────────────────────────

    def do_build(self) -> None:
        if not self.project:
            QMessageBox.information(self, "Build", "Open or create a project first.")
            return
        if self._dirty:
            self.save_current()
        self.tools.resolve()
        report = build_project(self.tools, self.project)
        self._log_build(report.messages)
        if report.var_map:
            self._log_build(
                ["Variable map:"] + [f"  {k} → {v}" for k, v in report.var_map.items()]
            )
        self._show_diagnostics(report.diagnostics)
        errs = sum(1 for d in report.diagnostics if d.severity == "error")
        warns = sum(1 for d in report.diagnostics if d.severity == "warning")
        if errs or warns:
            self.bottom.setCurrentWidget(self.problems)
        else:
            self.bottom.setCurrentWidget(self.build_log)
        self.refresh_disk()
        self._rebuild_tree()
        self.status_extra.setText(
            f"Build OK · {errs} err · {warns} warn"
            if report.ok
            else "Build failed"
        )
        if not report.ok:
            QMessageBox.warning(self, "Build failed", "\n".join(report.messages[-5:]))

    def do_diagnostics(self) -> None:
        """Build (to refresh artifact) and focus Problems."""
        if not self.project:
            QMessageBox.information(self, "Diagnostics", "Open or create a project first.")
            return
        self.do_build()
        self.bottom.setCurrentWidget(self.problems)

    def do_assemble_only(self) -> None:
        if not self.project or not self.project.root:
            QMessageBox.information(self, "Assemble", "Open a project first.")
            return
        self.tools.resolve()
        from cocoide.asm import assemble_project, copy_bins_to_disk
        from cocoide.build import ensure_disk

        asm_result, units = assemble_project(
            self.tools, self.project.root, self.project.asm_sources or None
        )
        self._log_build(asm_result.messages)
        if not units:
            QMessageBox.information(
                self,
                "Assemble",
                "No .asm sources found under src/.\n"
                "Add e.g. src/sprites.asm and Build again.",
            )
            return
        if not asm_result.ok:
            QMessageBox.warning(self, "Assemble failed", "\n".join(asm_result.messages[-8:]))
            self.bottom.setCurrentWidget(self.build_log)
            return
        disk_rep = ensure_disk(self.tools, self.project)
        self._log_build(disk_rep.messages)
        if disk_rep.ok and self.project.disk_path:
            copy_ml = copy_bins_to_disk(self.tools, self.project.disk_path, units)
            self._log_build(copy_ml.messages)
            self.refresh_disk()
        self._rebuild_tree()
        self.bottom.setCurrentWidget(self.build_log)
        self.status_extra.setText("ASM assembled")

    def do_disassemble_bin(self) -> None:
        start = (
            str(self.project.root)
            if self.project and self.project.root
            else str(Path.home())
        )
        # Prefer project build/ if it has .bin files
        if self.project and self.project.root:
            build_dir = self.project.root / "build"
            if build_dir.is_dir() and any(build_dir.glob("*.bin")):
                start = str(build_dir)
        path, _ = get_open_file_name(
            self,
            "Disassemble CoCo BIN / raw 6809 binary",
            start,
            "Binaries (*.bin *.BIN *.raw);;All (*.*)",
        )
        if not path:
            return
        self._disassemble_path(Path(path))

    def _disassemble_path(self, src: Path) -> None:
        """Disassemble a binary and open the resulting .asm in the editor."""
        if not src.is_file():
            QMessageBox.warning(self, "Disassemble", f"File not found:\n{src}")
            return
        out = src.with_suffix(".asm")
        if self.project and self.project.root:
            out = self.project.root / "src" / "imported" / (src.stem + ".asm")
            try:
                out.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                QMessageBox.warning(self, "Disassemble", str(exc))
                return
        try:
            from cocoide.disasm6809 import disassemble_bin_file

            _text, msg = disassemble_bin_file(src, out)
        except Exception as exc:  # noqa: BLE001 — show any failure in UI
            self._log_build([f"Disassemble failed: {exc}"])
            QMessageBox.warning(
                self,
                "Disassemble failed",
                f"{exc}\n\nSource: {src}\nOutput: {out}",
            )
            return
        self._log_build([msg, f"Wrote {out}"])
        self._rebuild_tree()
        # Open as text (not via binary branch)
        try:
            text = out.read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Disassemble", str(exc))
            return
        self._current_file = out
        self.editor.blockSignals(True)
        self.editor.setPlainText(text)
        self.editor.blockSignals(False)
        self.editor.setReadOnly(False)
        self._dirty = False
        if self.project and self.project.root:
            try:
                label = str(out.relative_to(self.project.root))
            except ValueError:
                label = str(out)
        else:
            label = str(out)
        self.file_label.setText(label + "  [disassembly]")
        self.view_modern.setChecked(True)
        self.view_coco.setChecked(False)
        self.setWindowTitle(self._title())
        self.bottom.setCurrentWidget(self.build_log)
        self.status_extra.setText("Disassembled")
        QMessageBox.information(
            self,
            "Disassemble",
            f"{msg}\n\n"
            f"Opened:\n{out}\n\n"
            "Best-effort listing — clean up before re-assembling with lwasm.",
        )

    def do_run(self) -> None:
        if not self.project:
            QMessageBox.information(self, "Run", "Open or create a project first.")
            return
        if self._dirty:
            self.save_current()
        self.tools.resolve()
        if not self.tools.xroar:
            QMessageBox.warning(
                self,
                "XRoar missing",
                "xroar not found.\n\n"
                "Install XRoar on PATH, place it in a tools/ folder next to "
                "CoCoIDE (portable builds), or set COCOIDE_XROAR to the binary.",
            )
            return
        report = run_project(self.tools, self.project)
        self._log_build(report.messages)
        self._show_diagnostics(report.diagnostics)
        if report.xroar_cmd:
            self.xroar_log.appendPlainText(" ".join(report.xroar_cmd))
            self.bottom.setCurrentWidget(self.xroar_log)
        self.refresh_disk()
        self._rebuild_tree()
        errs = sum(1 for d in report.diagnostics if d.severity == "error")
        self.status_extra.setText(
            "XRoar launched" if report.ok else "Run failed"
        )
        if errs:
            self.status_extra.setText(
                f"{'XRoar launched' if report.ok else 'Run failed'} · {errs} err"
            )
        if not report.ok:
            QMessageBox.warning(self, "Run failed", "\n".join(report.messages[-6:]))

    def _show_diagnostics(self, diags: list[Diagnostic]) -> None:
        from PySide6.QtGui import QColor, QBrush
        from PySide6.QtWidgets import QListWidgetItem

        self._diagnostics = list(diags)
        self.problems.clear()
        if not diags:
            item = QListWidgetItem("No issues found.")
            item.setForeground(QBrush(QColor("#3dcc85")))
            self.problems.addItem(item)
        else:
            colors = {
                "error": QColor("#e85a5a"),
                "warning": QColor("#e6b84d"),
                "info": QColor("#5b9fd4"),
            }
            for d in diags:
                item = QListWidgetItem(d.format())
                item.setData(Qt.ItemDataRole.UserRole, d)
                item.setForeground(QBrush(colors.get(d.severity, QColor("#e8eaed"))))
                self.problems.addItem(item)
        errs = sum(1 for d in diags if d.severity == "error")
        warns = sum(1 for d in diags if d.severity == "warning")
        infos = sum(1 for d in diags if d.severity == "info")
        label = "Problems"
        if diags:
            label = f"Problems ({errs}/{warns}/{infos})"
        self.bottom.setTabText(self.bottom.indexOf(self.problems), label)

    def _on_problem_activated(self, item) -> None:  # noqa: ANN001
        d = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(d, Diagnostic) or not self.project or not self.project.root:
            return
        if not d.path:
            return
        path = self.project.root / d.path
        if not path.is_file():
            return
        self._open_file(path)
        if not d.line or d.line <= 0:
            return
        from PySide6.QtGui import QTextCursor

        # Modern sources: line is 1-based file line.
        # Generated .bas: line may be a CoCo line number (100, 110, …) — search for it.
        doc = self.editor.document()
        target_block = None
        if path.suffix.lower() == ".bas" and "build" in path.parts:
            needle = f"{d.line} "
            for i in range(doc.blockCount()):
                block = doc.findBlockByNumber(i)
                t = block.text().lstrip()
                if t.startswith(needle) or t.startswith(f"{d.line}\t"):
                    target_block = block
                    break
        if target_block is None:
            target_block = doc.findBlockByNumber(d.line - 1)
        if target_block is not None and target_block.isValid():
            cursor = QTextCursor(target_block)
            self.editor.setTextCursor(cursor)
            self.editor.setFocus()
            self.editor.centerCursor()

    def refresh_disk(self) -> None:
        from PySide6.QtWidgets import QListWidgetItem

        self.disk_list.clear()
        if not self.project:
            self.disk_meta.setText("No project")
            self.disk_free_label.setText("Free granules —")
            self._set_disk_bar(None, None)
            return
        listing, free = disk_listing(self.tools, self.project)
        disk = self.project.disk_path
        name = disk.name if disk else "?"
        # Geometry hint for meta line (35T default for our dskini -3)
        exists = bool(disk and disk.exists())
        self.disk_meta.setText(f"{name}\n35T SS DECB" if exists else f"{name}\n(not created)")

        free_n, total_n = parse_granule_usage(free, listing)
        if free_n is not None and total_n is not None:
            self.disk_free_label.setText(f"Free granules  {free_n} / {total_n}")
            self._set_disk_bar(free_n, total_n)
        elif free.strip():
            self.disk_free_label.setText(free.strip().splitlines()[0])
            self._set_disk_bar(None, None)
        else:
            self.disk_free_label.setText(
                "Free granules —" if exists else "Free granules — (New or Build first)"
            )
            self._set_disk_bar(None, None)

        for row in parse_decb_dir(listing):
            label = row["raw"]
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, row["name"])
            self.disk_list.addItem(item)

    # ── Disk panel actions ───────────────────────────────────────

    def _require_disk_tools(self) -> bool:
        self.tools.resolve()
        if not self.project:
            QMessageBox.information(self, "Disk", "Open or create a project first.")
            return False
        if not self.tools.decb:
            QMessageBox.warning(
                self,
                "decb missing",
                "Toolshed `decb` not found.\n\n"
                "Install Toolshed on PATH, place decb in tools/ next to CoCoIDE, "
                "or set COCOIDE_DECB.",
            )
            return False
        return True

    def _ensure_project_disk(self) -> Path | None:
        if not self._require_disk_tools() or not self.project:
            return None
        rep = ensure_disk(self.tools, self.project)
        if rep.messages:
            self._log_build(rep.messages)
        if not rep.ok or not self.project.disk_path:
            QMessageBox.warning(self, "Disk", "\n".join(rep.messages) or "Could not create disk")
            return None
        return self.project.disk_path

    def disk_new(self) -> None:
        if not self._require_disk_tools() or not self.project or not self.project.disk_path:
            return
        disk = self.project.disk_path
        if disk.exists():
            r = QMessageBox.question(
                self,
                "New disk",
                f"Replace existing disk image?\n\n{disk}\n\n"
                "All files on the image will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r != QMessageBox.StandardButton.Yes:
                return
        assert self.tools.decb
        proc = decb_dskini(self.tools.decb, disk, tracks="3")
        if proc.returncode != 0:
            QMessageBox.warning(
                self,
                "New disk failed",
                (proc.stderr or proc.stdout or "dskini failed").strip(),
            )
            return
        self._log_build([f"Created blank disk {disk}"])
        self.refresh_disk()
        self._rebuild_tree()
        self.status_extra.setText("New blank disk")

    def disk_add_file(self) -> None:
        disk = self._ensure_project_disk()
        if not disk or not self.tools.decb:
            return
        path, _ = get_open_file_name(
            self,
            "Add file to disk image",
            str(self.project.root if self.project and self.project.root else Path.home()),
            "CoCo files (*.bas *.bin *.dat *.txt *.asc);;All (*.*)",
        )
        if not path:
            return
        self._add_host_file_to_disk(Path(path), disk)

    def disk_add_current(self) -> None:
        disk = self._ensure_project_disk()
        if not disk or not self.tools.decb:
            return
        if not self._current_file or not self._current_file.is_file():
            QMessageBox.information(
                self,
                "Add current",
                "No file open. Open a host file, or use Build Disk for modern BASIC.",
            )
            return
        path = self._current_file
        if path.suffix.lower() == ".mbas":
            QMessageBox.information(
                self,
                "Add current",
                "Modern BASIC (.mbas) is packaged with Build Disk, not raw-copied.\n"
                "Use Build Disk, or open a .bas/.bin to add directly.",
            )
            return
        if self._dirty and not self.editor.isReadOnly():
            self.save_current()
        self._add_host_file_to_disk(path, disk)

    def _add_host_file_to_disk(self, host: Path, disk: Path) -> None:
        assert self.tools.decb
        coco = host_to_coco_name(host)
        ftype, binary, tokenize = guess_decb_type(host)
        # Artifacts already numbered BASIC — still fine to tokenize
        proc = decb_copy_to_disk(
            self.tools.decb,
            host,
            disk,
            coco,
            file_type=ftype,
            binary=binary,
            tokenize=tokenize,
            eol_translate=(ftype == 3 and not binary),
        )
        if proc.returncode != 0 and tokenize:
            proc = decb_copy_to_disk(
                self.tools.decb,
                host,
                disk,
                coco,
                file_type=ftype,
                binary=binary,
                tokenize=False,
            )
        if proc.returncode != 0:
            QMessageBox.warning(
                self,
                "Add failed",
                (proc.stderr or proc.stdout or f"decb copy failed for {coco}").strip(),
            )
            return
        self._log_build([f"Added {host.name} → {coco} (type {ftype})"])
        self.refresh_disk()
        self.status_extra.setText(f"Added {coco}")

    def _selected_coco_name(self) -> str | None:
        item = self.disk_list.currentItem()
        if not item:
            return None
        name = item.data(Qt.ItemDataRole.UserRole)
        return str(name) if name else None

    def disk_extract(self) -> None:
        disk = self._ensure_project_disk()
        if not disk or not self.tools.decb or not self.project or not self.project.root:
            return
        coco = self._selected_coco_name()
        if not coco:
            QMessageBox.information(self, "Extract", "Select a file in the disk list first.")
            return
        default = self.project.root / "build" / coco.replace("/", "_")
        path, _ = get_save_file_name(
            self,
            f"Extract {coco}",
            str(default),
            "All (*.*)",
        )
        if not path:
            return
        host = Path(path)
        # EOL translate for text-ish extensions
        eol = host.suffix.lower() in (".txt", ".bas", ".asc", ".asm")
        proc = decb_extract(self.tools.decb, disk, coco, host, eol_translate=eol)
        if proc.returncode != 0:
            # retry without -l
            proc = decb_extract(self.tools.decb, disk, coco, host, eol_translate=False)
        if proc.returncode != 0:
            QMessageBox.warning(
                self,
                "Extract failed",
                (proc.stderr or proc.stdout or "decb copy failed").strip(),
            )
            return
        self._log_build([f"Extracted {coco} → {host}"])
        self.status_extra.setText(f"Extracted {coco}")
        self._rebuild_tree()

    def disk_delete(self) -> None:
        disk = self._ensure_project_disk()
        if not disk or not self.tools.decb:
            return
        coco = self._selected_coco_name()
        if not coco:
            QMessageBox.information(self, "Delete", "Select a file in the disk list first.")
            return
        r = QMessageBox.question(
            self,
            "Delete from disk",
            f"Delete {coco} from the disk image?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r != QMessageBox.StandardButton.Yes:
            return
        proc = decb_kill(self.tools.decb, disk, coco)
        if proc.returncode != 0:
            QMessageBox.warning(
                self,
                "Delete failed",
                (proc.stderr or proc.stdout or "decb kill failed").strip(),
            )
            return
        self._log_build([f"Deleted {coco} from disk"])
        self.refresh_disk()
        self.status_extra.setText(f"Deleted {coco}")

    def _set_disk_bar(self, free: int | None, total: int | None) -> None:
        if free is None or total is None or total <= 0:
            self.disk_bar.setValue(0)
            self.disk_bar.setFormat("")
            self.disk_bar.setToolTip("Disk space unknown")
            self.disk_bar.setProperty("level", "empty")
            self.disk_bar.style().unpolish(self.disk_bar)
            self.disk_bar.style().polish(self.disk_bar)
            return
        used = max(0, total - free)
        pct = int(round(100.0 * used / total))
        self.disk_bar.setValue(pct)
        self.disk_bar.setToolTip(f"Used {used} / {total} granules ({pct}%)")
        if pct >= 90:
            level = "critical"
        elif pct >= 70:
            level = "warn"
        else:
            level = "ok"
        self.disk_bar.setProperty("level", level)
        self.disk_bar.style().unpolish(self.disk_bar)
        self.disk_bar.style().polish(self.disk_bar)

    def _log_build(self, messages: list[str]) -> None:
        for m in messages:
            self.build_log.appendPlainText(m)

    def _user_guide_dir(self) -> Path | None:
        """Directory containing the user guide markdown pages."""
        import sys

        candidates: list[Path] = []
        # Portable / PyInstaller: docs/ next to the executable
        candidates.append(
            Path(sys.executable).resolve().parent / "docs" / "user-guide"
        )
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "docs" / "user-guide")
        # Source tree: cocoide/mainwindow.py → repo root
        candidates.append(
            Path(__file__).resolve().parent.parent / "docs" / "user-guide"
        )
        # PyInstaller onedir often puts the package under _internal/cocoide/
        # so parent.parent is _internal — also try one level up from that.
        pkg = Path(__file__).resolve().parent
        candidates.append(pkg.parent.parent / "docs" / "user-guide")
        candidates.append(pkg.parent / "docs" / "user-guide")
        candidates.append(Path.cwd() / "docs" / "user-guide")
        for d in candidates:
            if (d / "README.md").is_file():
                return d
        return None

    def _user_guide_path(self) -> Path | None:
        d = self._user_guide_dir()
        if d is None:
            return None
        return d / "README.md"

    def _open_user_guide(self) -> None:
        """Show the user guide in an in-app browser (always works offline)."""
        guide_dir = self._user_guide_dir()
        if guide_dir is None:
            QMessageBox.information(
                self,
                "User Guide",
                "User guide not found.\n\n"
                "Expected docs/user-guide/README.md next to CoCoIDE "
                "(portable zip) or in the source checkout.",
            )
            return

        if self._help_dialog is not None and self._help_dialog.isVisible():
            self._help_dialog.raise_()
            self._help_dialog.activateWindow()
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("CoCoIDE User Guide")
        dlg.resize(780, 560)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        layout = QVBoxLayout(dlg)
        toolbar = QHBoxLayout()
        btn_home = QPushButton("Home")
        btn_back = QPushButton("Back")
        btn_open_ext = QPushButton("Open folder…")
        path_label = QLabel()
        path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        toolbar.addWidget(btn_home)
        toolbar.addWidget(btn_back)
        toolbar.addWidget(btn_open_ext)
        toolbar.addWidget(path_label, stretch=1)
        layout.addLayout(toolbar)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setOpenLinks(False)
        layout.addWidget(browser, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)
        buttons.accepted.connect(dlg.accept)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn is not None:
            close_btn.clicked.connect(dlg.accept)
        layout.addWidget(buttons)

        history: list[Path] = []

        def show_page(path: Path, *, push_history: bool = True) -> None:
            path = path.resolve()
            if not path.is_file():
                browser.setPlainText(f"Page not found:\n{path}")
                path_label.setText(str(path))
                return
            if push_history and (not history or history[-1] != path):
                history.append(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            # Qt renders CommonMark-ish markdown; relative links stay as hrefs.
            browser.setMarkdown(text)
            browser.setSearchPaths([str(path.parent)])
            path_label.setText(str(path.name))
            dlg.setWindowTitle(f"CoCoIDE User Guide — {path.name}")

        def on_anchor(url: QUrl) -> None:
            if url.isRelative() or url.scheme() in ("", "file"):
                local = url.toLocalFile() if url.isLocalFile() else url.path()
                # QUrl relative: path may be "01-getting-started.md"
                rel = local or url.toString()
                if rel.startswith("file:"):
                    target = Path(QUrl(rel).toLocalFile())
                else:
                    base = history[-1].parent if history else guide_dir
                    target = (base / rel).resolve()
                # Only navigate within the guide tree (and immediate parents for
                # linked reference docs that may or may not be shipped).
                if target.suffix.lower() in {".md", ".markdown", ".txt", ".html"}:
                    if target.is_file():
                        show_page(target)
                        return
                    browser.setPlainText(
                        f"Linked page not found:\n{target}\n\n"
                        f"(Guide root: {guide_dir})"
                    )
                    return
            # External / unknown — try desktop handler
            QDesktopServices.openUrl(url)

        def go_home() -> None:
            history.clear()
            show_page(guide_dir / "README.md")

        def go_back() -> None:
            if len(history) > 1:
                history.pop()
                show_page(history[-1], push_history=False)

        def open_folder() -> None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(guide_dir)))

        browser.anchorClicked.connect(on_anchor)
        btn_home.clicked.connect(go_home)
        btn_back.clicked.connect(go_back)
        btn_open_ext.clicked.connect(open_folder)

        def on_finished() -> None:
            self._help_dialog = None

        dlg.finished.connect(on_finished)
        self._help_dialog = dlg
        show_page(guide_dir / "README.md")
        dlg.show()

    def _about_mascot_path(self) -> Path | None:
        """Bundled mascot, then ~/coco.jpg."""
        bundled = Path(__file__).resolve().parent / "assets" / "coco.jpg"
        if bundled.is_file():
            return bundled
        home = Path.home() / "coco.jpg"
        if home.is_file():
            return home
        return None

    def _about(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("About CoCoIDE")
        dlg.setModal(True)
        dlg.setMinimumWidth(480)
        root = QHBoxLayout(dlg)
        root.setSpacing(20)
        root.setContentsMargins(20, 16, 20, 16)

        text_col = QVBoxLayout()
        text_col.setSpacing(8)
        self.tools.resolve()
        paths_html = "<br/>".join(
            f"<code>{name}={getattr(self.tools, name) or 'missing'}</code>"
            for name in ("xroar", "decb", "lwasm")
        )
        body = QLabel(
            f"<h2 style='margin:0 0 8px 0;'>CoCoIDE {__version__}</h2>"
            "<p style='margin:4px 0;'>Tandy Color Computer IDE — Disk Extended BASIC</p>"
            "<p style='margin:4px 0;'>Integrates XRoar, Toolshed <code>decb</code>, "
            "and LWTOOLS (lwasm).</p>"
            f"<p style='margin:4px 0;'>Tools: {self.tools.status_line()}</p>"
            f"<p style='margin:4px 0; font-size: small;'>{paths_html}</p>"
            "<p style='margin:4px 0;'>F1 for Help</p>"
            "<p style='margin:12px 0 0 0;'>(C) Alex Gayer 2026</p>"
        )
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setWordWrap(True)
        body.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        text_col.addWidget(body)
        text_col.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dlg.accept)
        text_col.addWidget(buttons)
        root.addLayout(text_col, stretch=1)

        mascot = self._about_mascot_path()
        if mascot is not None:
            pix = QPixmap(str(mascot))
            if not pix.isNull():
                # Portrait mascot — keep on the right, max ~220px tall
                scaled = pix.scaled(
                    QSize(160, 240),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                img = QLabel()
                img.setPixmap(scaled)
                img.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
                img.setStyleSheet(
                    "QLabel { background: transparent; padding: 0; border: none; }"
                )
                root.addWidget(img, stretch=0)

        dlg.exec()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._dirty and not self._confirm_discard():
            event.ignore()
            return
        event.accept()
