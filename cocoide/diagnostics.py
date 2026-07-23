"""CoCo-aware diagnostics (Problems panel).

Analyzes modern sources, preprocessor output, project target, and disk free space.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from cocoide.project import Project
from cocoide.tools import parse_granule_usage


Severity = str  # "error" | "warning" | "info"


@dataclass(order=True)
class Diagnostic:
    severity: str
    message: str
    code: str = ""
    path: str | None = None  # project-relative when possible
    line: int | None = None  # 1-based
    col: int | None = None

    def sort_key(self) -> tuple:
        rank = {"error": 0, "warning": 1, "info": 2}.get(self.severity, 9)
        return (rank, self.path or "", self.line or 0, self.message)

    def format(self) -> str:
        loc = ""
        if self.path and self.line:
            loc = f"{self.path}:{self.line}: "
        elif self.path:
            loc = f"{self.path}: "
        elif self.line:
            loc = f"line {self.line}: "
        sev = {"error": "error", "warning": "warn ", "info": "info "}.get(
            self.severity, self.severity
        )
        code = f"[{self.code}] " if self.code else ""
        return f"{sev}  {loc}{code}{self.message}"


# Super Extended / CoCo 3 (and related) keywords not on CoCo 1/2 DECB
COCO3_ONLY = {
    "hscreen", "hprint", "hstat", "hbuff", "hget", "hput", "hcolor", "hline",
    "hpaint", "hcircle", "hreset", "hset", "hdraw", "hcls",
    "palette", "rgb", "cmp", "attr", "width", "lpeek", "lpoke",
}

# Multi-word Super Extended statements (CoCo 3) — match as phrases, not lone tokens
# (avoids flagging normal ON … GOTO / variable names like ERR alone)
COCO3_PHRASES = (
    re.compile(r"\bon\s+err\s+goto\b", re.I),
    re.compile(r"\bon\s+brk\s+goto\b", re.I),
)

# Not in Disk Extended Color BASIC
NOT_DECB = {
    "while", "wend", "do", "loop", "repeat", "until", "select", "case",
    "function", "sub", "call", "local", "shared",
}

# DECB / ECB statement-ish keywords (for "used as variable" checks — light)
BASIC_KEYWORDS = {
    "for", "to", "step", "next", "if", "then", "else", "goto", "gosub", "return",
    "print", "input", "data", "read", "restore", "dim", "rem", "end", "stop",
    "run", "new", "list", "clear", "cls", "let", "on", "and", "or", "not",
    "pclear", "pmode", "screen", "color", "line", "pset", "preset", "circle",
    "paint", "get", "put", "play", "sound", "poke", "peek", "exec", "load",
    "loadm", "save", "savem", "open", "close", "width", "hscreen",
}

IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)(\$)?\b")
STRING_RE = re.compile(r'"(?:[^"]|"")*"')
LINE_RE = re.compile(r"^(\d+)\s*(.*)$")
GOTO_RE = re.compile(r"\bGO\s*TO\s+(\d+)\b", re.I)
GOSUB_RE = re.compile(r"\bGO\s*SUB\s+(\d+)\b", re.I)
PCLEAR_RE = re.compile(r"\bPCLEAR\s+(\d+)\b", re.I)
CLEAR_RE = re.compile(r"\bCLEAR\s+(\d+)\s*(?:,\s*(\d+))?", re.I)
POKE_RE = re.compile(r"\bPOKE\s+(\d+)\s*,", re.I)
EXEC_RE = re.compile(r"\bEXEC\s+(\d+)\b", re.I)


def _strip_strings(line: str) -> str:
    return STRING_RE.sub('""', line)


def _rel(path: Path, root: Path | None) -> str:
    if root:
        try:
            return str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            pass
    return str(path)


@dataclass
class AnalysisContext:
    project: Project
    coco_text: str = ""
    var_map: dict[str, str] = field(default_factory=dict)
    includes: list[str] = field(default_factory=list)
    preprocess_warnings: list[str] = field(default_factory=list)
    free_granules: int | None = None
    total_granules: int | None = None
    source_texts: dict[str, str] = field(default_factory=dict)  # rel path -> text
    standalone_rels: list[str] = field(default_factory=list)


def analyze(ctx: AnalysisContext) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    root = ctx.project.root

    for w in ctx.preprocess_warnings:
        diags.append(
            Diagnostic(severity="warning", code="PP000", message=w, path=None, line=None)
        )

    diags.extend(_analyze_var_map(ctx.var_map))
    diags.extend(_analyze_sources(ctx))
    if ctx.coco_text:
        diags.extend(_analyze_coco_text(ctx.coco_text, ctx.project))
    diags.extend(_analyze_disk(ctx))
    diags.extend(_analyze_orphans(ctx))

    diags.sort(key=lambda d: d.sort_key())
    return diags


def _analyze_var_map(var_map: dict[str, str]) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    if not var_map:
        return diags

    # Collision on short name (should be rare)
    inv: dict[str, list[str]] = {}
    for long, short in var_map.items():
        inv.setdefault(short.upper(), []).append(long)
    for short, longs in inv.items():
        if len(longs) > 1:
            diags.append(
                Diagnostic(
                    severity="error",
                    code="VAR001",
                    message=(
                        f"Short name {short} maps from multiple variables: "
                        f"{', '.join(longs)} (they would alias on the CoCo)"
                    ),
                )
            )

    # Educational: modern names sharing 2-letter prefix (preprocessor remapped)
    by_prefix: dict[str, list[str]] = {}
    for long in var_map:
        key = re.sub(r"[^A-Za-z0-9]", "", long)[:2].upper() or "?"
        by_prefix.setdefault(key, []).append(long)
    for prefix, longs in sorted(by_prefix.items()):
        if len(longs) < 2:
            continue
        mapped = ", ".join(f"{n}→{var_map[n]}" for n in sorted(longs))
        diags.append(
            Diagnostic(
                severity="info",
                code="VAR002",
                message=(
                    f"Names sharing prefix '{prefix}' would alias without remapping: {mapped}"
                ),
            )
        )

    # Long names summary (details live in Build log variable map)
    long_names = [n for n in var_map if len(n.rstrip("$")) > 2]
    if long_names:
        sample = ", ".join(
            f"{n}→{var_map[n]}" for n in sorted(long_names)[:6]
        )
        more = f" (+{len(long_names) - 6} more)" if len(long_names) > 6 else ""
        diags.append(
            Diagnostic(
                severity="info",
                code="VAR003",
                message=(
                    f"{len(long_names)} long name(s) remapped for 2-char CoCo rule: "
                    f"{sample}{more}"
                ),
            )
        )

    return diags


def _analyze_sources(ctx: AnalysisContext) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    target = (ctx.project.target or "coco3").lower()
    mem = ctx.project.memory_kb or 64

    for rel, text in ctx.source_texts.items():
        for lineno, raw in enumerate(text.splitlines(), start=1):
            code = _strip_strings(raw.split("'")[0])  # drop ' comments
            if not code.strip() or code.strip().startswith("@"):
                continue
            low = code.lower()

            # Unsupported modern constructs
            for bad in NOT_DECB:
                if re.search(rf"\b{bad}\b", low):
                    diags.append(
                        Diagnostic(
                            severity="error",
                            code="SYN001",
                            message=(
                                f"'{bad}' is not Disk Extended Color BASIC "
                                f"and is not translated yet"
                            ),
                            path=rel,
                            line=lineno,
                        )
                    )

            # CoCo 3-only on older targets
            if target in ("coco1", "coco2"):
                for kw in COCO3_ONLY:
                    if re.search(rf"\b{kw}\b", low):
                        diags.append(
                            Diagnostic(
                                severity="error",
                                code="TGT001",
                                message=(
                                    f"'{kw}' requires CoCo 3 / Super Extended BASIC "
                                    f"(project target is {target})"
                                ),
                                path=rel,
                                line=lineno,
                            )
                        )
                for phrase_re in COCO3_PHRASES:
                    m = phrase_re.search(code)
                    if m:
                        phrase = re.sub(r"\s+", " ", m.group(0).upper())
                        diags.append(
                            Diagnostic(
                                severity="error",
                                code="TGT002",
                                message=(
                                    f"'{phrase}' requires CoCo 3 / Super Extended BASIC "
                                    f"(project target is {target})"
                                ),
                                path=rel,
                                line=lineno,
                            )
                        )

            # PCLEAR
            m = PCLEAR_RE.search(code)
            if m:
                pages = int(m.group(1))
                if pages < 1 or pages > 8:
                    diags.append(
                        Diagnostic(
                            severity="warning",
                            code="MEM001",
                            message=f"PCLEAR {pages} is outside the usual 1–8 range",
                            path=rel,
                            line=lineno,
                        )
                    )
                else:
                    # Each page ~1.5K on CoCo; program start moves up
                    approx = pages * 1536
                    diags.append(
                        Diagnostic(
                            severity="info",
                            code="MEM002",
                            message=(
                                f"PCLEAR {pages} reserves ~{approx} bytes for graphics "
                                f"and raises the start of BASIC"
                            ),
                            path=rel,
                            line=lineno,
                        )
                    )
                    if target == "coco1" and mem <= 16 and pages > 2:
                        diags.append(
                            Diagnostic(
                                severity="warning",
                                code="MEM003",
                                message=(
                                    f"PCLEAR {pages} is tight on CoCo 1 with {mem}K"
                                ),
                                path=rel,
                                line=lineno,
                            )
                        )

            # CLEAR string[,himem]
            m = CLEAR_RE.search(code)
            if m:
                strspace = int(m.group(1))
                himem = int(m.group(2)) if m.group(2) else None
                if strspace > 2000:
                    diags.append(
                        Diagnostic(
                            severity="warning",
                            code="MEM004",
                            message=(
                                f"CLEAR {strspace} reserves a large string space "
                                f"— watch for ?OM ERROR"
                            ),
                            path=rel,
                            line=lineno,
                        )
                    )
                elif strspace < 50:
                    diags.append(
                        Diagnostic(
                            severity="info",
                            code="MEM005",
                            message=(
                                f"CLEAR {strspace}: small string space; long strings "
                                f"may cause ?OS ERROR"
                            ),
                            path=rel,
                            line=lineno,
                        )
                    )
                if himem is not None:
                    diags.append(
                        Diagnostic(
                            severity="info",
                            code="MEM006",
                            message=(
                                f"CLEAR sets high memory to {himem} "
                                f"(protects ML / leaves room above BASIC)"
                            ),
                            path=rel,
                            line=lineno,
                        )
                    )
                    if target in ("coco1", "coco2") and himem > mem * 1024 - 1:
                        diags.append(
                            Diagnostic(
                                severity="warning",
                                code="MEM007",
                                message=(
                                    f"High memory {himem} may exceed {mem}K target RAM"
                                ),
                                path=rel,
                                line=lineno,
                            )
                        )

            # Keyword used as assignment target (rough): IF FOO= where FOO is keyword
            am = re.match(
                r"^\s*(?:let\s+)?([A-Za-z_][A-Za-z0-9_]*\$?)\s*=",
                code,
                re.I,
            )
            if am:
                name = am.group(1)
                core = name.rstrip("$").lower()
                if core in BASIC_KEYWORDS:
                    diags.append(
                        Diagnostic(
                            severity="warning",
                            code="VAR004",
                            message=(
                                f"'{name}' looks like a BASIC keyword used as a variable "
                                f"— likely ?SN ERROR on the CoCo"
                            ),
                            path=rel,
                            line=lineno,
                        )
                    )

    return diags


def _analyze_coco_text(text: str, project: Project) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    lines: dict[int, str] = {}
    for raw in text.splitlines():
        m = LINE_RE.match(raw.strip())
        if not m:
            continue
        num = int(m.group(1))
        body = m.group(2)
        if num in lines:
            diags.append(
                Diagnostic(
                    severity="error",
                    code="LN001",
                    message=f"Duplicate line number {num} in generated BASIC",
                    path="build/" + Path(project.entry).stem + ".bas",
                    line=None,
                )
            )
        lines[num] = body

    if not lines:
        return diags

    known = set(lines)
    path = "build/" + Path(project.entry).stem + ".bas"

    for num, body in lines.items():
        code = _strip_strings(body)
        for m in GOTO_RE.finditer(code):
            tgt = int(m.group(1))
            if tgt not in known:
                diags.append(
                    Diagnostic(
                        severity="error",
                        code="LN002",
                        message=f"GOTO {tgt} targets a missing line",
                        path=path,
                        line=num,
                    )
                )
        for m in GOSUB_RE.finditer(code):
            tgt = int(m.group(1))
            if tgt not in known:
                diags.append(
                    Diagnostic(
                        severity="error",
                        code="LN003",
                        message=f"GOSUB {tgt} targets a missing line",
                        path=path,
                        line=num,
                    )
                )

        # High POKE/EXEC for small machines
        mem = project.memory_kb or 64
        ceiling = mem * 1024
        for m in POKE_RE.finditer(code):
            addr = int(m.group(1))
            if project.target in ("coco1", "coco2") and addr >= ceiling:
                diags.append(
                    Diagnostic(
                        severity="warning",
                        code="MEM008",
                        message=(
                            f"POKE {addr} is at or above {mem}K RAM end ({ceiling})"
                        ),
                        path=path,
                        line=num,
                    )
                )
        for m in EXEC_RE.finditer(code):
            addr = int(m.group(1))
            if project.target in ("coco1", "coco2") and addr >= ceiling:
                diags.append(
                    Diagnostic(
                        severity="warning",
                        code="MEM009",
                        message=f"EXEC {addr} may be outside {mem}K RAM",
                        path=path,
                        line=num,
                    )
                )

        # Generated RETURN lines are fine; flag RUN-time RG only if RETURN before any GOSUB
        # layout is handled by preprocessor — skip.

    # First executable should not be bare RETURN
    for num in sorted(lines):
        body = lines[num].strip().upper()
        if body.startswith("REM") or not body:
            continue
        if body == "RETURN" or body.startswith("RETURN "):
            diags.append(
                Diagnostic(
                    severity="error",
                    code="RG001",
                    message=(
                        f"Line {num} is RETURN as first executable — "
                        f"?RG ERROR on RUN (missing GOTO past procedures?)"
                    ),
                    path=path,
                    line=num,
                )
            )
        break

    return diags


def _analyze_disk(ctx: AnalysisContext) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    free, total = ctx.free_granules, ctx.total_granules
    if free is None:
        return diags
    if free <= 0:
        diags.append(
            Diagnostic(
                severity="error",
                code="DSK001",
                message="Disk has no free granules — cannot add programs",
                path=ctx.project.disk_image,
            )
        )
    elif free <= 2:
        diags.append(
            Diagnostic(
                severity="warning",
                code="DSK002",
                message=f"Disk almost full: {free} free granule(s)"
                + (f" of {total}" if total else ""),
                path=ctx.project.disk_image,
            )
        )
    elif total and free / total < 0.15:
        diags.append(
            Diagnostic(
                severity="info",
                code="DSK003",
                message=f"Disk free space low: {free} / {total} granules",
                path=ctx.project.disk_image,
            )
        )
    return diags


def _standalone_keys(ctx: AnalysisContext) -> set[str]:
    """Names/rels that count as standalone (project list, scan results, @standalone in text)."""
    from cocoide.preprocessor import parse_standalone_directive

    keys: set[str] = set()
    for s in ctx.project.standalone:
        keys.add(Path(s.split(":")[0]).name.lower())
        keys.add(s.lower().replace("\\", "/"))
    for rel in ctx.standalone_rels:
        keys.add(Path(rel).name.lower())
        keys.add(rel.lower().replace("\\", "/"))
    root = ctx.project.root
    if root and (root / "src").is_dir():
        for path in (root / "src").rglob("*.mbas"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if parse_standalone_directive(text)[0]:
                rel = _rel(path, root)
                keys.add(path.name.lower())
                keys.add(rel.lower().replace("\\", "/"))
    return keys


def _analyze_orphans(ctx: AnalysisContext) -> list[Diagnostic]:
    """Warn about .mbas under src/ not in the include graph and not standalone."""
    diags: list[Diagnostic] = []
    root = ctx.project.root
    if not root:
        return diags
    src = root / "src"
    if not src.is_dir():
        return diags

    included = {Path(p).name.lower() for p in ctx.includes}
    included.update(Path(p).as_posix().lower() for p in ctx.includes)
    entry_name = Path(ctx.project.entry).name.lower()
    included.add(entry_name)

    standalone = _standalone_keys(ctx)

    for path in sorted(src.rglob("*.mbas")):
        rel = _rel(path, root)
        name = path.name.lower()
        rel_l = rel.lower().replace("\\", "/")
        if name in included or rel_l in included:
            continue
        if name in standalone or rel_l in standalone:
            continue
        if rel_l == ctx.project.entry.lower().replace("\\", "/"):
            continue
        diags.append(
            Diagnostic(
                severity="warning",
                code="LNK001",
                message=(
                    f"'{rel}' is not in the entry include graph and not @standalone "
                    f"— will not be on the disk"
                ),
                path=rel,
            )
        )
    return diags


def collect_source_texts(
    project: Project,
    include_paths: list[str],
    standalone_rels: list[str] | None = None,
) -> dict[str, str]:
    """Load modern sources: entry includes + standalones."""
    out: dict[str, str] = {}
    root = project.root
    if not root:
        return out
    paths: list[Path] = []
    for inc in include_paths:
        p = root / inc
        if p.is_file():
            paths.append(p)
    for rel in standalone_rels or []:
        p = root / rel
        if p.is_file():
            paths.append(p)
    if project.entry_path and project.entry_path.is_file():
        paths.append(project.entry_path.resolve())
    seen: set[Path] = set()
    for p in paths:
        p = p.resolve()
        if p in seen:
            continue
        seen.add(p)
        try:
            out[_rel(p, root)] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return out


def analyze_after_build(
    project: Project,
    *,
    coco_text: str,
    var_map: dict[str, str],
    includes: list[str],
    preprocess_warnings: list[str],
    free_text: str = "",
    dir_text: str = "",
    standalone_rels: list[str] | None = None,
) -> list[Diagnostic]:
    free_n, total_n = parse_granule_usage(free_text, dir_text)
    sa = standalone_rels or []
    ctx = AnalysisContext(
        project=project,
        coco_text=coco_text,
        var_map=var_map,
        includes=includes,
        preprocess_warnings=preprocess_warnings,
        free_granules=free_n,
        total_granules=total_n,
        source_texts=collect_source_texts(project, includes, sa),
        standalone_rels=sa,
    )
    return analyze(ctx)
