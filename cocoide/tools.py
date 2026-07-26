"""Discover and invoke external CoCo tools (xroar, decb, lwasm)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


TOOL_NAMES = ("xroar", "decb", "lwasm", "os9")


@dataclass
class ToolPaths:
    xroar: str | None = None
    decb: str | None = None
    lwasm: str | None = None
    os9: str | None = None
    overrides: dict[str, str] = field(default_factory=dict)

    def resolve(self) -> ToolPaths:
        for name in TOOL_NAMES:
            override = self.overrides.get(name) or os.environ.get(
                f"COCOIDE_{name.upper()}"
            )
            if override and Path(override).is_file() and os.access(override, os.X_OK):
                setattr(self, name, override)
            else:
                setattr(self, name, shutil.which(name))
        return self

    def status_line(self) -> str:
        parts = []
        for name in ("xroar", "decb", "lwasm"):
            path = getattr(self, name)
            parts.append(f"{name}={'OK' if path else 'missing'}")
        return " · ".join(parts)

    def all_required_ok(self) -> bool:
        return bool(self.xroar and self.decb)


def run_cmd(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 60.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def decb_dskini(
    decb: str, disk: Path, tracks: str = "3"
) -> subprocess.CompletedProcess[str]:
    """Create a blank DECB disk image. tracks: 3=35, 4=40, 8=80."""
    disk.parent.mkdir(parents=True, exist_ok=True)
    if disk.exists():
        disk.unlink()
    return run_cmd([decb, "dskini", str(disk), f"-{tracks}"])


def decb_dir(decb: str, disk: Path) -> subprocess.CompletedProcess[str]:
    return run_cmd([decb, "dir", f"{disk},"])


def decb_free(decb: str, disk: Path) -> subprocess.CompletedProcess[str]:
    return run_cmd([decb, "free", f"{disk},"])


def decb_copy_bas(
    decb: str,
    host_file: Path,
    disk: Path,
    coco_name: str,
    *,
    tokenize: bool = True,
    kill_before_write: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Copy a BASIC file onto a DECB image as type 0 binary (tokenized optional)."""
    return decb_copy_to_disk(
        decb,
        host_file,
        disk,
        coco_name,
        file_type=0,
        binary=True,
        tokenize=tokenize,
        kill_before_write=kill_before_write,
    )


def normalize_coco_name(coco_name: str) -> str:
    """Uppercase DECB-style NAME.EXT."""
    name = coco_name.strip().replace("\\", "/").split("/")[-1]
    if "." in name:
        stem, ext = name.rsplit(".", 1)
        return f"{stem.upper()[:8]}.{ext.upper()[:3]}"
    return name.upper()[:8]


def decb_file_exists(decb: str, disk: Path, coco_name: str) -> bool:
    """True if NAME.EXT appears in ``decb dir``."""
    want = normalize_coco_name(coco_name)
    proc = decb_dir(decb, disk)
    text = proc.stdout or ""
    for row in parse_decb_dir(text):
        if normalize_coco_name(row.get("name", "")) == want:
            return True
    # Fallback: substring match on raw dir lines (odd Toolshed formatting)
    stem, _, ext = want.partition(".")
    for line in text.splitlines():
        u = line.upper()
        if stem in u and (not ext or ext in u):
            # avoid matching PAD1 when looking for PAD10, etc.
            parts = line.split()
            if parts and normalize_coco_name(
                parts[0] + ("." + parts[1] if len(parts) > 1 and len(parts[1]) <= 3 else "")
            ) == want:
                return True
    return False


def decb_kill_quiet(decb: str, disk: Path, coco_name: str) -> bool:
    """Kill a DECB file if present. Returns True if kill ran with exit 0."""
    coco_name = normalize_coco_name(coco_name)
    proc = decb_kill(decb, disk, coco_name)
    return proc.returncode == 0


def decb_free_granules(decb: str, disk: Path) -> int | None:
    """Parse free granule count from ``decb free``."""
    free_text = decb_free(decb, disk).stdout or ""
    free_n, _ = parse_granule_usage(free_text, "")
    return free_n


def decb_copy_to_disk(
    decb: str,
    host_file: Path,
    disk: Path,
    coco_name: str,
    *,
    file_type: int = 0,
    binary: bool = True,
    tokenize: bool = False,
    eol_translate: bool = False,
    kill_before_write: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Copy a host file onto a DECB image.

    file_type: 0=BASIC, 1=data, 2=ML, 3=text

    **kill_before_write** (default True): always attempt ``decb kill`` on the
    destination name first (ignore missing-file errors). Toolshed
    ``decb copy -r`` still needs free granules *before* releasing the old
    file, which fails with error **248** on full disks. Kill-then-copy frees
    granules first so same-size replacements fit.
    """
    coco_name = normalize_coco_name(coco_name)
    dest = f"{disk},{coco_name}"
    host_file = Path(host_file)

    if kill_before_write and disk.is_file():
        # Always try kill — do not rely solely on dir parsing (can miss names).
        decb_kill_quiet(decb, disk, coco_name)
        # Also try extension variants sometimes seen on imported disks
        stem = coco_name.rsplit(".", 1)[0]
        for alt_ext in ("BIN", "BAS", "DAT", "OBJ"):
            alt = f"{stem}.{alt_ext}"
            if alt != coco_name:
                decb_kill_quiet(decb, disk, alt)

    args = [decb, "copy", str(host_file.resolve())]
    if tokenize:
        args.append("-t")
    if eol_translate:
        args.append("-l")
    # Prefer not using -r after kill (cleaner allocate); keep -r as safety net
    args.extend([f"-{file_type}", "-b" if binary else "-a", "-r", dest])
    proc = run_cmd(args)

    # If still 248, report free space in stderr for the UI
    if proc.returncode != 0 and (
        "248" in (proc.stderr or "")
        or "248" in (proc.stdout or "")
        or "filled to capacity" in (proc.stderr or "").lower()
        or "filled to capacity" in (proc.stdout or "").lower()
    ):
        free_n = decb_free_granules(decb, disk)
        size = host_file.stat().st_size if host_file.is_file() else 0
        # DECB granule ≈ 2304 bytes
        need = max(1, (size + 2303) // 2304)
        hint = (
            f"\n[CoCoIDE] Disk full (error 248) writing {coco_name} "
            f"({size} bytes ≈ {need} granule(s)). "
            f"Free granules now: {free_n if free_n is not None else '?'}. "
            f"Kill freed the old same-name file only if it existed under "
            f"exactly that name; a larger rebuild or a different BIN name "
            f"still needs spare room. Free space on the image or use a "
            f"larger disk (40/80 track)."
        )
        # Annotate for callers reading stderr/stdout
        err = (proc.stderr or proc.stdout or "") + hint
        proc = subprocess.CompletedProcess(
            proc.args, proc.returncode, proc.stdout or "", err
        )
    return proc


def decb_extract(
    decb: str,
    disk: Path,
    coco_name: str,
    host_file: Path,
    *,
    eol_translate: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Copy a file from a DECB image to the host filesystem."""
    host_file.parent.mkdir(parents=True, exist_ok=True)
    src = f"{disk},{coco_name}"
    args = [decb, "copy", src, str(host_file)]
    if eol_translate:
        args.append("-l")
    # rewrite host file if present
    args.append("-r")
    return run_cmd(args)


def decb_kill(decb: str, disk: Path, coco_name: str) -> subprocess.CompletedProcess[str]:
    """Delete a file from a DECB image."""
    return run_cmd([decb, "kill", f"{disk},{normalize_coco_name(coco_name)}"])


def decb_list(
    decb: str,
    disk: Path,
    coco_name: str,
    *,
    detokenize: bool = True,
) -> subprocess.CompletedProcess[str]:
    """List/detokenize a file from a DECB image (BASIC → ASCII)."""
    args = [decb, "list"]
    if detokenize:
        args.append("-t")
    args.append(f"{disk},{coco_name}")
    return run_cmd(args)


def guess_decb_type(host_file: Path) -> tuple[int, bool, bool]:
    """Return (file_type, binary, tokenize) for a host path."""
    ext = host_file.suffix.lower()
    if ext in (".bas", ".asc"):
        return 0, True, True
    if ext in (".bin", ".rom"):
        return 2, True, False
    if ext in (".dat", ".data"):
        return 1, True, False
    if ext in (".txt", ".asm", ".a"):
        return 3, False, False
    return 3, True, False


def host_to_coco_name(host_file: Path) -> str:
    """Map host filename to DECB 8.3-ish NAME.EXT."""
    stem = re.sub(r"[^A-Za-z0-9]", "", host_file.stem.upper())[:8] or "FILE"
    ext = re.sub(r"[^A-Za-z0-9]", "", host_file.suffix.lstrip(".").upper())[:3] or "DAT"
    return f"{stem}.{ext}"


def parse_decb_dir(output: str) -> list[dict[str, str]]:
    """Best-effort parse of `decb dir` text into rows with full NAME.EXT."""
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        raw = line.rstrip()
        s = line.strip()
        if not s:
            continue
        lower = s.lower()
        if lower.startswith("directory") or "free space" in lower or "free granules" in lower:
            continue
        parts = s.split()
        if len(parts) >= 2 and len(parts[1]) <= 3 and parts[1].replace(".", "").isalnum():
            # MAIN BAS 0 B 1
            name = f"{parts[0]}.{parts[1]}"
            ftype = parts[2] if len(parts) > 2 else ""
            ab = parts[3] if len(parts) > 3 else ""
            grans = parts[4] if len(parts) > 4 else ""
        else:
            name = parts[0] if parts else s
            ftype = ab = grans = ""
        rows.append(
            {
                "raw": raw.strip(),
                "name": name.upper(),
                "type": ftype,
                "ascii": ab,
                "granules": grans,
            }
        )
    return rows


def parse_granule_usage(free_text: str, dir_text: str = "") -> tuple[int | None, int | None]:
    """Return (free, total) granules from `decb free` / `decb dir` output.

    Toolshed prints e.g. ``Free granules: 67 (154368 bytes)``.
    Total is inferred as free + sum of file granule counts from dir when possible,
    else common DECB sizes (68 / 78 / 156).
    """
    free: int | None = None
    for line in free_text.splitlines():
        m = re.search(r"free\s+granules?\s*:\s*(\d+)", line, re.I)
        if m:
            free = int(m.group(1))
            break
    if free is None:
        return None, None

    used = 0
    for line in dir_text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("directory"):
            continue
        parts = line.split()
        # Typical: NAME EXT type ascii/binary granules  e.g. MAIN BAS 0 B 1
        if len(parts) >= 5 and parts[-1].isdigit():
            used += int(parts[-1])
        elif len(parts) >= 2 and parts[-1].isdigit() and not parts[0].lower().startswith("free"):
            # fallback: last integer token
            used += int(parts[-1])

    total = free + used if used > 0 else None
    if total is None:
        # Guess standard DECB geometries
        for candidate in (68, 78, 156):
            if free <= candidate:
                total = candidate
                break
        if total is None:
            total = free  # unknown; bar shows empty used
    return free, total


# Sane IDE targets → XRoar machine + allowed RAM.
# Only profiles that boot with common ECB/DECB ROMs (bas+extbas+disk or coco3+disk).
# Avoids odd clones, PAL-only variants, and illegal RAM (e.g. CoCo 2 · 512K).
MACHINE_PROFILES: dict[str, dict] = {
    "coco1": {
        "label": "CoCo 1 (NTSC)",
        "xroar": "cocous",
        "ram_choices": (16, 32, 64),
        "default_ram": 64,
        "blurb": "Color + Extended BASIC. Needs bas13 + extbas + disk11 ROMs.",
    },
    "coco2": {
        "label": "CoCo 2 (NTSC)",
        "xroar": "coco2bus",
        "ram_choices": (32, 64),
        "default_ram": 64,
        "blurb": "Best for classic DECB/PMODE games. 32K or 64K only.",
    },
    "coco3": {
        "label": "CoCo 3 (NTSC)",
        "xroar": "coco3",
        "ram_choices": (128, 512),
        "default_ram": 512,
        "blurb": "Super Extended Color BASIC. Needs coco3.rom + disk11.",
    },
}


def xroar_machine_flag(target: str) -> str:
    """Map project target id to an XRoar machine profile that boots with stock ROMs."""
    prof = MACHINE_PROFILES.get((target or "").lower())
    if prof:
        return str(prof["xroar"])
    return "coco3"


def normalize_target_ram(target: str, memory_kb: int) -> tuple[str, int]:
    """Clamp target/RAM to a sane, bootable pair. Returns (target, memory_kb)."""
    t = (target or "coco3").lower().strip()
    if t not in MACHINE_PROFILES:
        t = "coco3"
    prof = MACHINE_PROFILES[t]
    choices = tuple(int(x) for x in prof["ram_choices"])
    try:
        mem = int(memory_kb)
    except (TypeError, ValueError):
        mem = int(prof["default_ram"])
    if mem not in choices:
        # Pick nearest allowed size (prefer default if far)
        mem = min(choices, key=lambda c: (abs(c - mem), abs(c - int(prof["default_ram"]))))
    return t, mem


def entry_disk_name(entry: str) -> str:
    """Map src/main.mbas → MAIN.BAS (DECB 8.3 style)."""
    stem = Path(entry).stem.upper()[:8]
    return f"{stem}.BAS"


def default_xroar_audio_args() -> list[str]:
    """Sensible Linux audio defaults for XRoar (Pulse/PipeWire + full gain).

    XRoar defaults to about -3 dBFS gain, which can sound silent next to desktop
    audio. Prefer PulseAudio module (works with PipeWire's pulse layer).
    Override with env COCOIDE_XROAR_AO / COCOIDE_XROAR_AO_GAIN or project fields.
    """
    ao = os.environ.get("COCOIDE_XROAR_AO", "pulse").strip() or "pulse"
    gain = os.environ.get("COCOIDE_XROAR_AO_GAIN", "0").strip() or "0"
    args = ["-ao", ao, "-ao-gain", gain]
    # Optional: COCOIDE_XROAR_ARGS='-ao-volume 100 -ao-rate 48000'
    extra = os.environ.get("COCOIDE_XROAR_ARGS", "").strip()
    if extra:
        # naive split; good enough for simple flags
        args.extend(extra.split())
    return args


def build_xroar_command(
    xroar: str,
    *,
    target: str,
    memory_kb: int,
    disk: Path,
    auto_run: bool,
    entry_name: str = "MAIN.BAS",
    extra_args: list[str] | None = None,
    audio: bool = True,
    ao: str | None = None,
    ao_gain: str | None = None,
) -> list[str]:
    """Build XRoar argv.

    Disk is attached with write-back disabled so emulator SAVEs do not dirty
    the project image. Auto-run uses -type to inject RUN\"NAME\".
    """
    target, memory_kb = normalize_target_ram(target, memory_kb)
    machine = xroar_machine_flag(target)
    # -default-machine selects the boot profile (overrides ~/.xroar/xroar.conf).
    cmd = [
        xroar,
        "-default-machine",
        machine,
    ]
    if memory_kb:
        cmd.extend(["-ram", str(int(memory_kb))])

    if audio:
        if ao or ao_gain:
            cmd.extend(["-ao", ao or os.environ.get("COCOIDE_XROAR_AO", "pulse")])
            cmd.extend(
                ["-ao-gain", ao_gain or os.environ.get("COCOIDE_XROAR_AO_GAIN", "0")]
            )
            extra_env = os.environ.get("COCOIDE_XROAR_ARGS", "").strip()
            if extra_env:
                cmd.extend(extra_env.split())
        else:
            cmd.extend(default_xroar_audio_args())

    # Mount floppy 0; keep project disk clean from emulator writes.
    cmd.extend(["-load-fd0", str(disk), "-no-disk-write-back"])

    if auto_run:
        bas = Path(entry_name).stem.upper()[:8]
        # -type intercepts BASIC input ROM calls once the interpreter is ready.
        cmd.extend(["-type", f'RUN"{bas}"\r'])

    if extra_args:
        cmd.extend(extra_args)
    return cmd


def unmute_xroar_pulse_streams() -> list[str]:
    """Unmute PipeWire/Pulse sink-inputs named XRoar (common 'silent emulator' cause).

    Other apps can have sound while XRoar alone is muted via stream-restore.
    """
    messages: list[str] = []
    if not shutil.which("pactl"):
        return messages
    try:
        out = subprocess.check_output(
            ["pactl", "list", "sink-inputs"],
            text=True,
            errors="replace",
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return messages

    import re

    for block in re.split(r"\n(?=Sink Input #)", out):
        if "XRoar" not in block and "xroar" not in block:
            continue
        m = re.search(r"Sink Input #(\d+)", block)
        if not m:
            continue
        sid = m.group(1)
        try:
            subprocess.run(
                ["pactl", "set-sink-input-mute", sid, "0"],
                check=False,
                timeout=3,
                capture_output=True,
            )
            subprocess.run(
                ["pactl", "set-sink-input-volume", sid, "100%"],
                check=False,
                timeout=3,
                capture_output=True,
            )
            messages.append(f"Unmuted Pulse/PipeWire stream for XRoar (sink-input #{sid})")
        except (OSError, subprocess.TimeoutExpired):
            continue
    return messages


def launch_xroar(cmd: list[str], *, cwd: Path | None = None) -> subprocess.Popen[bytes]:
    # Keep stderr available for audio/driver failures (log file next to project)
    log_path = None
    log_f: object = subprocess.DEVNULL
    if cwd:
        try:
            log_path = Path(cwd) / "build" / "xroar.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_f = open(log_path, "w", encoding="utf-8", errors="replace")
        except OSError:
            log_f = subprocess.DEVNULL
            log_path = None

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=log_f if log_path else subprocess.DEVNULL,
        stderr=subprocess.STDOUT if log_path else subprocess.DEVNULL,
    )

    # XRoar registers with Pulse a moment after start — unmute if stream was saved muted.
    def _deferred_unmute() -> None:
        import time

        for delay in (0.4, 1.0, 2.0):
            time.sleep(delay)
            if proc.poll() is not None:
                return
            msgs = unmute_xroar_pulse_streams()
            if msgs and log_path:
                try:
                    with open(log_path, "a", encoding="utf-8") as lf:
                        for m in msgs:
                            lf.write(m + "\n")
                except OSError:
                    pass
            if msgs:
                return

    try:
        import threading

        threading.Thread(target=_deferred_unmute, daemon=True).start()
    except Exception:
        pass

    return proc
