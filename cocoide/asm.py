"""Assemble 6809 sources with LWTOOLS ``lwasm`` into DECB LOADM .BIN files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from cocoide.tools import ToolPaths, decb_copy_to_disk, normalize_coco_name, run_cmd


@dataclass
class AsmUnit:
    source: Path
    rel: str
    disk_name: str  # e.g. SPRITES.BIN
    output_bin: Path


@dataclass
class AsmResult:
    ok: bool
    messages: list[str] = field(default_factory=list)
    bins: list[Path] = field(default_factory=list)


def discover_asm_sources(root: Path, explicit: list[str] | None = None) -> list[AsmUnit]:
    """Find ``src/**/*.asm`` plus any paths listed in project.asm_sources."""
    units: list[AsmUnit] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        path = path.resolve()
        if path in seen or not path.is_file():
            return
        if path.suffix.lower() not in (".asm", ".a", ".s"):
            return
        seen.add(path)
        try:
            rel = str(path.relative_to(root.resolve()))
        except ValueError:
            rel = path.name
        stem = re.sub(r"[^A-Za-z0-9]", "", path.stem.upper())[:8] or "CODE"
        disk_name = f"{stem}.BIN"
        out = root / "build" / f"{path.stem}.bin"
        units.append(AsmUnit(source=path, rel=rel, disk_name=disk_name, output_bin=out))

    for entry in explicit or []:
        for c in (root / entry, root / "src" / entry, root / "src" / Path(entry).name):
            if c.is_file():
                add(c)
                break

    src = root / "src"
    if src.is_dir():
        for path in sorted(src.rglob("*")):
            if path.suffix.lower() not in (".asm", ".a", ".s"):
                continue
            # Skip disassembly dumps / imports — not project ML sources
            parts = {p.lower() for p in path.parts}
            if "imported" in parts:
                continue
            add(path)

    return units


def assemble_unit(tools: ToolPaths, unit: AsmUnit, *, cpu6809: bool = True) -> AsmResult:
    result = AsmResult(ok=True)
    if not tools.lwasm:
        result.ok = False
        result.messages.append("lwasm not found — install LWTOOLS")
        return result

    unit.output_bin.parent.mkdir(parents=True, exist_ok=True)
    args = [
        tools.lwasm,
        "-9" if cpu6809 else "-3",
        "--format=decb",
        "-o",
        str(unit.output_bin),
        str(unit.source),
    ]
    # Also emit a listing for debugging
    list_path = unit.output_bin.with_suffix(".lst")
    args.extend(["-l", str(list_path)])

    proc = run_cmd(args, cwd=unit.source.parent)
    if proc.returncode != 0:
        result.ok = False
        err = (proc.stderr or proc.stdout or "lwasm failed").strip()
        result.messages.append(f"lwasm {unit.rel}:\n{err}")
        return result

    if not unit.output_bin.is_file():
        result.ok = False
        result.messages.append(f"lwasm produced no output for {unit.rel}")
        return result

    result.bins.append(unit.output_bin)
    result.messages.append(
        f"Assembled {unit.rel} → {unit.output_bin.name} ({unit.output_bin.stat().st_size} bytes) "
        f"disk as {unit.disk_name}"
    )
    return result


def assemble_project(
    tools: ToolPaths,
    root: Path,
    explicit: list[str] | None = None,
) -> tuple[AsmResult, list[AsmUnit]]:
    units = discover_asm_sources(root, explicit)
    combined = AsmResult(ok=True)
    if not units:
        combined.messages.append("No .asm sources under src/")
        return combined, units

    for unit in units:
        one = assemble_unit(tools, unit)
        combined.messages.extend(one.messages)
        combined.bins.extend(one.bins)
        if not one.ok:
            combined.ok = False
    return combined, units


def copy_bins_to_disk(
    tools: ToolPaths,
    disk: Path,
    units: list[AsmUnit],
) -> AsmResult:
    result = AsmResult(ok=True)
    if not tools.decb:
        result.ok = False
        result.messages.append("decb not found")
        return result
    for unit in units:
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
            kill_before_write=True,
        )
        if proc.returncode != 0:
            result.ok = False
            result.messages.append(
                f"decb copy {unit.disk_name} failed: "
                f"{(proc.stderr or proc.stdout or '').strip()}"
            )
        else:
            result.messages.append(f"Copied {unit.disk_name} (ML type 2) → disk")
            result.bins.append(unit.output_bin)
    return result
