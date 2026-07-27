"""CoCo DAC SFX synthesis and 6809 export (wavetables + mux-safe player).

Design notes (Fiscarelli / CoCoWG inspired):
- 6-bit DAC at $FF20 (values 0–63, shifted <<2 before write)
- Tables are 256 samples
- v1 player is blocking busy-loop (XRoar + real hardware friendly)
- Mux enable uses ORA #$08 only (never STA #$3C on keyboard PIA)
"""

from __future__ import annotations

import json
import math
import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

TABLE_LEN = 256
MAX_VOLUME = 63
MAX_LENGTH = 8000
MIN_LENGTH = 16
MAX_PITCH = 255
WAVE_KINDS = ("sine", "square", "saw", "noise", "custom")


@dataclass
class SfxPatch:
    """One short sound effect (authoring model)."""

    name: str = "sfx"
    id: int = 0
    wave: str = "square"
    pitch: int = 32
    pitch_end: int = 32
    length: int = 200
    volume: int = 48
    duty: float = 0.5
    table: list[int] | None = None  # 256 values 0–63 if wave==custom
    comment: str = ""
    version: int = 1

    def clamp(self) -> SfxPatch:
        self.wave = self.wave if self.wave in WAVE_KINDS else "square"
        self.pitch = max(1, min(MAX_PITCH, int(self.pitch)))
        self.pitch_end = max(1, min(MAX_PITCH, int(self.pitch_end)))
        self.length = max(MIN_LENGTH, min(MAX_LENGTH, int(self.length)))
        self.volume = max(0, min(MAX_VOLUME, int(self.volume)))
        self.duty = max(0.05, min(0.95, float(self.duty)))
        self.name = (self.name or "sfx").strip()[:16] or "sfx"
        if self.table is not None:
            t = [max(0, min(MAX_VOLUME, int(x))) for x in self.table[:TABLE_LEN]]
            if len(t) < TABLE_LEN:
                t.extend([32] * (TABLE_LEN - len(t)))
            self.table = t
        return self


def generate_table(
    kind: str,
    *,
    volume: int = MAX_VOLUME,
    duty: float = 0.5,
    custom: Sequence[int] | None = None,
) -> bytes:
    """Return 256 bytes with samples in 0..63."""
    volume = max(0, min(MAX_VOLUME, int(volume)))
    duty = max(0.05, min(0.95, float(duty)))
    kind = kind if kind in WAVE_KINDS else "square"
    out = bytearray(TABLE_LEN)

    if kind == "custom" and custom is not None:
        for i in range(TABLE_LEN):
            v = int(custom[i]) if i < len(custom) else 32
            out[i] = max(0, min(MAX_VOLUME, v))
        return bytes(out)

    if kind == "noise":
        # xorshift-ish LFSR → unipolar 0..volume
        state = 0xACE1
        for i in range(TABLE_LEN):
            bit = ((state >> 0) ^ (state >> 2) ^ (state >> 3) ^ (state >> 5)) & 1
            state = ((state >> 1) | (bit << 15)) & 0xFFFF
            out[i] = (state & MAX_VOLUME) * volume // MAX_VOLUME
        return bytes(out)

    for i in range(TABLE_LEN):
        phase = i / TABLE_LEN  # 0..1
        if kind == "sine":
            # unipolar sine: 0.5 + 0.5*sin
            s = 0.5 + 0.5 * math.sin(2 * math.pi * phase)
        elif kind == "square":
            s = 1.0 if phase < duty else 0.0
        elif kind == "saw":
            s = phase
        else:
            s = 0.5 + 0.5 * math.sin(2 * math.pi * phase)
        out[i] = int(round(s * volume))
        out[i] = max(0, min(MAX_VOLUME, out[i]))
    return bytes(out)


def load_sfx(path: Path) -> SfxPatch:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    known = {f.name for f in SfxPatch.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    filtered = {k: v for k, v in data.items() if k in known}
    return SfxPatch(**filtered).clamp()


def save_sfx(path: Path, patch: SfxPatch) -> None:
    patch = patch.clamp()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    d = asdict(patch)
    path.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")


def list_sfx_dir(sfx_dir: Path) -> list[SfxPatch]:
    sfx_dir = Path(sfx_dir)
    if not sfx_dir.is_dir():
        return []
    patches: list[SfxPatch] = []
    for p in sorted(sfx_dir.glob("*.sfx.json")):
        try:
            patches.append(load_sfx(p))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    # stable ids by sort order if missing/dupe
    for i, patch in enumerate(patches):
        patch.id = i
    return patches


def render_pcm_preview(
    patch: SfxPatch,
    *,
    sample_rate: int = 11025,
) -> bytes:
    """Render mono signed 16-bit LE PCM for host preview."""
    patch = patch.clamp()
    table = generate_table(
        patch.wave,
        volume=patch.volume,
        duty=patch.duty,
        custom=patch.table,
    )
    # ~ one sample tick ≈ 40 host samples at 11kHz for coarse pitch feel
    host_per_tick = max(1, sample_rate // 400)
    pitch = patch.pitch
    pitch_end = patch.pitch_end
    phase = 0
    samples: list[int] = []
    lfsr = 0xACE1
    for tick in range(patch.length):
        if patch.wave == "noise":
            bit = ((lfsr >> 0) ^ (lfsr >> 2) ^ (lfsr >> 3) ^ (lfsr >> 5)) & 1
            lfsr = ((lfsr >> 1) | (bit << 15)) & 0xFFFF
            level = (lfsr & MAX_VOLUME) * patch.volume // MAX_VOLUME
        else:
            level = table[(phase >> 8) & 0xFF]
        # unipolar 0..63 → signed roughly -1..1 around mid
        amp = (level - 32) / 32.0
        val = int(max(-1.0, min(1.0, amp)) * 20000)
        samples.extend([val] * host_per_tick)
        phase = (phase + (pitch << 8)) & 0xFFFF
        if pitch_end != patch.pitch:
            if pitch < pitch_end:
                pitch = min(pitch_end, pitch + 1)
            elif pitch > pitch_end:
                pitch = max(pitch_end, pitch - 1)
    return b"".join(struct.pack("<h", s) for s in samples)


def _asm_byte_list(data: bytes, per_line: int = 16) -> str:
    lines = []
    for i in range(0, len(data), per_line):
        chunk = data[i : i + per_line]
        lines.append("        fcb     " + ",".join(f"${b:02X}" for b in chunk))
    return "\n".join(lines)


def export_project_sfx(
    dest_dir: Path,
    patches: Sequence[SfxPatch],
    *,
    org: int = 0x3F00,
    include_demo_loop: bool = False,
) -> list[Path]:
    """Write sfx.asm + sfx_tables.bin into dest_dir (typically project src/).

    Returns list of written paths.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    patches = [p.clamp() for p in patches]
    if not patches:
        raise ValueError("no SFX patches to export")

    # One table per patch (simple indexing by id)
    tables = bytearray()
    for p in patches:
        tables.extend(
            generate_table(
                p.wave,
                volume=MAX_VOLUME,  # scale by patch volume at play time
                duty=p.duty,
                custom=p.table,
            )
        )

    tables_path = dest_dir / "sfx_tables.bin"
    tables_path.write_bytes(bytes(tables))

    # Catalog: 8 bytes per effect
    # wave_index(1), flags(1), pitch(1), pitch_end(1), length_hi, length_lo, volume(1), reserved(1)
    # flags bit0 = noise (ignore table, use LFSR)
    cat_lines = []
    for i, p in enumerate(patches):
        flags = 1 if p.wave == "noise" else 0
        ln = p.length
        cat_lines.append(
            f"        fcb     {i},${flags:02X},${p.pitch:02X},${p.pitch_end:02X}"
            f",${(ln >> 8) & 0xFF:02X},${ln & 0xFF:02X},${p.volume:02X},$00"
            f"  * {i}: {p.name}"
        )

    n = len(patches)
    demo = _DEMO_LOOP if include_demo_loop else _RTS_ONLY

    asm = _PLAYER_TEMPLATE.format(
        org=f"${org:04X}",
        n_effects=n,
        catalog="\n".join(cat_lines),
        demo_body=demo,
        table_bytes=len(tables),
    )
    asm_path = dest_dir / "sfx.asm"
    asm_path.write_text(asm, encoding="utf-8")

    return [asm_path, tables_path]


def export_sfx_json_dir(project_src: Path, sfx_subdir: str = "sfx") -> list[Path]:
    """Load all JSON under src/sfx/ and export next to them (src/)."""
    src = Path(project_src)
    sfx_dir = src / sfx_subdir
    patches = list_sfx_dir(sfx_dir)
    if not patches:
        raise ValueError(f"no *.sfx.json in {sfx_dir}")
    return export_project_sfx(src, patches, include_demo_loop=False)


# --- ASM templates -----------------------------------------------------------

_DEMO_LOOP = """\
* Demo: press 1/2/3… for SFX 0/1/2… ; Q quits to BASIC (RTS)
DemoLoop
        lbsr    WaitKey
        cmpa    #'Q'
        beq     DemoDone
        cmpa    #'q'
        beq     DemoDone
        suba    #'1'
        blo     DemoLoop
        cmpa    #SFXCOUNT
        bhs     DemoLoop
        lbsr    PlaySfx
        bra     DemoLoop
DemoDone
        rts

WaitKey
        pshs    b
wk1     jsr     [$A000]         ; POLCAT
        tsta
        beq     wk1
        puls    b
        rts
"""

_RTS_ONLY = """\
* Library build — START just inits and returns (call PlaySfx from your game).
        rts
"""

_PLAYER_TEMPLATE = """\
***********************************************************************
* CoCoIDE SFX player — auto-generated (re-export from SFX Lab)
*
* API:
*   SoundInit  — enable DAC mux safely (call once)
*   PlaySfx    — A = effect id 0..{n_effects}-1 (blocks until done)
*
* Clobbers: A,B,X,Y,U,CC
* Hardware: 6-bit DAC $FF20; mux ORA #$08 only (never full-byte PIA smash)
* Tables: sfx_tables.bin ({table_bytes} bytes = {n_effects} x 256)
* Wavetable model inspired by Paul Fiscarelli CoCoWG (samples 0-63).
***********************************************************************

SFXCOUNT        equ     {n_effects}

                org     {org}

START
                lbsr    SoundInit
{demo_body}

***********************************************************************
SoundInit
                pshs    a
                orcc    #$50
                lda     $FF01
                ora     #$08
                sta     $FF01
                lda     $FF03
                ora     #$08
                sta     $FF03
                lda     $FF23
                ora     #$08
                sta     $FF23
                lda     $FF21
                anda    #$FB
                sta     $FF21
                lda     #$FC
                sta     $FF20
                lda     $FF21
                ora     #$04
                sta     $FF21
                lda     #$80
                sta     $FF20
                andcc   #$AF
                puls    a
                rts

***********************************************************************
* PlaySfx — A = effect id
PlaySfx
                pshs    cc,a,b,x,y,u
                orcc    #$50
                cmpa    #SFXCOUNT
                lbhs    ps_done
                * U = &SfxCat[A]
                ldb     #8
                mul                     ; D = A*8
                ldu     #SfxCat
                leau    d,u
                lda     1,u
                sta     SfxFlags
                lda     2,u
                sta     SfxPitch
                lda     3,u
                sta     SfxPend
                lda     4,u
                ldb     5,u
                std     SfxLen
                lda     6,u
                sta     SfxVol
                * X = SfxTables + id*256
                lda     ,u
                clrb
                tfr     d,x             ; D = id*256
                leax    SfxTables,x
                stx     SfxTab
                clr     SfxPhase
                clr     SfxPhase+1
                lda     $FF23
                ora     #$08
                sta     $FF23
                ldd     SfxLen
                lbeq    ps_quiet

ps_loop
                lda     SfxFlags
                bita    #$01
                bne     ps_noise
                * A = table[phase_hi]
                ldx     SfxTab
                lda     SfxPhase        ; high byte of phase
                lda     a,x
                bra     ps_scale
ps_noise
                * 16-bit LFSR step → A = 0..63
                ldd     SfxLfsr
                bne     ps_n1
                ldd     #$ACE1
ps_n1           eora    SfxLfsr+1
                lsra
                rorb
                eora    SfxLfsr
                std     SfxLfsr
                lda     SfxLfsr+1
                anda    #63
ps_scale
                * A = raw 0..63; level ~= (raw * vol) >> 6; DAC = level << 2
                ldb     SfxVol
                mul                     ; D = raw * vol
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb                    ; D >>= 6 → B
                tfr     b,a
                lsla
                lsla
                anda    #$FC
                sta     $FF20
                * phase_hi += pitch (8-bit step through 256-sample table)
                lda     SfxPhase
                adda    SfxPitch
                sta     SfxPhase
                * slide pitch toward pitch_end
                lda     SfxPitch
                cmpa    SfxPend
                beq     ps_len
                blo     ps_inc
                dec     SfxPitch
                bra     ps_len
ps_inc          inc     SfxPitch
ps_len
                ldd     SfxLen
                subd    #1
                std     SfxLen
                lbeq    ps_quiet
                ldb     #10
ps_dly          decb
                bne     ps_dly
                bra     ps_loop

ps_quiet
                lda     #$80
                sta     $FF20
ps_done
                andcc   #$AF
                puls    cc,a,b,x,y,u
                rts

***********************************************************************
* Catalog: wave_id, flags, pitch, pitch_end, len_hi, len_lo, vol, pad
SfxCat
{catalog}

SfxTables
                includebin sfx_tables.bin

SfxFlags        rmb     1
SfxPitch        rmb     1
SfxPend         rmb     1
SfxVol          rmb     1
SfxLen          rmb     2
SfxPhase        rmb     2
SfxTab          rmb     2
SfxLfsr         fdb     $ACE1

                end     START
"""
