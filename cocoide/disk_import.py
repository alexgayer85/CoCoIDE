"""Import from external DECB .dsk images and create projects from disks."""

from __future__ import annotations

import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from cocoide.project import PROJECT_FILENAME, Project
from cocoide.tools import (
    ToolPaths,
    decb_dir,
    decb_extract,
    decb_list,
    parse_decb_dir,
)


# Extensions that are never treated as Color BASIC programs for detokenize/rename.
NON_BASIC_EXTENSIONS = {
    ".DAT",
    ".BIN",
    ".ROM",
    ".TXT",
    ".ASC",
    ".VCG",
    ".CHR",
    ".MAP",
    ".PAL",
    ".SPR",
    ".RAW",
}


@dataclass
class DiskFile:
    name: str  # NAME.EXT
    raw: str
    type: str  # "0".."3" or ""
    ascii_flag: str  # A/B
    granules: str

    @property
    def extension(self) -> str:
        return Path(self.name).suffix.upper()

    @property
    def is_basic(self) -> bool:
        """Likely a BASIC *program* (for “Import all BASIC”).

        Prefer the filename extension over DECB type: many disks store ASCII
        data as type 0, and ``decb list -t`` will mangle those if we treat
        every type-0 file as BASIC.
        """
        ext = self.extension
        if ext in NON_BASIC_EXTENSIONS:
            return False
        if ext == ".BAS":
            return True
        # No/unknown extension: type 0 is a weak hint only
        if not ext and self.type == "0":
            return True
        return False

    @property
    def is_binary_ml(self) -> bool:
        return self.type == "2" or self.extension == ".BIN"


@dataclass
class ImportResult:
    ok: bool
    messages: list[str] = field(default_factory=list)
    paths: list[Path] = field(default_factory=list)


def list_disk_files(tools: ToolPaths, disk: Path) -> tuple[list[DiskFile], str]:
    """Return parsed directory and raw dir text."""
    if not tools.decb:
        return [], "decb not found"
    if not disk.is_file():
        return [], f"Disk not found: {disk}"
    proc = decb_dir(tools.decb, disk)
    text = proc.stdout or proc.stderr or ""
    files: list[DiskFile] = []
    for row in parse_decb_dir(text):
        files.append(
            DiskFile(
                name=row["name"],
                raw=row["raw"],
                type=row.get("type", ""),
                ascii_flag=row.get("ascii", ""),
                granules=row.get("granules", ""),
            )
        )
    return files, text


def safe_host_stem(coco_name: str) -> str:
    stem = Path(coco_name).stem
    stem = re.sub(r"[^A-Za-z0-9_-]", "_", stem) or "file"
    return stem.lower()


def host_name_for_disk_file(coco_name: str) -> str:
    """Preserve DECB extension on the host (SCORES.DAT → scores.dat, not .bas)."""
    stem = safe_host_stem(coco_name)
    ext = Path(coco_name).suffix.lower()
    if not ext:
        ext = ".dat"
    return f"{stem}{ext}"


def looks_like_tokenized_basic(data: bytes) -> bool:
    """DECB tokenized programs typically start with 0xFF.

    ASCII listings / data files do not — refuse to run ``list -t`` on them.
    """
    if not data:
        return False
    # Standard DECB tokenized BASIC lead-in
    if data[0] == 0xFF:
        return True
    # Some tools strip the FF; look for line structure: lo hi link, line# lo hi
    # Avoid false positives on short binary. Require 0xFF somewhere early only
    # if second byte patterns — keep conservative: require leading 0xFF.
    return False


def looks_like_ascii_text(data: bytes) -> bool:
    if not data:
        return True
    sample = data[:512]
    # Allow CR/LF/TAB and printable
    for b in sample:
        if b in (9, 10, 13):
            continue
        if b < 32 or b > 126:
            return False
    return True


def import_file_from_disk(
    tools: ToolPaths,
    disk: Path,
    coco_name: str,
    dest: Path,
    *,
    file_type: str = "",
    prefer_detokenize: bool = True,
    force_raw: bool = False,
    disassemble_bin: bool = False,
) -> ImportResult:
    """Import one file from a .dsk to the host.

    - Always preserves the caller's ``dest`` path (including extension).
    - Detokenize only when ``prefer_detokenize`` and the payload looks like
      tokenized BASIC (0xFF header), and the name is not a non-BASIC extension.
    - Otherwise raw ``decb copy`` (optional CR/LF translate for ASCII).
    """
    result = ImportResult(ok=True)
    if not tools.decb:
        result.ok = False
        result.messages.append("decb not found")
        return result

    dest.parent.mkdir(parents=True, exist_ok=True)
    ext = Path(coco_name).suffix.upper()
    non_basic_ext = ext in NON_BASIC_EXTENSIONS

    # Always pull a raw copy first (to a temp file) so we can sniff content.
    with tempfile.NamedTemporaryFile(prefix="cocoide_imp_", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        raw = decb_extract(
            tools.decb, disk, coco_name, tmp_path, eol_translate=False
        )
        if raw.returncode != 0:
            result.ok = False
            result.messages.append(
                f"Import failed for {coco_name}: "
                f"{(raw.stderr or raw.stdout or '').strip()}"
            )
            return result

        data = tmp_path.read_bytes()
        tokenized = looks_like_tokenized_basic(data)
        ascii_text = looks_like_ascii_text(data)

        do_detok = (
            prefer_detokenize
            and not force_raw
            and not non_basic_ext
            and tokenized
            and (ext == ".BAS" or file_type == "0" or ext == "")
        )

        if do_detok:
            listed = decb_list(tools.decb, disk, coco_name, detokenize=True)
            if listed.returncode == 0 and (listed.stdout or "").strip():
                text = listed.stdout.replace("\r\n", "\n").replace("\r", "\n")
                if not text.endswith("\n"):
                    text += "\n"
                dest.write_text(text, encoding="utf-8", errors="replace")
                result.paths.append(dest)
                result.messages.append(
                    f"Imported (detokenized BASIC) {coco_name} → {dest.name}"
                )
                return result
            result.messages.append(
                f"list -t failed for {coco_name}; keeping raw bytes"
            )

        # Raw copy (as-is). EOL translate only for clear ASCII non-tokenized text.
        if ascii_text and not tokenized:
            # Prefer host text with Unix newlines for editing
            text = data.decode("utf-8", errors="replace")
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            dest.write_text(text, encoding="utf-8", errors="replace")
            kind = "ASCII"
        else:
            dest.write_bytes(data)
            kind = "raw/binary"

        if prefer_detokenize and not force_raw and not do_detok:
            if non_basic_ext:
                result.messages.append(
                    f"Imported ({kind}, not detokenized — {ext or 'no ext'} data) "
                    f"{coco_name} → {dest.name}"
                )
            elif not tokenized:
                result.messages.append(
                    f"Imported ({kind}, not tokenized BASIC) {coco_name} → {dest.name}"
                )
            else:
                result.messages.append(f"Imported ({kind}) {coco_name} → {dest.name}")
        else:
            result.messages.append(f"Imported ({kind}) {coco_name} → {dest.name}")
        result.paths.append(dest)

        # Optional 6809 disassembly alongside machine-language binaries
        is_ml = (
            disassemble_bin
            and not force_raw
            and (
                ext == ".BIN"
                or file_type == "2"
                or (kind == "raw/binary" and ext == ".BIN")
            )
        )
        if is_ml and dest.is_file():
            try:
                from cocoide.disasm6809 import disassemble_bin_file

                asm_path = dest.with_suffix(".asm")
                _text, msg = disassemble_bin_file(dest, asm_path)
                result.paths.append(asm_path)
                result.messages.append(msg)
            except Exception as exc:  # noqa: BLE001 — best-effort
                result.messages.append(f"Disassembly skipped for {coco_name}: {exc}")

        return result
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


def import_files_to_directory(
    tools: ToolPaths,
    disk: Path,
    files: list[DiskFile],
    dest_dir: Path,
    *,
    basic_as_ascii: bool = True,
    force_raw: bool = False,
    disassemble_bin: bool = False,
) -> ImportResult:
    """Import many files into dest_dir (unique host names; **keep extensions**)."""
    combined = ImportResult(ok=True)
    dest_dir.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()

    for f in files:
        host_name = host_name_for_disk_file(f.name)
        base, suf = Path(host_name).stem, Path(host_name).suffix
        candidate = host_name
        n = 2
        while candidate.lower() in used or (dest_dir / candidate).exists():
            candidate = f"{base}_{n}{suf}"
            n += 1
        used.add(candidate.lower())
        dest = dest_dir / candidate
        one = import_file_from_disk(
            tools,
            disk,
            f.name,
            dest,
            file_type=f.type,
            prefer_detokenize=basic_as_ascii and not force_raw,
            force_raw=force_raw,
            disassemble_bin=disassemble_bin,
        )
        combined.messages.extend(one.messages)
        combined.paths.extend(one.paths)
        if not one.ok:
            combined.ok = False
    return combined


def create_project_from_disk(
    tools: ToolPaths,
    source_disk: Path,
    project_root: Path,
    *,
    name: str | None = None,
    target: str = "coco3",
    memory_kb: int = 512,
    import_all: bool = True,
    entry_coco_name: str | None = None,
) -> tuple[Project | None, ImportResult]:
    """Create a CoCoIDE project from an existing DECB .dsk.

    - Copies the disk to ``build/work.dsk``
    - Imports BASIC (and optionally all files) under ``src/imported/``
    - Sets ``preprocessor: false`` so classic line-numbered BASIC is edited as-is
    - Entry points at the chosen / first BASIC file
    """
    result = ImportResult(ok=True)
    if not source_disk.is_file():
        result.ok = False
        result.messages.append(f"Disk not found: {source_disk}")
        return None, result
    if not tools.decb:
        result.ok = False
        result.messages.append("decb not found")
        return None, result

    project_root = project_root.resolve()
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "src").mkdir(exist_ok=True)
    (project_root / "src" / "imported").mkdir(exist_ok=True)
    (project_root / "build").mkdir(exist_ok=True)

    proj_name = name or project_root.name or source_disk.stem
    dest_disk = project_root / "build" / "work.dsk"
    shutil.copy2(source_disk, dest_disk)
    result.messages.append(f"Copied disk → {dest_disk.relative_to(project_root)}")

    files, _ = list_disk_files(tools, dest_disk)
    if not files:
        result.messages.append("Disk directory is empty or unreadable")

    bas_files = [f for f in files if f.is_basic]
    other = [f for f in files if not f.is_basic]

    to_import = list(files) if import_all else list(bas_files)
    if to_import:
        imp = import_files_to_directory(
            tools,
            dest_disk,
            to_import,
            project_root / "src" / "imported",
            basic_as_ascii=True,
        )
        result.messages.extend(imp.messages)
        result.paths.extend(imp.paths)
        if not imp.ok:
            result.ok = False

    # Pick entry: explicit name, else first BAS, else a stub
    entry_rel = "src/imported/main.bas"
    chosen: DiskFile | None = None
    if entry_coco_name:
        for f in bas_files:
            if f.name.upper() == entry_coco_name.upper():
                chosen = f
                break
    if chosen is None and bas_files:
        chosen = bas_files[0]

    if chosen:
        stem = safe_host_stem(chosen.name)
        # Find imported path
        candidates = list((project_root / "src" / "imported").glob(f"{stem}*.bas"))
        if candidates:
            entry_rel = str(candidates[0].relative_to(project_root))
        else:
            entry_rel = f"src/imported/{stem}.bas"
    else:
        stub = project_root / "src" / "imported" / "main.bas"
        if not stub.exists():
            stub.write_text(
                "10 REM IMPORTED DISK HAD NO BASIC FILES\n20 END\n",
                encoding="utf-8",
            )
        entry_rel = "src/imported/main.bas"
        result.messages.append("No BASIC files on disk — wrote stub entry")

    # README for the user
    readme = project_root / "src" / "imported" / "README.txt"
    readme.write_text(
        "Files imported from a DECB disk image.\n"
        "BASIC was detokenized to ASCII for editing.\n"
        "This project uses preprocessor: false (classic line numbers).\n"
        "Rebuild with Build Disk to refresh build/work.dsk from sources,\n"
        "or keep using the copied original disk until you rebuild.\n",
        encoding="utf-8",
    )

    proj = Project(
        name=proj_name,
        target=target,
        memory_kb=memory_kb,
        dialect="decb",
        entry=entry_rel,
        disk_image="build/work.dsk",
        auto_run=True,
        preprocessor=False,  # classic imported BASIC
        standalone=[],
        root=project_root,
    )
    proj.save()
    result.messages.append(f"Created project {project_root / PROJECT_FILENAME}")
    result.messages.append(f"Entry: {entry_rel}")
    if bas_files:
        result.messages.append(
            f"BASIC files on disk: {', '.join(f.name for f in bas_files)}"
        )
    if other and import_all:
        result.messages.append(
            f"Also imported: {', '.join(f.name for f in other)}"
        )
    return proj, result


def copy_disk_into_project(
    source_disk: Path,
    project: Project,
    *,
    replace: bool = True,
) -> ImportResult:
    """Mount/copy an external .dsk as the project's disk image."""
    result = ImportResult(ok=True)
    if not project.root or not project.disk_path:
        result.ok = False
        result.messages.append("No project disk path")
        return result
    if not source_disk.is_file():
        result.ok = False
        result.messages.append(f"Disk not found: {source_disk}")
        return result
    dest = project.disk_path
    if dest.exists() and not replace:
        result.ok = False
        result.messages.append("Project disk exists; refuse to replace")
        return result
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_disk, dest)
    result.messages.append(f"Mounted (copied) {source_disk.name} → {project.disk_image}")
    return result


def create_project_around_imports(
    import_dir: Path,
    *,
    source_disk: Path | None = None,
    name: str | None = None,
    target: str = "coco3",
    memory_kb: int = 512,
    entry_bas: Path | None = None,
) -> tuple[Project | None, ImportResult]:
    """Create project.cocoide for a folder that already has imported .bas files.

    Project root is ``import_dir`` if it is named like a project, otherwise
    the parent of ``import_dir`` when imports live in ``src/imported``, else
    ``import_dir`` itself becomes root with sources at ``src/imported``.
    """
    result = ImportResult(ok=True)
    import_dir = import_dir.resolve()
    if not import_dir.is_dir():
        result.ok = False
        result.messages.append(f"Not a directory: {import_dir}")
        return None, result

    # Layout A: …/project/src/imported  → root = project
    # Layout B: arbitrary folder of .bas → root = folder, move/copy structure
    if (
        import_dir.name.lower() == "imported"
        and import_dir.parent.name.lower() == "src"
        and import_dir.parent.parent.is_dir()
    ):
        project_root = import_dir.parent.parent
        entry_prefix = "src/imported"
        imported = import_dir
    else:
        project_root = import_dir
        imported = project_root / "src" / "imported"
        if imported.resolve() != import_dir.resolve():
            imported.mkdir(parents=True, exist_ok=True)
            # If files sit directly in import_dir, leave them; prefer listing both
            if import_dir != imported and any(import_dir.glob("*.bas")):
                # files already in import_dir as flat folder project
                imported = import_dir
                entry_prefix = "."
            else:
                entry_prefix = "src/imported"
        else:
            entry_prefix = "src/imported"

    (project_root / "src").mkdir(exist_ok=True)
    (project_root / "build").mkdir(exist_ok=True)

    bas_files = sorted(set(imported.glob("*.bas")) | set(imported.glob("*.BAS")))
    if not bas_files and entry_prefix == ".":
        bas_files = sorted(project_root.glob("*.bas"))
    if not bas_files:
        bas_files = sorted(project_root.rglob("*.bas"))

    def _prefer_main(paths: list[Path]) -> list[Path]:
        def key(p: Path) -> tuple:
            n = p.stem.lower()
            # Prefer classic main / startup names
            rank = 0 if n in ("main", "startup", "menu", "run") else 1
            return (rank, p.name.lower())

        return sorted(paths, key=key)

    bas_files = _prefer_main(bas_files)

    if entry_bas and entry_bas.is_file():
        entry_path = entry_bas.resolve()
    elif bas_files:
        entry_path = bas_files[0].resolve()
    else:
        stub = imported / "main.bas" if imported.is_dir() else project_root / "main.bas"
        stub.parent.mkdir(parents=True, exist_ok=True)
        stub.write_text("10 REM NO BASIC IMPORTED\n20 END\n", encoding="utf-8")
        entry_path = stub
        result.messages.append("No .bas found — wrote stub main.bas")

    try:
        entry_rel = str(entry_path.relative_to(project_root))
    except ValueError:
        # copy into src/imported
        dest_entry = project_root / "src" / "imported" / entry_path.name
        dest_entry.parent.mkdir(parents=True, exist_ok=True)
        if entry_path != dest_entry:
            shutil.copy2(entry_path, dest_entry)
        entry_rel = str(dest_entry.relative_to(project_root))

    if source_disk and source_disk.is_file():
        dest_disk = project_root / "build" / "work.dsk"
        if not dest_disk.exists():
            shutil.copy2(source_disk, dest_disk)
            result.messages.append(f"Copied disk → build/work.dsk")

    proj = Project(
        name=name or project_root.name,
        target=target,
        memory_kb=memory_kb,
        dialect="decb",
        entry=entry_rel.replace("\\", "/"),
        disk_image="build/work.dsk",
        auto_run=True,
        preprocessor=False,
        standalone=[],
        root=project_root,
    )
    saved = proj.save()
    result.messages.append(f"Created project file: {saved}")
    result.messages.append(f"Project root: {project_root}")
    result.messages.append(f"Entry: {entry_rel}")
    result.paths.append(saved)
    return proj, result
