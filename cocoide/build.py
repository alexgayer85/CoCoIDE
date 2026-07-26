"""Build pipeline: preprocess → disk image → optional XRoar launch."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cocoide.asm import assemble_project
from cocoide.diagnostics import Diagnostic, analyze_after_build
from cocoide.preprocessor import (
    discover_standalones,
    preprocess_project,
    write_artifact,
)
from cocoide.project import Project
from cocoide.tools import (
    ToolPaths,
    build_xroar_command,
    decb_copy_bas,
    decb_copy_to_disk,
    decb_dir,
    decb_dskini,
    decb_free,
    decb_free_granules,
    decb_kill_quiet,
    entry_disk_name,
    launch_xroar,
)


@dataclass
class BuildReport:
    ok: bool
    messages: list[str] = field(default_factory=list)
    coco_path: Path | None = None
    disk_path: Path | None = None
    xroar_cmd: list[str] | None = None
    var_map: dict[str, str] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    standalones: list[str] = field(default_factory=list)  # disk names copied


def ensure_disk(tools: ToolPaths, project: Project) -> BuildReport:
    report = BuildReport(ok=True)
    if not tools.decb:
        report.ok = False
        report.messages.append("decb not found — install Toolshed")
        return report
    disk = project.disk_path
    assert disk is not None
    if not disk.exists():
        proc = decb_dskini(tools.decb, disk)
        if proc.returncode != 0:
            report.ok = False
            report.messages.append(f"dskini failed: {proc.stderr or proc.stdout}")
            return report
        report.messages.append(f"Created disk {disk}")
    report.disk_path = disk
    return report


def build_project(tools: ToolPaths, project: Project) -> BuildReport:
    report = BuildReport(ok=True)
    if not project.root:
        report.ok = False
        report.messages.append("No project root")
        return report

    entry = project.entry_path
    if not entry or not entry.is_file():
        report.ok = False
        report.messages.append(f"Entry not found: {project.entry}")
        return report

    preprocess_warnings: list[str] = []
    coco_text = ""
    standalone_units = discover_standalones(project.root, project.standalone)
    standalone_rels = [u.rel for u in standalone_units]

    # Preprocess entry link unit
    if project.preprocessor:
        result = preprocess_project(entry, project.root)
        preprocess_warnings = list(result.warnings)
        report.messages.extend(f"preprocess: {w}" for w in result.warnings)
        report.var_map = result.var_map
        report.includes = list(result.includes)
        coco_path = project.root / "build" / (Path(project.entry).stem + ".bas")
        write_artifact(result, coco_path)
        report.coco_path = coco_path
        coco_text = result.coco_text
        report.messages.append(f"Wrote artifact {coco_path.relative_to(project.root)}")

        # Warn if a standalone is also pulled into the entry include graph
        inc_names = {Path(p).name.lower() for p in result.includes}
        inc_rels = {p.lower().replace("\\", "/") for p in result.includes}
        for unit in standalone_units:
            if (
                unit.source.name.lower() in inc_names
                or unit.rel.lower().replace("\\", "/") in inc_rels
            ):
                msg = (
                    f"{unit.rel} is @standalone but also @include'd by the entry — "
                    f"it will be merged into MAIN and also copied as {unit.disk_name}"
                )
                preprocess_warnings.append(msg)
                report.messages.append(f"preprocess: {msg}")
    else:
        coco_path = entry
        report.coco_path = coco_path
        try:
            coco_text = entry.read_text(encoding="utf-8", errors="replace")
        except OSError:
            coco_text = ""

    # Preprocess each standalone into build/<stem>.bas
    standalone_artifacts: list[tuple[Path, str]] = []  # (host bas, disk name)
    if project.preprocessor:
        for unit in standalone_units:
            # Skip if this path is the project entry (nonsensical standalone on main)
            if unit.source.resolve() == entry.resolve():
                msg = f"Entry file {unit.rel} has @standalone — ignored (entry is the Run program)"
                preprocess_warnings.append(msg)
                report.messages.append(f"preprocess: {msg}")
                continue
            sa = preprocess_project(unit.source, project.root)
            preprocess_warnings.extend(sa.warnings)
            report.messages.extend(
                f"preprocess[{unit.disk_name}]: {w}" for w in sa.warnings
            )
            art = project.root / "build" / (unit.source.stem + ".bas")
            # Avoid clobbering entry artifact if same stem
            if art.resolve() == (project.root / "build" / (Path(project.entry).stem + ".bas")).resolve():
                art = project.root / "build" / f"{unit.source.stem}_sa.bas"
            write_artifact(sa, art)
            standalone_artifacts.append((art, unit.disk_name))
            report.messages.append(
                f"Wrote standalone artifact {art.relative_to(project.root)} → {unit.disk_name}"
            )

    disk_report = ensure_disk(tools, project)
    report.messages.extend(disk_report.messages)
    if not disk_report.ok:
        report.ok = False
        report.diagnostics = analyze_after_build(
            project,
            coco_text=coco_text,
            var_map=report.var_map,
            includes=report.includes,
            preprocess_warnings=preprocess_warnings,
            standalone_rels=standalone_rels,
        )
        return report

    if not tools.decb:
        report.ok = False
        report.messages.append("decb not found")
        return report

    disk = project.disk_path
    assert disk is not None
    coco_name = entry_disk_name(project.entry)
    assert report.coco_path is not None

    # Assemble ASM to host first (so we know all disk names before writing)
    asm_result, asm_units = assemble_project(
        tools, project.root, project.asm_sources or None
    )
    report.messages.extend(asm_result.messages)
    if asm_units and not asm_result.ok:
        report.ok = False

    # Free space for every file we are about to rewrite *before* any copy.
    # Sequential kill+copy can still 248 if an earlier file grows and eats the
    # granules needed for a later BIN on a packed game disk.
    kill_names: list[str] = [coco_name]
    kill_names.extend(dname for _art, dname in standalone_artifacts)
    if asm_result.ok:
        kill_names.extend(u.disk_name for u in asm_units)
    free_before = decb_free_granules(tools.decb, disk)
    killed: list[str] = []
    for name in kill_names:
        if decb_kill_quiet(tools.decb, disk, name):
            killed.append(name)
    free_after_kill = decb_free_granules(tools.decb, disk)
    if killed:
        report.messages.append(
            f"Freed disk slots before write: {', '.join(killed)} "
            f"(free granules {free_before} → {free_after_kill})"
        )
    elif free_before is not None and free_before == 0:
        report.messages.append(
            "Disk reports 0 free granules and no matching names were killed — "
            "writes may fail with error 248 if files use different DECB names "
            "than this build (e.g. disk has ML.BIN but asm builds as GAME.BIN)."
        )

    # Copies skip per-file kill (already done in batch)
    copy = decb_copy_bas(
        tools.decb, report.coco_path, disk, coco_name, tokenize=True, kill_before_write=False
    )
    if copy.returncode != 0:
        copy2 = decb_copy_bas(
            tools.decb,
            report.coco_path,
            disk,
            coco_name,
            tokenize=False,
            kill_before_write=False,
        )
        if copy2.returncode != 0:
            report.ok = False
            report.messages.append(
                f"decb copy failed: {(copy.stderr or copy.stdout or copy2.stderr or copy2.stdout).strip()}"
            )
            report.diagnostics = analyze_after_build(
                project,
                coco_text=coco_text,
                var_map=report.var_map,
                includes=report.includes,
                preprocess_warnings=preprocess_warnings,
                standalone_rels=standalone_rels,
            )
            return report
        report.messages.append(f"Copied {coco_name} (ASCII) → disk")
    else:
        report.messages.append(f"Copied {coco_name} (tokenized) → disk")

    for art, dname in standalone_artifacts:
        scopy = decb_copy_bas(
            tools.decb, art, disk, dname, tokenize=True, kill_before_write=False
        )
        if scopy.returncode != 0:
            scopy = decb_copy_bas(
                tools.decb, art, disk, dname, tokenize=False, kill_before_write=False
            )
        if scopy.returncode != 0:
            report.messages.append(
                f"standalone copy failed for {dname}: "
                f"{(scopy.stderr or scopy.stdout or '').strip()}"
            )
            report.ok = False
        else:
            report.standalones.append(dname)
            report.messages.append(f"Copied standalone {dname} (tokenized) → disk")

    if asm_units and asm_result.ok:
        for unit in asm_units:
            if not unit.output_bin.is_file():
                continue
            proc = decb_copy_to_disk(
                tools.decb,
                unit.output_bin,
                disk,
                unit.disk_name,
                file_type=2,
                binary=True,
                tokenize=False,
                kill_before_write=False,  # already batch-killed
            )
            if proc.returncode != 0:
                report.ok = False
                report.messages.append(
                    f"decb copy {unit.disk_name} failed: "
                    f"{(proc.stderr or proc.stdout or '').strip()}"
                )
            else:
                report.messages.append(
                    f"Copied {unit.disk_name} (ML type 2) → disk"
                )

    report.disk_path = disk
    free = decb_free(tools.decb, disk)
    dire = decb_dir(tools.decb, disk)
    free_text = free.stdout or free.stderr or ""
    dir_text = dire.stdout or dire.stderr or ""
    if free.stdout:
        report.messages.append(free.stdout.strip().splitlines()[-1])

    report.diagnostics = analyze_after_build(
        project,
        coco_text=coco_text,
        var_map=report.var_map,
        includes=report.includes,
        preprocess_warnings=preprocess_warnings,
        free_text=free_text,
        dir_text=dir_text,
        standalone_rels=standalone_rels,
    )
    hard = [d for d in report.diagnostics if d.severity == "error"]
    if hard:
        report.messages.append(f"{len(hard)} diagnostic error(s) — see Problems")
    return report


def run_project(tools: ToolPaths, project: Project) -> BuildReport:
    report = build_project(tools, project)
    if not report.ok:
        return report
    if not tools.xroar:
        report.ok = False
        report.messages.append("xroar not found")
        return report
    assert report.disk_path is not None
    cmd = build_xroar_command(
        tools.xroar,
        target=project.target,
        memory_kb=project.memory_kb,
        disk=report.disk_path,
        auto_run=project.auto_run,
        entry_name=entry_disk_name(project.entry),
        ao=getattr(project, "xroar_ao", None),
        ao_gain=getattr(project, "xroar_ao_gain", None),
    )
    report.xroar_cmd = cmd
    report.messages.append("XRoar: " + " ".join(cmd))
    try:
        launch_xroar(cmd, cwd=project.root)
        report.messages.append("XRoar launched")
    except OSError as exc:
        report.ok = False
        report.messages.append(f"Failed to launch XRoar: {exc}")
    return report


def disk_listing(tools: ToolPaths, project: Project) -> tuple[str, str]:
    """Return (dir_text, free_text)."""
    if not tools.decb or not project.disk_path:
        return ("(no decb or disk)", "")
    disk = project.disk_path
    if not disk.exists():
        return ("(disk not created yet — Build first)", "")
    d = decb_dir(tools.decb, disk)
    f = decb_free(tools.decb, disk)
    return (d.stdout or d.stderr or "", f.stdout or f.stderr or "")
