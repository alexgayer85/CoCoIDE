"""Modern BASIC → CoCo DECB text.

Option C: entry + @include → one linked program (read-only artifact).

Procedure calls expand to parameter assignments + GOSUB (global, not stacked):

    Greet("WORLD")
  →
    WH$="WORLD"
    GOSUB <Greet>
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


DIRECTIVE_RE = re.compile(r"^@(\w+)(?:\s+(.*))?$")
PROC_RE = re.compile(r"^procedure\s+(\w+)\s*\(([^)]*)\)\s*$", re.I)
END_RE = re.compile(r"^end\s*$", re.I)
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\$?")
CALL_RE = re.compile(r"^([A-Za-z_]\w*)\s*\((.*)\)\s*$")
LABEL_RE = re.compile(r"^([A-Za-z_]\w*)\s*:\s*(.*)$")

KEYWORDS = {
    "cls", "print", "input", "goto", "gosub", "return", "for", "to", "step",
    "next", "if", "then", "else", "and", "or", "not", "dim", "data", "read",
    "restore", "rem", "end", "stop", "run", "new", "list", "clear", "pclear",
    "pmode", "screen", "color", "line", "pset", "preset", "circle", "paint",
    "get", "put", "play", "sound", "poke", "peek", "exec", "load", "loadm",
    "save", "savem", "open", "close", "eof", "write", "width", "hscreen",
    "hprint", "rgb", "palette", "on", "off", "motor", "audio", "inkey",
    "string", "left", "right", "mid", "chr", "asc", "val", "str", "len",
    "abs", "int", "rnd", "sin", "cos", "tan", "atn", "log", "exp", "sqr",
    "sgn", "timer", "while", "wend", "procedure", "true", "false",
}

# Not in Disk Extended Color BASIC — warn if seen as statements/keywords.
UNSUPPORTED_DECB = {"while", "wend", "do", "loop", "repeat", "until", "select", "case"}


@dataclass
class PreprocessResult:
    coco_text: str
    var_map: dict[str, str] = field(default_factory=dict)
    includes: list[str] = field(default_factory=list)
    start: int = 100
    step: int = 10
    warnings: list[str] = field(default_factory=list)
    proc_params: dict[str, list[str]] = field(default_factory=dict)
    disk_name: str | None = None  # optional DECB name for standalone units


@dataclass
class StandaloneUnit:
    """A separate modern program packaged to its own DECB file."""

    source: Path
    disk_name: str  # e.g. UTIL.BAS
    rel: str  # project-relative path


def parse_standalone_directive(text: str) -> tuple[bool, str | None]:
    """Return (is_standalone, optional explicit disk name).

    Forms::

        @standalone
        @standalone UTIL.BAS
        @standalone "util.bas"
    """
    for line in text.splitlines():
        m = DIRECTIVE_RE.match(line.strip())
        if not m or m.group(1).lower() != "standalone":
            continue
        arg = (m.group(2) or "").strip().strip("\"'")
        return True, (arg or None)
    return False, None


def coco_name_from_source(path: Path, explicit: str | None = None) -> str:
    """DECB 8.3 name for a standalone source."""
    if explicit:
        name = explicit.upper().replace("\\", "/").split("/")[-1]
        if "." not in name:
            name = f"{name[:8]}.BAS"
        stem, _, ext = name.partition(".")
        stem = re.sub(r"[^A-Z0-9]", "", stem)[:8] or "FILE"
        ext = re.sub(r"[^A-Z0-9]", "", ext)[:3] or "BAS"
        return f"{stem}.{ext}"
    stem = re.sub(r"[^A-Za-z0-9]", "", path.stem.upper())[:8] or "FILE"
    return f"{stem}.BAS"


def discover_standalones(root: Path, project_standalone: list[str] | None = None) -> list[StandaloneUnit]:
    """Find standalone sources from @standalone directives and project.standalone."""
    units: list[StandaloneUnit] = []
    seen: set[Path] = set()
    project_standalone = project_standalone or []

    def add(path: Path, explicit: str | None = None) -> None:
        path = path.resolve()
        if path in seen or not path.is_file():
            return
        seen.add(path)
        try:
            rel = str(path.relative_to(root.resolve()))
        except ValueError:
            rel = path.name
        if explicit is None:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            is_sa, explicit = parse_standalone_directive(text)
            if not is_sa and explicit is None:
                # project list entry without @standalone in file is still standalone
                pass
        units.append(
            StandaloneUnit(
                source=path,
                disk_name=coco_name_from_source(path, explicit),
                rel=rel,
            )
        )

    # Explicit project list (paths relative to root or src/)
    for entry in project_standalone:
        entry = entry.strip()
        if not entry:
            continue
        # optional "path:NAME.BAS" form
        explicit_name = None
        if ":" in entry and not entry[1:2] == "\\":  # avoid Windows drive
            # only split on last colon if looks like name.bas
            left, right = entry.rsplit(":", 1)
            if "." in right or right.upper().endswith("BAS"):
                entry, explicit_name = left, right
        candidates = [
            root / entry,
            root / "src" / entry,
            root / "src" / Path(entry).name,
        ]
        for c in candidates:
            if c.is_file():
                add(c, explicit_name)
                break
        else:
            # missing — still record as unresolved later via diagnostics
            pass

    # Scan src/**/*.mbas for @standalone
    src = root / "src"
    if src.is_dir():
        for path in sorted(src.rglob("*.mbas")):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            is_sa, explicit = parse_standalone_directive(text)
            if is_sa:
                add(path, explicit)

    return units


def _resolve_include(from_file: Path, arg: str, root: Path) -> Path:
    arg = arg.strip().strip("\"'")
    for c in (
        from_file.parent / arg,
        root / arg,
        root / "src" / arg,
        root / "src" / Path(arg).name,
    ):
        if c.is_file():
            return c.resolve()
    return (from_file.parent / arg).resolve()


def _collect_sources(entry: Path, root: Path) -> tuple[list[Path], list[str]]:
    ordered: list[Path] = []
    warnings: list[str] = []
    seen: set[Path] = set()
    stack: set[Path] = set()

    def visit(path: Path) -> None:
        path = path.resolve()
        if path in stack:
            warnings.append(f"Circular include involving {path.name}")
            return
        if path in seen:
            return
        if not path.is_file():
            warnings.append(f"Missing include: {path}")
            return
        stack.add(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            m = DIRECTIVE_RE.match(line.strip())
            if m and m.group(1).lower() == "include":
                visit(_resolve_include(path, m.group(2) or "", root))
        stack.discard(path)
        seen.add(path)
        ordered.append(path)

    visit(entry.resolve())
    return ordered, warnings


def _is_rem(s: str) -> bool:
    u = s.strip().upper()
    return u.startswith("REM ") or u == "REM"


def split_args(argstr: str) -> list[str]:
    """Split procedure-call arguments on commas, respecting quotes."""
    argstr = argstr.strip()
    if not argstr:
        return []
    args: list[str] = []
    cur: list[str] = []
    in_str = False
    depth = 0
    for ch in argstr:
        if ch == '"':
            in_str = not in_str
            cur.append(ch)
            continue
        if not in_str:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            elif ch == "," and depth == 0:
                piece = "".join(cur).strip()
                if piece:
                    args.append(piece)
                cur = []
                continue
        cur.append(ch)
    piece = "".join(cur).strip()
    if piece:
        args.append(piece)
    return args


def preprocess_project(entry: Path, root: Path) -> PreprocessResult:
    files, warnings = _collect_sources(entry, root)
    start, step = 100, 10
    var_map: dict[str, str] = {}
    used_short: set[str] = set()
    include_names: list[str] = []
    proc_params: dict[str, list[str]] = {}  # lower name -> param names as written

    if files:
        for line in files[0].read_text(encoding="utf-8", errors="replace").splitlines():
            m = DIRECTIVE_RE.match(line.strip())
            if not m:
                continue
            name, arg = m.group(1).lower(), (m.group(2) or "").strip()
            if name == "start" and arg.isdigit():
                start = int(arg)
            elif name == "step" and arg.isdigit():
                step = int(arg)

    procs: dict[str, list[str]] = {}  # original case name -> body lines
    proc_order: list[str] = []
    top_level: list[str] = []
    current: str | None = None

    for fpath in files:
        try:
            include_names.append(str(fpath.relative_to(root.resolve())))
        except ValueError:
            include_names.append(fpath.name)

        for line in fpath.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s:
                continue
            if DIRECTIVE_RE.match(s):
                continue
            if s.startswith("'"):
                rem = f"REM {s[1:].strip()}"
                (procs.setdefault(current, []) if current else top_level).append(rem)
                continue
            if s.lower().startswith("rem "):
                rem = f"REM {s[4:].strip()}"
                (procs.setdefault(current, []) if current else top_level).append(rem)
                continue

            # label: optional statement
            lm = LABEL_RE.match(s)
            if lm and lm.group(1).lower() not in KEYWORDS:
                label, rest = lm.group(1), lm.group(2).strip()
                target_list = procs.setdefault(current, []) if current else top_level
                target_list.append(f"<<LABEL {label}>>")
                if rest:
                    target_list.append(rest)
                continue

            pm = PROC_RE.match(s)
            if pm:
                current = pm.group(1)
                if current not in procs:
                    procs[current] = []
                    proc_order.append(current)
                params = [p.strip() for p in (pm.group(2) or "").split(",") if p.strip()]
                # validate param names
                clean: list[str] = []
                for p in params:
                    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*\$?$", p):
                        warnings.append(f"Procedure {current}: bad parameter '{p}'")
                    else:
                        clean.append(p)
                proc_params[current.lower()] = clean
                continue
            if END_RE.match(s) and current:
                current = None
                continue

            if current:
                procs.setdefault(current, []).append(s)
            else:
                top_level.append(s)

    def alloc_short(name: str) -> str:
        key = name.rstrip("$")
        is_str = name.endswith("$")
        low = key.lower()
        if low in KEYWORDS:
            return key.upper() + ("$" if is_str else "")
        if low in var_map:
            return var_map[low] + ("$" if is_str else "")
        base = re.sub(r"[^A-Za-z0-9]", "", key).upper()[:2] or "V"
        if len(base) < 2:
            base = (base + "X")[:2]
        cand = base
        n = 0
        while cand in used_short:
            n += 1
            cand = f"{base[0]}{n % 10}"
        used_short.add(cand)
        var_map[low] = cand
        return cand + ("$" if is_str else "")

    # Reserve parameter short names early so bodies and call sites agree.
    for _pname, params in proc_params.items():
        for p in params:
            alloc_short(p)

    def rewrite_expr(expr: str) -> str:
        """Rewrite identifiers; leave strings and <<placeholders>> alone."""
        # Protect preprocessor placeholders from variable renaming
        holders: list[str] = []

        def stash(m: re.Match[str]) -> str:
            holders.append(m.group(0))
            return f"__PH{len(holders) - 1}__"

        expr = re.sub(r"<<[^>]+>>", stash, expr)
        parts = re.split(r'(".*?")', expr)
        out: list[str] = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                out.append(part)
                continue

            def repl(m: re.Match[str]) -> str:
                tok = m.group(0)
                if tok.startswith("__PH") and tok.endswith("__"):
                    return tok
                core = tok.rstrip("$").lower()
                if core in KEYWORDS:
                    return tok[:-1].upper() + "$" if tok.endswith("$") else tok.upper()
                return alloc_short(tok)

            out.append(IDENT_RE.sub(repl, part))
        text = "".join(out)
        for i, h in enumerate(holders):
            text = text.replace(f"__PH{i}__", h)
        return text

    def expand_stmt(s: str) -> list[str]:
        """Expand one modern statement into one or more CoCo statements (no line #s)."""
        if _is_rem(s) or s.startswith("<<LABEL "):
            return [s]

        # Procedure call as full statement
        call = CALL_RE.match(s)
        if call and call.group(1).lower() not in KEYWORDS:
            cname = call.group(1)
            args = split_args(call.group(2))
            params = proc_params.get(cname.lower())
            out: list[str] = []
            if params is None:
                warnings.append(f"Call to unknown procedure: {cname}")
                out.append(f"GOSUB <<{cname}>>")
                return out
            if len(args) != len(params):
                warnings.append(
                    f"{cname}(): expected {len(params)} argument(s), got {len(args)}"
                )
            for param, arg in zip(params, args):
                lhs = alloc_short(param)
                rhs = rewrite_expr(arg)
                out.append(f"{lhs}={rhs}")
            out.append(f"GOSUB <<{cname}>>")
            return out

        low = s.lower()
        for bad in UNSUPPORTED_DECB:
            if re.search(rf"\b{bad}\b", low):
                warnings.append(
                    f"'{bad}' is not Disk Extended Color BASIC — will not run on CoCo"
                )
                break

        # Labels: CoCo prefers "IF … THEN 1230" over "IF … THEN GOTO 1230"
        # (THEN GOTO can confuse some ROM paths; bare GOTO stays for non-THEN jumps.)
        def patch_goto_labels(text: str) -> str:
            # THEN GOTO label/number → THEN <<L:…>> or THEN n
            def then_go(m: re.Match[str]) -> str:
                target = m.group(1)
                if target.isdigit():
                    return f"THEN {target}"
                return f"THEN <<L:{target}>>"

            text = re.sub(
                r"\bthen\s+goto\s+([A-Za-z_]\w*|\d+)",
                then_go,
                text,
                flags=re.I,
            )

            def bare_go(m: re.Match[str]) -> str:
                target = m.group(1)
                if target.isdigit():
                    return f"GOTO {target}"
                return f"GOTO <<L:{target}>>"

            text = re.sub(
                r"\bgoto\s+([A-Za-z_]\w*|\d+)",
                bare_go,
                text,
                flags=re.I,
            )
            return text

        s2 = patch_goto_labels(s)

        # Expand "THEN Proc(args)" / multi-statement lines ending with Proc()
        # into separate assign+GOSUB lines where possible.
        then_call = re.search(
            r"(?i)^(.*\bthen\s+)([A-Za-z_]\w*)\s*\((.*)\)\s*$",
            s2,
        )
        if then_call and then_call.group(2).lower() not in KEYWORDS:
            cname = then_call.group(2)
            prefix = then_call.group(1)
            args = split_args(then_call.group(3))
            params = proc_params.get(cname.lower())
            if params is None:
                warnings.append(f"Call to unknown procedure: {cname}")
                return [rewrite_expr(f"{prefix}GOSUB <<{cname}>>")]
            # Keep GOSUB on the same IF line (colon chain) so it only runs when true
            parts: list[str] = []
            for param, arg in zip(params, args):
                parts.append(f"{alloc_short(param)}={rewrite_expr(arg)}")
            parts.append(f"GOSUB <<{cname}>>")
            return [rewrite_expr(prefix) + ":".join(parts)]

        return [rewrite_expr(s2)]

    def expand_block(stmts: list[str]) -> list[str]:
        out: list[str] = []
        for st in stmts:
            out.extend(expand_stmt(st))
        return out

    procs_rw = {k: expand_block(v) for k, v in procs.items()}
    top_rw = expand_block(top_level)
    top_code = [x for x in top_rw if not _is_rem(x) and not x.startswith("<<LABEL ")]
    top_rems = [x for x in top_rw if _is_rem(x)]
    # labels in top_level kept inside top_rw order — re-expand carefully
    # Rebuild top keeping label markers and code order
    top_seq = [x for x in top_rw if not _is_rem(x)]

    # Layout:
    #   header / rems
    #   GOTO boot
    #   procedures… RETURN
    #   boot: entry
    #   END
    lines: list[str] = []
    ln = start
    proc_line: dict[str, int] = {}
    label_line: dict[str, int] = {}
    boot_line: int | None = None

    lines.append(f"{ln} REM GENERATED BY COCOIDE - READ ONLY ARTIFACT")
    ln += step
    for rem in top_rems:
        lines.append(f"{ln} {rem}")
        ln += step

    # Jump past procedures into boot. Main is entered with GOTO (not GOSUB)
    # so that CLEAR at the start of Main is legal; CLEAR would wipe a GOSUB stack.
    if procs_rw:
        lines.append(f"{ln} GOTO <<BOOT>>")
        ln += step

    def emit_body_rows(body: list[str], *, is_proc: bool, pname: str = "") -> None:
        """Emit statements; bind labels to the *next executable* line (not REM)."""
        nonlocal ln, entry_set
        pending: list[str] = []
        for row in body:
            if row.startswith("<<LABEL "):
                lab = row[len("<<LABEL ") :].rstrip(">").strip()
                pending.append(lab.lower())
                continue
            # Optional debug rem for labels (does not receive GOTO)
            if pending:
                lines.append(
                    f"{ln} REM LABEL {','.join(p.upper() for p in pending)}"
                )
                ln += step
            for lab in pending:
                # Point at this statement's line number
                label_line[lab] = ln
            pending = []
            if is_proc and not entry_set and not _is_rem(row):
                proc_line[pname.lower()] = ln
                entry_set = True
            lines.append(f"{ln} {row}")
            ln += step
        # Trailing labels with no following code → point at RETURN (added by caller)
        for lab in pending:
            label_line[lab] = ln

    for pname in proc_order:
        body = procs_rw.get(pname, [])
        lines.append(f"{ln} REM PROC {pname.upper()}")
        ln += step
        entry_set = False
        emit_body_rows(body, is_proc=True, pname=pname)
        if not entry_set:
            proc_line[pname.lower()] = ln
        # Main is the program entry (GOTO), so it must END — not RETURN.
        if pname.lower() == "main":
            lines.append(f"{ln} END")
        else:
            lines.append(f"{ln} RETURN")
        ln += step

    boot_line = ln
    lines.append(f"{ln} REM ENTRY")
    ln += step

    if top_seq:
        entry_set = True  # unused
        emit_body_rows(top_seq, is_proc=False)
        lines.append(f"{ln} END")
        ln += step
    elif "main" in {k.lower() for k in proc_line}:
        # GOTO Main (not GOSUB) so CLEAR inside Main is safe
        lines.append(f"{ln} GOTO <<Main>>")
        ln += step
    else:
        lines.append(f"{ln} REM NO ENTRY POINT")
        ln += step
        warnings.append("No Main procedure and no top-level code")
        lines.append(f"{ln} END")
        ln += step

    def resolve_placeholders(text: str) -> str:
        def boot(_m: re.Match[str] | None = None) -> str:
            if boot_line is None:
                warnings.append("Internal error: missing boot line")
                return str(start)
            return str(boot_line)

        text = re.sub(r"<<BOOT>>", lambda _m: boot(), text)

        def patch(m: re.Match[str]) -> str:
            name = m.group(1)
            if name.upper() == "BOOT":
                return boot()
            if name.startswith("L:") or name.startswith("l:"):
                lab = name[2:]
                target = label_line.get(lab.lower())
                if target is None:
                    warnings.append(f"Unknown label: {lab}")
                    # Avoid GOTO 0 (?UL ERROR); jump to program end stub
                    return str(start)
                return str(target)
            target = proc_line.get(name.lower())
            if target is None:
                warnings.append(f"Unknown procedure: {name}")
                return str(start)
            return str(target)

        return re.sub(r"<<([A-Za-z_:][A-Za-z0-9_:]*)>>", patch, text)

    final: list[str] = []
    for row in lines:
        row = resolve_placeholders(row)
        m = re.match(r"^(\d+\s+)(.*)$", row)
        if not m:
            final.append(row)
            continue
        num, rest = m.group(1), m.group(2)
        if rest.upper().startswith("REM"):
            final.append(row)
            continue
        parts = re.split(r'(".*?")', rest)
        rebuilt = []
        for i, p in enumerate(parts):
            rebuilt.append(p if i % 2 == 1 else p.upper())
        final.append(num + "".join(rebuilt))

    # Deduplicate warnings while preserving order
    seen_w: set[str] = set()
    uniq_w: list[str] = []
    for w in warnings:
        if w not in seen_w:
            seen_w.add(w)
            uniq_w.append(w)

    return PreprocessResult(
        coco_text="\n".join(final) + "\n",
        var_map=var_map,
        includes=include_names,
        start=start,
        step=step,
        warnings=uniq_w,
        proc_params=proc_params,
    )


def write_artifact(result: PreprocessResult, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(result.coco_text, encoding="utf-8")
