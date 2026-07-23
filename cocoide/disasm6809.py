"""Best-effort MC6809 disassembler + CoCo DECB LOADM (.BIN) parser.

This is **not** a full interactive reverse-engineering suite. It produces
editable assembly aimed at lwasm re-assembly. Data-as-code still needs
hand cleanup; install f9dasm on PATH for higher quality when available.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DecbSegment:
    load: int
    data: bytes


@dataclass
class DecbBinary:
    segments: list[DecbSegment] = field(default_factory=list)
    exec_addr: int | None = None
    raw_fallback: bytes = b""

    @property
    def is_decb(self) -> bool:
        return bool(self.segments)


def parse_decb_bin(data: bytes) -> DecbBinary:
    """Parse CoCo LOADM / DECB .BIN (preamble 00 / postamble FF)."""
    out = DecbBinary()
    if not data:
        return out
    if data[0] not in (0x00, 0xFF):
        out.raw_fallback = data
        return out

    i = 0
    n = len(data)
    try:
        while i < n:
            tag = data[i]
            i += 1
            if tag == 0x00:
                if i + 4 > n:
                    break
                length = (data[i] << 8) | data[i + 1]
                load = (data[i + 2] << 8) | data[i + 3]
                i += 4
                chunk = data[i : i + length]
                i += length
                out.segments.append(DecbSegment(load=load, data=chunk))
            elif tag == 0xFF:
                if i + 4 > n:
                    break
                _ln = (data[i] << 8) | data[i + 1]
                exec_a = (data[i + 2] << 8) | data[i + 3]
                i += 4
                out.exec_addr = exec_a
                break
            else:
                out.segments.clear()
                out.raw_fallback = data
                out.exec_addr = None
                return out
    except Exception:
        out.segments.clear()
        out.raw_fallback = data
    if not out.segments and not out.raw_fallback:
        out.raw_fallback = data
    return out


# ---------------------------------------------------------------------------
# Opcode map: opcode -> (mnemonic, mode)
# mode: inh, imm8, imm16, dir, ext, idx, rel8, rel16
# ---------------------------------------------------------------------------

_OP: dict[int, tuple[str, str]] = {}


def _build_table() -> None:
    # Inherent / relative / simple
    for op, m in (
        (0x12, ("NOP", "inh")),
        (0x13, ("SYNC", "inh")),
        (0x19, ("DAA", "inh")),
        (0x1D, ("SEX", "inh")),
        (0x39, ("RTS", "inh")),
        (0x3A, ("ABX", "inh")),
        (0x3B, ("RTI", "inh")),
        (0x3C, ("CWAI", "imm8")),
        (0x3D, ("MUL", "inh")),
        (0x3F, ("SWI", "inh")),
        (0x16, ("LBRA", "rel16")),
        (0x17, ("LBSR", "rel16")),
        # A inherent
        (0x40, ("NEGA", "inh")),
        (0x43, ("COMA", "inh")),
        (0x44, ("LSRA", "inh")),
        (0x46, ("RORA", "inh")),
        (0x47, ("ASRA", "inh")),
        (0x48, ("ASLA", "inh")),
        (0x49, ("ROLA", "inh")),
        (0x4A, ("DECA", "inh")),
        (0x4C, ("INCA", "inh")),
        (0x4D, ("TSTA", "inh")),
        (0x4F, ("CLRA", "inh")),
        # B inherent
        (0x50, ("NEGB", "inh")),
        (0x53, ("COMB", "inh")),
        (0x54, ("LSRB", "inh")),
        (0x56, ("RORB", "inh")),
        (0x57, ("ASRB", "inh")),
        (0x58, ("ASLB", "inh")),
        (0x59, ("ROLB", "inh")),
        (0x5A, ("DECB", "inh")),
        (0x5C, ("INCB", "inh")),
        (0x5D, ("TSTB", "inh")),
        (0x5F, ("CLRB", "inh")),
        (0x1C, ("ANDCC", "imm8")),
        (0x1A, ("ORCC", "imm8")),
        (0x1E, ("EXG", "imm8")),
        (0x1F, ("TFR", "imm8")),
        (0x30, ("LEAX", "idx")),
        (0x31, ("LEAY", "idx")),
        (0x32, ("LEAS", "idx")),
        (0x33, ("LEAU", "idx")),
        (0x34, ("PSHS", "imm8")),
        (0x35, ("PULS", "imm8")),
        (0x36, ("PSHU", "imm8")),
        (0x37, ("PULU", "imm8")),
        (0x20, ("BRA", "rel8")),
        (0x21, ("BRN", "rel8")),
        (0x22, ("BHI", "rel8")),
        (0x23, ("BLS", "rel8")),
        (0x24, ("BCC", "rel8")),
        (0x25, ("BCS", "rel8")),
        (0x26, ("BNE", "rel8")),
        (0x27, ("BEQ", "rel8")),
        (0x28, ("BVC", "rel8")),
        (0x29, ("BVS", "rel8")),
        (0x2A, ("BPL", "rel8")),
        (0x2B, ("BMI", "rel8")),
        (0x2C, ("BGE", "rel8")),
        (0x2D, ("BLT", "rel8")),
        (0x2E, ("BGT", "rel8")),
        (0x2F, ("BLE", "rel8")),
        (0x8D, ("BSR", "rel8")),
    ):
        _OP[op] = m

    # Memory RMW: dir (0x0x), idx (0x6x), ext (0x7x)
    for low, name in (
        (0x00, "NEG"),
        (0x03, "COM"),
        (0x04, "LSR"),
        (0x06, "ROR"),
        (0x07, "ASR"),
        (0x08, "ASL"),
        (0x09, "ROL"),
        (0x0A, "DEC"),
        (0x0C, "INC"),
        (0x0D, "TST"),
        (0x0E, "JMP"),
        (0x0F, "CLR"),
    ):
        _OP[0x00 + low] = (name, "dir")
        _OP[0x60 + low] = (name, "idx")
        _OP[0x70 + low] = (name, "ext")

    # A/B arithmetic / logic
    for base, n in (
        (0x80, "SUBA"),
        (0xC0, "SUBB"),
        (0x81, "CMPA"),
        (0xC1, "CMPB"),
        (0x82, "SBCA"),
        (0xC2, "SBCB"),
        (0x84, "ANDA"),
        (0xC4, "ANDB"),
        (0x85, "BITA"),
        (0xC5, "BITB"),
        (0x86, "LDA"),
        (0xC6, "LDB"),
        (0x88, "EORA"),
        (0xC8, "EORB"),
        (0x89, "ADCA"),
        (0xC9, "ADCB"),
        (0x8A, "ORA"),
        (0xCA, "ORB"),
        (0x8B, "ADDA"),
        (0xCB, "ADDB"),
    ):
        _OP[base] = (n, "imm8")
        _OP[base + 0x10] = (n, "dir")
        _OP[base + 0x20] = (n, "idx")
        _OP[base + 0x30] = (n, "ext")

    _OP[0x97] = ("STA", "dir")
    _OP[0xA7] = ("STA", "idx")
    _OP[0xB7] = ("STA", "ext")
    _OP[0xD7] = ("STB", "dir")
    _OP[0xE7] = ("STB", "idx")
    _OP[0xF7] = ("STB", "ext")

    for base, n, imm in (
        (0x8C, "CMPX", "imm16"),
        (0x8E, "LDX", "imm16"),
        (0xCC, "LDD", "imm16"),
        (0xCE, "LDU", "imm16"),
        (0x83, "SUBD", "imm16"),
        (0xC3, "ADDD", "imm16"),
    ):
        _OP[base] = (n, imm)
        _OP[base + 0x10] = (n, "dir")
        _OP[base + 0x20] = (n, "idx")
        _OP[base + 0x30] = (n, "ext")

    _OP[0x9F] = ("STX", "dir")
    _OP[0xAF] = ("STX", "idx")
    _OP[0xBF] = ("STX", "ext")
    _OP[0xDD] = ("STD", "dir")
    _OP[0xED] = ("STD", "idx")
    _OP[0xFD] = ("STD", "ext")
    _OP[0xDF] = ("STU", "dir")
    _OP[0xEF] = ("STU", "idx")
    _OP[0xFF] = ("STU", "ext")

    _OP[0x9D] = ("JSR", "dir")
    _OP[0xAD] = ("JSR", "idx")
    _OP[0xBD] = ("JSR", "ext")


_build_table()

_PAGE1 = {
    0x21: ("LBRN", "rel16"),
    0x22: ("LBHI", "rel16"),
    0x23: ("LBLS", "rel16"),
    0x24: ("LBCC", "rel16"),
    0x25: ("LBCS", "rel16"),
    0x26: ("LBNE", "rel16"),
    0x27: ("LBEQ", "rel16"),
    0x2C: ("LBGE", "rel16"),
    0x2D: ("LBLT", "rel16"),
    0x2E: ("LBGT", "rel16"),
    0x2F: ("LBLE", "rel16"),
    0x3F: ("SWI2", "inh"),
    0x83: ("CMPD", "imm16"),
    0x8C: ("CMPY", "imm16"),
    0x8E: ("LDY", "imm16"),
    0x93: ("CMPD", "dir"),
    0x9C: ("CMPY", "dir"),
    0x9E: ("LDY", "dir"),
    0x9F: ("STY", "dir"),
    0xA3: ("CMPD", "idx"),
    0xAC: ("CMPY", "idx"),
    0xAE: ("LDY", "idx"),
    0xAF: ("STY", "idx"),
    0xB3: ("CMPD", "ext"),
    0xBC: ("CMPY", "ext"),
    0xBE: ("LDY", "ext"),
    0xBF: ("STY", "ext"),
    0xCE: ("LDS", "imm16"),
    0xDE: ("LDS", "dir"),
    0xDF: ("STS", "dir"),
    0xEE: ("LDS", "idx"),
    0xEF: ("STS", "idx"),
    0xFE: ("LDS", "ext"),
    0xFF: ("STS", "ext"),
    0x8D: ("LBSR", "rel16"),
}

_PAGE2 = {
    0x3F: ("SWI3", "inh"),
    0x83: ("CMPU", "imm16"),
    0x8C: ("CMPS", "imm16"),
    0x93: ("CMPU", "dir"),
    0x9C: ("CMPS", "dir"),
    0xA3: ("CMPU", "idx"),
    0xAC: ("CMPS", "idx"),
    0xB3: ("CMPU", "ext"),
    0xBC: ("CMPS", "ext"),
}


def _idx_extra_len(post: int) -> int:
    """Extra bytes after postbyte for indexed mode."""
    if (post & 0x80) == 0:
        return 0  # 5-bit offset
    ll = post & 0x0F
    if ll in (0x8, 0xC):
        return 1
    if ll in (0x9, 0xD, 0xF):
        return 2
    return 0


def _format_idx(post: int, extra: bytes, pc: int) -> str:
    regs = ["X", "Y", "U", "S"]
    rr = (post >> 5) & 3
    r = regs[rr]
    if (post & 0x80) == 0:
        off = post & 0x1F
        if off & 0x10:
            off = off - 0x20
        return f"{off},{r}"
    ll = post & 0x0F
    ind = bool(post & 0x10)
    if ll == 0x4:
        s = f",{r}"
    elif ll == 0x8 and len(extra) >= 1:
        off = extra[0] if extra[0] < 128 else extra[0] - 256
        s = f"{off},{r}"
    elif ll == 0x9 and len(extra) >= 2:
        off = (extra[0] << 8) | extra[1]
        if off >= 0x8000:
            off -= 0x10000
        s = f"{off},{r}"
    elif ll == 0x6:
        s = f"A,{r}"
    elif ll == 0x5:
        s = f"B,{r}"
    elif ll == 0xB:
        s = f"D,{r}"
    elif ll == 0x0:
        s = f",{r}+"
    elif ll == 0x1:
        s = f",{r}++"
    elif ll == 0x2:
        s = f",-{r}"
    elif ll == 0x3:
        s = f",--{r}"
    elif ll == 0xC and len(extra) >= 1:
        off = extra[0] if extra[0] < 128 else extra[0] - 256
        s = f"{off},PCR"
    elif ll == 0xD and len(extra) >= 2:
        off = (extra[0] << 8) | extra[1]
        if off >= 0x8000:
            off -= 0x10000
        s = f"{off},PCR"
    elif ll == 0xF and len(extra) >= 2:
        addr = (extra[0] << 8) | extra[1]
        s = f"${addr:04X}"
        ind = True
    else:
        s = f"${post:02X},{r}"
    if ind:
        return f"[{s}]"
    return s


# TFR/EXG register codes (postbyte high/low nibble)
_TFR_REGS = {
    0x0: "D",
    0x1: "X",
    0x2: "Y",
    0x3: "U",
    0x4: "S",
    0x5: "PC",
    0x8: "A",
    0x9: "B",
    0xA: "CC",
    0xB: "DP",
}

# PSHS/PULS bit order (low bit first in listing is conventional)
_STACK_BITS_S = (
    (0x01, "CC"),
    (0x02, "A"),
    (0x04, "B"),
    (0x08, "DP"),
    (0x10, "X"),
    (0x20, "Y"),
    (0x40, "U"),
    (0x80, "PC"),
)
_STACK_BITS_U = (
    (0x01, "CC"),
    (0x02, "A"),
    (0x04, "B"),
    (0x08, "DP"),
    (0x10, "X"),
    (0x20, "Y"),
    (0x40, "S"),
    (0x80, "PC"),
)


def _format_stack(mnem: str, pb: int) -> str:
    bits = _STACK_BITS_U if mnem.upper() in ("PSHU", "PULU") else _STACK_BITS_S
    regs = [name for mask, name in bits if pb & mask]
    if not regs:
        return f"#${pb:02X}"
    return ",".join(regs)


def _emit_instr(addr: int, mnem: str, operand: str = "") -> list[str]:
    """lwasm-friendly lines: label, then indented mnemonic + operand."""
    mnem = mnem.lower()
    out = [f"L{addr:04X}"]
    if operand:
        out.append(f"\t{mnem} {operand}")
    else:
        out.append(f"\t{mnem}")
    return out


@dataclass
class _Decoded:
    size: int
    mnem: str
    operand: str
    refs: list[int] = field(default_factory=list)  # absolute code addresses referenced


def _decode_at(data: bytes, i: int, base: int) -> _Decoded | None:
    """Decode one instruction at offset i. None if truncated/unknown → use fcb."""
    n = len(data)
    if i >= n:
        return None
    addr = base + i
    op = data[i]
    pos = i + 1
    mnem: str
    mode: str

    if op == 0x10 and pos < n:
        op2 = data[pos]
        pos += 1
        if op2 not in _PAGE1:
            return _Decoded(2, "fcb", f"$10,${op2:02X}")
        mnem, mode = _PAGE1[op2]
    elif op == 0x11 and pos < n:
        op2 = data[pos]
        pos += 1
        if op2 not in _PAGE2:
            return _Decoded(2, "fcb", f"$11,${op2:02X}")
        mnem, mode = _PAGE2[op2]
    elif op in _OP:
        mnem, mode = _OP[op]
    else:
        return _Decoded(1, "fcb", f"${op:02X}")

    refs: list[int] = []
    operand = ""
    try:
        if mode == "inh":
            pass
        elif mode == "imm8":
            if pos >= n:
                return None
            pb = data[pos]
            pos += 1
            mu = mnem.upper()
            if mu in ("TFR", "EXG"):
                r1 = _TFR_REGS.get((pb >> 4) & 0xF, f"${(pb >> 4) & 0xF:X}")
                r2 = _TFR_REGS.get(pb & 0xF, f"${pb & 0xF:X}")
                operand = f"{r1},{r2}"
            elif mu in ("PSHS", "PULS", "PSHU", "PULU"):
                operand = _format_stack(mu, pb)
            else:
                operand = f"#${pb:02X}"
        elif mode == "imm16":
            if pos + 1 >= n:
                return None
            operand = f"#${data[pos]:02X}{data[pos + 1]:02X}"
            pos += 2
        elif mode == "dir":
            if pos >= n:
                return None
            dp = data[pos]
            pos += 1
            operand = f"<${dp:02X}"
            mu = mnem.upper()
            if mu in ("JMP", "JSR"):
                # Direct-page absolute is incomplete without DP; skip ref
                pass
        elif mode == "ext":
            if pos + 1 >= n:
                return None
            ea = (data[pos] << 8) | data[pos + 1]
            pos += 2
            operand = f"${ea:04X}"
            if mnem.upper() in ("JMP", "JSR"):
                refs.append(ea)
        elif mode == "rel8":
            if pos >= n:
                return None
            rel = data[pos]
            pos += 1
            if rel >= 128:
                rel -= 256
            target = base + pos + rel
            operand = f"L{target:04X}"
            refs.append(target)
        elif mode == "rel16":
            if pos + 1 >= n:
                return None
            rel = (data[pos] << 8) | data[pos + 1]
            pos += 2
            if rel >= 0x8000:
                rel -= 0x10000
            target = base + pos + rel
            operand = f"L{target:04X}"
            refs.append(target)
        elif mode == "idx":
            if pos >= n:
                return None
            post = data[pos]
            pos += 1
            extra_n = _idx_extra_len(post)
            if pos + extra_n > n:
                return None
            extra = data[pos : pos + extra_n]
            pos += extra_n
            operand = _format_idx(post, extra, base + pos)
        else:
            operand = ""
    except IndexError:
        return None

    return _Decoded(pos - i, mnem, operand, refs)


def disassemble_bytes(data: bytes, base: int = 0) -> list[str]:
    """Disassemble a linear blob at load address ``base``.

    Two-pass: collect branch/call targets, then force instruction boundaries
    so mid-instruction targets still get labels (bytes before them become fcb).
    """
    n = len(data)
    if n == 0:
        return []

    # Pass 1: linear decode → force-sync offsets + external refs
    force: set[int] = {0}
    external: set[int] = set()
    i = 0
    while i < n:
        dec = _decode_at(data, i, base)
        if dec is None or dec.size <= 0:
            i += 1
            continue
        for t in dec.refs:
            off = t - base
            if 0 <= off < n:
                force.add(off)
            else:
                external.add(t)
        i += dec.size

    # Pass 2: emit, never spanning a force point
    lines: list[str] = []
    if external:
        lines.append("* External / out-of-segment targets (ROM, RAM, etc.)")
        for t in sorted(external):
            lines.append(f"L{t:04X}\tequ\t${t:04X}")
        lines.append("")

    i = 0
    while i < n:
        addr = base + i
        dec = _decode_at(data, i, base)
        if dec is None or dec.size <= 0:
            lines.extend(_emit_instr(addr, "fcb", f"${data[i]:02X}"))
            i += 1
            continue
        # Would this instruction skip over a force-sync address?
        span = [f for f in force if i < f < i + dec.size]
        if span:
            lines.extend(_emit_instr(addr, "fcb", f"${data[i]:02X}"))
            i += 1
            continue
        lines.extend(_emit_instr(addr, dec.mnem, dec.operand))
        i += dec.size
    return lines


def disassemble_decb(data: bytes) -> str:
    """Full listing for a DECB or raw binary (lwasm-oriented)."""
    bin = parse_decb_bin(data)
    parts: list[str] = [
        "****************************************",
        "* CoCoIDE 6809 disassembly (best-effort)",
        "* Aimed at lwasm: labels + indented ops",
        "* Data-as-code may still need hand cleanup",
        "****************************************",
        "",
    ]
    if bin.is_decb:
        for seg in bin.segments:
            parts.append(f"\torg\t${seg.load:04X}")
            parts.append(f"* segment load=${seg.load:04X} len={len(seg.data)}")
            parts.extend(disassemble_bytes(seg.data, seg.load))
            parts.append("")
        if bin.exec_addr is not None:
            parts.append(f"\tend\t${bin.exec_addr:04X}")
        else:
            parts.append("\tend")
    else:
        parts.append("\torg\t$0000")
        parts.append("* raw binary (not DECB LOADM)")
        parts.extend(disassemble_bytes(bin.raw_fallback or data, 0))
        parts.append("\tend")
    return "\n".join(parts) + "\n"


def try_external_disassembler(data: bytes, out_asm: Path) -> tuple[bool, str]:
    """Use f9dasm if available; return (ok, message)."""
    f9 = shutil.which("f9dasm")
    if not f9:
        return False, "f9dasm not on PATH"
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        proc = subprocess.run(
            [f9, "-info", str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        text = proc.stdout or proc.stderr or ""
        if proc.returncode == 0 and text.strip():
            out_asm.write_text(text, encoding="utf-8", errors="replace")
            return True, f"Disassembled with f9dasm → {out_asm}"
        return False, f"f9dasm failed: {(proc.stderr or proc.stdout or '')[:200]}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _try_lwasm_check(asm_path: Path) -> str:
    """If lwasm is available, try a dry assemble and return first errors."""
    lwasm = shutil.which("lwasm")
    if not lwasm:
        return ""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
        tmp_bin = Path(tmp.name)
    try:
        proc = subprocess.run(
            [lwasm, "-9", "--format=decb", "-o", str(tmp_bin), str(asm_path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode == 0:
            return " lwasm: OK (reassembles)."
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        head = " | ".join(err[:3]) if err else "assemble failed"
        return f" lwasm: needs cleanup ({head})"
    except (OSError, subprocess.TimeoutExpired):
        return ""
    finally:
        try:
            tmp_bin.unlink(missing_ok=True)
        except OSError:
            pass


def disassemble_bin_file(path: Path, out_asm: Path | None = None) -> tuple[str, str]:
    """Disassemble a .BIN file. Returns (asm_text, method_message)."""
    data = path.read_bytes()
    out = out_asm or path.with_suffix(".asm")
    ok, msg = try_external_disassembler(data, out)
    if ok:
        note = _try_lwasm_check(out)
        return out.read_text(encoding="utf-8", errors="replace"), msg + note
    text = disassemble_decb(data)
    out.write_text(text, encoding="utf-8")
    note = _try_lwasm_check(out)
    return (
        text,
        f"Disassembled with built-in 6809 disassembler → {out}.{note}",
    )
