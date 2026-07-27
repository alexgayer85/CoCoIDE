"""CoCo DAC SFX synthesis and 6809 export (wavetables + mux-safe player).

Design notes (Fiscarelli / CoCoWG inspired):
- 6-bit DAC at $FF20 (values 0–63, shifted <<2 before write)
- Tables are 256 samples
- v1 player is blocking busy-loop (XRoar + real hardware friendly)
- Mux enable uses ORA #$08 only (never full-byte PIA smash)
"""

from __future__ import annotations

import json
import math
import struct
import subprocess
import tempfile
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

TABLE_LEN = 256
MAX_VOLUME = 63
MAX_LENGTH = 12000
MIN_LENGTH = 16
MAX_PITCH = 255
# Host preview sample rate (matches fixed delay ballpark on CoCo ~6–10 kHz)
PREVIEW_RATE = 11025
WAVE_KINDS = ("sine", "square", "saw", "noise", "whoosh", "custom")


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
    volume_end: int = 48  # linear fade toward this
    duty: float = 0.5
    table: list[int] | None = None
    comment: str = ""
    version: int = 1

    def clamp(self) -> SfxPatch:
        self.wave = self.wave if self.wave in WAVE_KINDS else "square"
        self.pitch = max(1, min(MAX_PITCH, int(self.pitch)))
        self.pitch_end = max(1, min(MAX_PITCH, int(self.pitch_end)))
        self.length = max(MIN_LENGTH, min(MAX_LENGTH, int(self.length)))
        self.volume = max(0, min(MAX_VOLUME, int(self.volume)))
        self.volume_end = max(0, min(MAX_VOLUME, int(self.volume_end)))
        self.duty = max(0.05, min(0.95, float(self.duty)))
        self.name = (self.name or "sfx").strip()[:16] or "sfx"
        if self.table is not None:
            t = [max(0, min(MAX_VOLUME, int(x))) for x in self.table[:TABLE_LEN]]
            if len(t) < TABLE_LEN:
                t.extend([32] * (TABLE_LEN - len(t)))
            self.table = t
        return self

    def summary(self) -> str:
        pe = f"→{self.pitch_end}" if self.pitch_end != self.pitch else ""
        ve = f"→{self.volume_end}" if self.volume_end != self.volume else ""
        return (
            f"{self.name}  [{self.wave}]  "
            f"p{self.pitch}{pe}  v{self.volume}{ve}  L{self.length}"
        )


def _lfsr_step(state: int) -> int:
    bit = ((state >> 0) ^ (state >> 2) ^ (state >> 3) ^ (state >> 5)) & 1
    return ((state >> 1) | (bit << 15)) & 0xFFFF


def generate_table(
    kind: str,
    *,
    volume: int = MAX_VOLUME,
    duty: float = 0.5,
    custom: Sequence[int] | None = None,
    seed: int = 0xACE1,
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

    if kind in ("noise", "whoosh"):
        state = seed & 0xFFFF or 0xACE1
        prev = 32
        for i in range(TABLE_LEN):
            state = _lfsr_step(state)
            raw = state & MAX_VOLUME
            if kind == "whoosh":
                # High-pass-ish hiss: emphasize differences (whisper/shoo)
                diff = abs(raw - prev)
                prev = raw
                # mix bright noise
                raw = min(MAX_VOLUME, (diff * 2 + (state >> 8) & 31) // 1)
                raw = min(MAX_VOLUME, raw + 8)
            out[i] = raw * volume // MAX_VOLUME
        return bytes(out)

    for i in range(TABLE_LEN):
        phase = i / TABLE_LEN
        if kind == "sine":
            s = 0.5 + 0.5 * math.sin(2 * math.pi * phase)
        elif kind == "square":
            s = 1.0 if phase < duty else 0.0
        elif kind == "saw":
            s = phase
        else:
            s = 0.5 + 0.5 * math.sin(2 * math.pi * phase)
        out[i] = max(0, min(MAX_VOLUME, int(round(s * volume))))
    return bytes(out)


def load_sfx(path: Path) -> SfxPatch:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    known = {f.name for f in SfxPatch.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    filtered = {k: v for k, v in data.items() if k in known}
    # default volume_end = volume for old files
    if "volume_end" not in filtered and "volume" in filtered:
        filtered["volume_end"] = filtered["volume"]
    return SfxPatch(**filtered).clamp()


def save_sfx(path: Path, patch: SfxPatch) -> None:
    patch = patch.clamp()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(patch), indent=2) + "\n", encoding="utf-8")


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
    for i, patch in enumerate(patches):
        patch.id = i
    return patches


def _seed_for(patch: SfxPatch) -> int:
    """Stable name hash (do not use Python's randomized hash())."""
    h = 0
    for c in patch.name:
        h = (h * 33 + ord(c)) & 0xFFFF
    return h or 0xACE1


def _lfsr_coco(state: int) -> int:
    """Match PlaySfx: ldd; eora low; lsra; rorb; eora orig_high; std."""
    if state == 0:
        state = 0xACE1
    a0 = (state >> 8) & 0xFF
    b0 = state & 0xFF
    a = a0 ^ b0
    d = ((a & 0xFF) << 8) | b0
    d >>= 1
    a = ((d >> 8) ^ a0) & 0xFF
    b = d & 0xFF
    return (a << 8) | b


def simulate_playsfx_levels(patch: SfxPatch) -> list[int]:
    """DAC levels 0..63 per CoCo sample — single source of truth for preview.

    Mirrors exported PlaySfx (volume step envelope, phase+=pitch, LFSR modes).
    """
    patch = patch.clamp()
    flags_noise = patch.wave in ("noise", "whoosh")
    flags_whoosh = patch.wave == "whoosh"
    table = generate_table(
        patch.wave,
        volume=MAX_VOLUME,
        duty=patch.duty,
        custom=patch.table,
        seed=_seed_for(patch),
    )
    pitch = patch.pitch
    pitch_end = patch.pitch_end
    vol = patch.volume
    vol_end = patch.volume_end
    length = patch.length
    # period = max(1, min(255,len) / max(1,|dv|))  — same as ASM
    dv = abs(patch.volume - patch.volume_end) or 1
    len8 = min(255, length) if length >= 256 else length
    vperiod = max(1, min(255, len8 // dv))
    vcnt = vperiod
    phase = 0
    lfsr = 0xACE1  # fixed start like ASM SfxLfsr fdb
    levels: list[int] = []

    for _ in range(length):
        vcnt -= 1
        if vcnt == 0:
            vcnt = vperiod
            if vol < vol_end:
                vol += 1
            elif vol > vol_end:
                vol -= 1

        if flags_noise:
            lfsr = _lfsr_coco(lfsr) or 0xACE1
            if flags_whoosh:
                a = (lfsr >> 8) & 63
                b = lfsr & 63
                raw = abs(a - b) + 10
                if raw > 63:
                    raw = 63
            else:
                raw = lfsr & 63
        else:
            raw = table[phase & 0xFF]

        # MUL then six lsr on D → (raw*vol)>>6
        level = (raw * vol) >> 6
        if level > 63:
            level = 63
        levels.append(level)

        phase = (phase + pitch) & 0xFF
        if pitch < pitch_end:
            pitch += 1
        elif pitch > pitch_end:
            pitch -= 1

    return levels


def render_pcm_preview(
    patch: SfxPatch,
    *,
    sample_rate: int = PREVIEW_RATE,
) -> bytes:
    """Host PCM from the same sample stream CoCo PlaySfx emits.

    Each CoCo DAC sample is held for ``hold`` host samples so pitch tracks
    the emulator (Fs_coco ≈ 0.89e6 / ~280 ≈ 3.2 kHz; we use 3200).
    """
    levels = simulate_playsfx_levels(patch)
    # Match fixed delay in ASM (~28 decb loops + work ≈ 250–350 cycles)
    coco_fs = 3200
    hold = max(1, sample_rate // coco_fs)
    out = bytearray()
    for level in levels:
        # DAC nibble 0..63 → bipolar-ish around mid (same as CoCo path perception)
        # Use the actual DAC bus value <<2 as unipolar duty energy:
        dac = (level << 2) & 0xFC  # 0,4,8,...,252
        amp = (dac - 128) / 128.0
        val = int(max(-1.0, min(1.0, amp)) * 24000)
        out.extend(struct.pack("<h", val) * hold)
    return bytes(out)

def write_wav(path: Path, pcm: bytes, *, sample_rate: int = PREVIEW_RATE) -> None:
    path = Path(path)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)


def play_pcm_host(pcm: bytes, *, sample_rate: int = PREVIEW_RATE) -> str:
    """Play preview on the host. Returns status message."""
    if not pcm:
        return "Nothing to play"
    tmp = Path(tempfile.mkstemp(suffix=".wav", prefix="cocoide-sfx-")[1])
    try:
        write_wav(tmp, pcm, sample_rate=sample_rate)
        for cmd in (
            ["paplay", str(tmp)],
            ["pw-play", str(tmp)],
            ["aplay", "-q", str(tmp)],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(tmp)],
        ):
            try:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return f"Playing via {cmd[0]}…"
            except FileNotFoundError:
                continue
        return f"Wrote {tmp} (no paplay/aplay/ffplay found — open the WAV manually)"
    except OSError as exc:
        return f"Preview failed: {exc}"


def export_project_sfx(
    dest_dir: Path,
    patches: Sequence[SfxPatch],
    *,
    org: int = 0x3F00,
    include_demo_loop: bool = False,
) -> list[Path]:
    """Write sfx.asm + sfx_tables.bin into dest_dir (typically project src/)."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    patches = [p.clamp() for p in patches]
    if not patches:
        raise ValueError("no SFX patches to export")

    tables = bytearray()
    for p in patches:
        tables.extend(
            generate_table(
                p.wave,
                volume=MAX_VOLUME,
                duty=p.duty,
                custom=p.table,
                seed=_seed_for(p),
            )
        )

    tables_path = dest_dir / "sfx_tables.bin"
    tables_path.write_bytes(bytes(tables))

    # Catalog 8 bytes: id, flags, pitch, pitch_end, len_hi, len_lo, vol, vol_end
    # flags: bit0 = live noise LFSR (noise/whoosh)
    cat_lines = []
    for i, p in enumerate(patches):
        flags = 1 if p.wave in ("noise", "whoosh") else 0
        if p.wave == "whoosh":
            flags |= 2  # breathy noise mode in player
        ln = p.length
        cat_lines.append(
            f"        fcb     {i},${flags:02X},${p.pitch:02X},${p.pitch_end:02X}"
            f",${(ln >> 8) & 0xFF:02X},${ln & 0xFF:02X}"
            f",${p.volume:02X},${p.volume_end:02X}"
            f"  * {i}: {p.name} ({p.wave})"
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
    src = Path(project_src)
    sfx_dir = src / sfx_subdir
    patches = list_sfx_dir(sfx_dir)
    if not patches:
        raise ValueError(f"no *.sfx.json in {sfx_dir}")
    return export_project_sfx(src, patches, include_demo_loop=False)


# --- ASM templates -----------------------------------------------------------

_DEMO_LOOP = """\
* Auto-play every effect once, then return to BASIC.
                clra
DemoAuto
                pshs    a
                lbsr    PlaySfx
                ldx     #$6000
da_w            leax    -1,x
                bne     da_w
                puls    a
                inca
                cmpa    #SFXCOUNT
                blo     DemoAuto
DemoDone
                rts

POLCAT          equ     $A000
WaitKey
                pshs    b,x
                andcc   #$EF
                ldx     #$4000
wk1             jsr     [POLCAT]
                anda    #$7F
                bne     wk2
                leax    -1,x
                bne     wk1
                clra
                puls    b,x
                rts
wk2             puls    b,x
                rts
"""

_RTS_ONLY = """\
                rts
"""

_PLAYER_TEMPLATE = """\
***********************************************************************
* CoCoIDE SFX player — auto-generated (re-export from SFX Lab)
* IMPORTANT: working storage is fcb/fdb (in the .BIN). Do not use rmb
* after includebin — DECB load would omit those bytes.
***********************************************************************

SFXCOUNT        equ     {n_effects}

                org     {org}

START
                lbsr    SoundInit
{demo_body}

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
                lda     $FF23
                anda    #$FB
                sta     $FF23
                lda     $FF22
                ora     #$02
                sta     $FF22
                lda     $FF23
                ora     #$04
                sta     $FF23
                andcc   #$AF
                puls    a
                rts

***********************************************************************
* PlaySfx — A = id  (same algorithm as host simulate_playsfx_levels)
PlaySfx
                pshs    cc,a,b,x,y,u
                orcc    #$50
                cmpa    #SFXCOUNT
                lbhs    ps_done
                ldb     #8
                mul
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
                lda     7,u
                sta     SfxVolEnd
                * vperiod = max(1, min(255,len)/max(1,|dv|))
                lda     6,u
                suba    7,u
                bpl     ps_abs
                nega
ps_abs          tsta
                bne     ps_dv
                lda     #1
ps_dv           tfr     a,b
                lda     SfxLen
                bne     ps_lhi
                lda     SfxLen+1
                bra     ps_div
ps_lhi          lda     #255
ps_div          pshs    b
                clrb
ps_divl         cmpa    ,s
                blo     ps_divd
                suba    ,s
                incb
                bne     ps_divl
ps_divd         tstb
                bne     ps_divok
                incb
ps_divok        stb     SfxVPeriod
                stb     SfxVCnt
                puls    a
                lda     ,u
                clrb
                tfr     d,x
                leax    SfxTables,x
                stx     SfxTab
                clr     SfxPhase
                ldd     #$ACE1
                std     SfxLfsr
                lda     $FF23
                ora     #$08
                sta     $FF23
                ldd     SfxLen
                lbeq    ps_quiet

ps_loop
                dec     SfxVCnt
                bne     ps_samp
                lda     SfxVPeriod
                sta     SfxVCnt
                lda     SfxVol
                cmpa    SfxVolEnd
                beq     ps_samp
                blo     ps_vup
                dec     SfxVol
                bra     ps_samp
ps_vup          inc     SfxVol
ps_samp
                lda     SfxFlags
                bita    #1
                bne     ps_nz
                ldx     SfxTab
                lda     SfxPhase
                lda     a,x
                bra     ps_dac
ps_nz           ldd     SfxLfsr
                bne     ps_n1
                ldd     #$ACE1
ps_n1           eora    SfxLfsr+1
                lsra
                rorb
                eora    SfxLfsr
                std     SfxLfsr
                lda     SfxFlags
                bita    #2
                bne     ps_wh
                lda     SfxLfsr+1
                anda    #63
                bra     ps_dac
ps_wh           lda     SfxLfsr
                anda    #63
                ldb     SfxLfsr+1
                andb    #63
                pshs    b
                suba    ,s+
                bpl     ps_w1
                nega
ps_w1           adda    #10
                cmpa    #63
                bls     ps_dac
                lda     #63
ps_dac          ldb     SfxVol
                mul
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
                rorb
                tfr     b,a
                lsla
                lsla
                anda    #$FC
                sta     $FF20
                tsta
                bpl     ps_pb0
                lda     $FF22
                ora     #$02
                bra     ps_pb1
ps_pb0          lda     $FF22
                anda    #$FD
ps_pb1          sta     $FF22
                lda     SfxPhase
                adda    SfxPitch
                sta     SfxPhase
                ldb     #28
ps_del          decb
                bne     ps_del
                lda     SfxPitch
                cmpa    SfxPend
                beq     ps_next
                blo     ps_pin
                deca
                bra     ps_pst
ps_pin          inca
ps_pst          sta     SfxPitch
ps_next         ldd     SfxLen
                subd    #1
                std     SfxLen
                lbne    ps_loop
ps_quiet        lda     #$80
                sta     $FF20
ps_done         andcc   #$AF
                puls    cc,a,b,x,y,u
                rts

***********************************************************************
* Working storage MUST be real data bytes inside the DECB image
SfxFlags        fcb     0
SfxPitch        fcb     0
SfxPend         fcb     0
SfxVol          fcb     0
SfxVolEnd       fcb     0
SfxVPeriod      fcb     1
SfxVCnt         fcb     1
SfxPhase        fcb     0
SfxLen          fdb     0
SfxTab          fdb     0
SfxLfsr         fdb     $ACE1

SfxCat
{catalog}

SfxTables
                includebin sfx_tables.bin

                end     START
"""
