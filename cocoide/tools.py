"""Discover and invoke external CoCo tools (xroar, decb, lwasm)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


TOOL_NAMES = ("xroar", "decb", "lwasm", "os9")


def _is_runnable(path: Path) -> bool:
    """True if path is a usable executable (Unix X_OK; Windows: file exists)."""
    if not path.is_file():
        return False
    if os.name == "nt":
        return True
    return os.access(path, os.X_OK)


def _tool_filenames(name: str) -> list[str]:
    """Candidate basenames for a tool on this platform."""
    if os.name == "nt":
        return [f"{name}.exe", name]
    return [name]


def _bundle_tools_dir() -> Path | None:
    """Directory containing bundled tools/, if present.

    Search order:
    1. Next to frozen executable (PyInstaller onedir portable layout)
    2. PyInstaller _MEIPASS/tools (onefile extract dir)
    3. Parent of executable dir (Windows embeddable: python/../tools)
    4. Repo root tools/ (developer checkout: CoCoIDE/tools/)
    5. Next to sys.executable
    6. Current working directory tools/ (launchers often chdir to portable root)
    """
    candidates: list[Path] = []
    exe_dir = Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False):
        candidates.append(exe_dir / "tools")
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "tools")
    # Windows embeddable layout: <root>/python/python.exe + <root>/tools/
    candidates.append(exe_dir.parent / "tools")
    candidates.append(exe_dir / "tools")
    # Dev checkout: cocoide/tools.py → parent.parent = repo root
    candidates.append(Path(__file__).resolve().parent.parent / "tools")
    candidates.append(Path.cwd() / "tools")
    for c in candidates:
        if c.is_dir():
            return c
    return None


def _find_bundled_tool(name: str) -> str | None:
    tools_dir = _bundle_tools_dir()
    if tools_dir is None:
        return None
    for fname in _tool_filenames(name):
        candidate = tools_dir / fname
        if _is_runnable(candidate):
            return str(candidate.resolve())
    return None


def default_xroar_ao() -> str:
    """Platform default for XRoar ``-ao`` module (empty = let XRoar choose)."""
    env = os.environ.get("COCOIDE_XROAR_AO")
    if env is not None:
        return env.strip()
    if sys.platform.startswith("linux"):
        return "pulse"
    if sys.platform == "darwin":
        return "coreaudio"
    # Windows and others: omit -ao so XRoar picks its native backend
    return ""


def default_xroar_ao_gain() -> str:
    env = os.environ.get("COCOIDE_XROAR_AO_GAIN")
    if env is not None and env.strip():
        return env.strip()
    return "0"


@dataclass
class ToolPaths:
    xroar: str | None = None
    decb: str | None = None
    lwasm: str | None = None
    os9: str | None = None
    overrides: dict[str, str] = field(default_factory=dict)

    def resolve(self) -> ToolPaths:
        """Resolve tools: env override → bundled tools/ → PATH."""
        for name in TOOL_NAMES:
            override = self.overrides.get(name) or os.environ.get(
                f"COCOIDE_{name.upper()}"
            )
            if override and _is_runnable(Path(override)):
                setattr(self, name, str(Path(override).resolve()))
                continue
            bundled = _find_bundled_tool(name)
            if bundled:
                setattr(self, name, bundled)
                continue
            found = None
            for fname in _tool_filenames(name):
                found = shutil.which(fname)
                if found:
                    break
            setattr(self, name, found)
        return self

    def status_line(self) -> str:
        parts = []
        for name in ("xroar", "decb", "lwasm"):
            path = getattr(self, name)
            parts.append(f"{name}={'OK' if path else 'missing'}")
        return " · ".join(parts)

    def paths_line(self) -> str:
        """Human-readable resolved paths for About / diagnostics."""
        parts = []
        for name in ("xroar", "decb", "lwasm"):
            path = getattr(self, name)
            parts.append(f"{name}={path or 'missing'}")
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


def xroar_ram_org(target: str, memory_kb: int) -> str | None:
    """XRoar -ram-org for this size, or None to leave the machine default.

    Critical: cocous/coco2bus default to 64kx1. Passing ``-ram 32`` alone
    yields ``0 banks * 64K = 0K`` and a black non-booting machine. Must set
    matching chip organisation (16kx1 / 32kx1 / 64kx1).
    """
    t, mem = normalize_target_ram(target, memory_kb)
    if t == "coco3":
        # coco3 accepts -ram 128/512 with its default org
        return None
    return {
        16: "16kx1",
        32: "32kx1",
        64: "64kx1",
    }.get(mem)


def entry_disk_name(entry: str) -> str:
    """Map src/main.mbas → MAIN.BAS (DECB 8.3 style)."""
    stem = Path(entry).stem.upper()[:8]
    return f"{stem}.BAS"


def default_xroar_audio_args() -> list[str]:
    """Platform-aware XRoar audio flags.

    Linux: Pulse/PipeWire + 0 dB gain (XRoar's own default is often -3 dBFS).
    Windows/macOS: gain only when no preferred module, or native module.
    Override with env COCOIDE_XROAR_AO / COCOIDE_XROAR_AO_GAIN or project fields.
    """
    ao = default_xroar_ao()
    gain = default_xroar_ao_gain()
    args: list[str] = []
    if ao:
        args.extend(["-ao", ao])
    if gain:
        args.extend(["-ao-gain", gain])
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
        org = xroar_ram_org(target, memory_kb)
        if org:
            cmd.extend(["-ram-org", org])

    if audio:
        # None / empty ao → platform default (may omit -ao entirely on Windows).
        if ao is None or not str(ao).strip():
            use_ao = default_xroar_ao()
        else:
            use_ao = str(ao).strip()
        if ao_gain is None or not str(ao_gain).strip():
            use_gain = default_xroar_ao_gain()
        else:
            use_gain = str(ao_gain).strip()
        if use_ao:
            cmd.extend(["-ao", use_ao])
        if use_gain:
            cmd.extend(["-ao-gain", use_gain])
        extra_env = os.environ.get("COCOIDE_XROAR_ARGS", "").strip()
        if extra_env:
            cmd.extend(extra_env.split())

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
