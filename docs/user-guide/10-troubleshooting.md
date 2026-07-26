# 10 — Troubleshooting

**Docs last updated:** 2026-07-12

## Tools show as missing

Status bar: `xroar=missing` or `decb=missing`.

1. Install XRoar and Toolshed so `xroar` and `decb` work in a terminal.  
2. Or set:

   ```bash
   export COCOIDE_XROAR=/full/path/to/xroar
   export COCOIDE_DECB=/full/path/to/decb
   ```

3. Restart CoCoIDE. Check **Help → About**.

## XRoar opens but no BASIC / black screen

XRoar needs **ROM images**. CoCoIDE does not ship copyrighted ROMs.

Typical layout under `~/.xroar/roms/`:

| Goal | ROMs |
|------|------|
| CoCo 1 / 2 (NTSC) | `bas13.rom`, `extbas10.rom` (or 1.1), `disk11.rom` |
| CoCo 3 (NTSC) | `coco3.rom`, `disk11.rom` |

Also check **Project Settings** (green chip): **CoCo 2 · 128K** (and similar) is invalid and used to pass a broken `-ram` to XRoar. The IDE now only offers legal sizes and clamps old projects.

Configure extra ROMs as XRoar expects (config / ROM path). See the [XRoar manual](https://www.6809.org.uk/xroar/doc/).

## Auto-run does nothing / wrong program

- Confirm **Auto-run** is checked.  
- Entry file stem becomes the RUN name (`main.mbas` → `RUN"MAIN"`).  
- Timing can be flaky on slow hosts; turn Auto-run off and type `RUN"MAIN"` yourself.  
- Standalone programs are **not** auto-started.

## `?RG ERROR` (RETURN without GOSUB)

Fixed in current preprocessor layout (`GOTO` past procedures).  
If you see it on **old** `build/*.bas`, run **Build Disk** again.  
If you write classic BASIC by hand, do not place bare `RETURN` before any `GOSUB`.

## `?SN ERROR` / odd variable behavior

- Keyword used as a variable name.  
- Without preprocessor, only **two characters** of names matter.  
- Check Problems for VAR\* and SYN\* codes.

## Disk empty after open

- Image not created yet → **Build Disk** or Disk **New**.  
- Wrong project / path in `disk_image`.  
- Hit **↻** refresh.

## Add cur refuses `.mbas`

Expected. Use **Build Disk** for modern BASIC.

## Build succeeds but Problems is full of red

Diagnostics can flag target mismatches (e.g. CoCo 3 keywords on CoCo 2).  
Either fix the source or click the green **target chip** (or **File → Project Settings…**) and choose **CoCo 3**.

## Emulator changes not saved

By design: **`-no-disk-write-back`**.  
Edit `src/`, then Build again.

## No sound in XRoar

**Very common on Linux:** the **system** and other apps have sound, but **XRoar’s own stream is muted** in PulseAudio/PipeWire (per-application mute). CoCoIDE will try to unmute it after launch; you can also fix it once by hand.

### Fix: unmute the XRoar app stream

While XRoar is running, either:

- **Desktop mixer** (Plasma / GNOME): find **XRoar** and unmute that application (not only the master volume), or  
- **Terminal:**

```bash
pactl list sink-inputs | python3 -c "
import sys, re, subprocess
blocks = sys.stdin.read().split('Sink Input #')
for block in blocks[1:]:
    if 'XRoar' not in block and 'xroar' not in block:
        continue
    sid = block.split()[0].strip()
    subprocess.run(['pactl', 'set-sink-input-mute', sid, '0'])
    subprocess.run(['pactl', 'set-sink-input-volume', sid, '100%'])
    print('unmuted XRoar stream', sid)
"
```

Then in BASIC: `AUDIO ON` / `PLAY "O3T5CDEFG"`.

PipeWire remembers per-app mute; once unmuted, later runs usually stay unmuted.

### CoCoIDE audio flags

Launch includes **`-ao pulse -ao-gain 0`**. See the **XRoar** tab. Log: `build/xroar.log`.

```bash
export COCOIDE_XROAR_AO=alsa
export COCOIDE_XROAR_AO_GAIN=0
```

Or in `project.cocoide`: `"xroar_ao": "pulse"`, `"xroar_ao_gain": "0"`.

### Program notes

- Auto-run only runs entry BASIC, not `BEEP.BIN`.  
- Sample: `AUDIO ON` / `LOADM"BEEP":EXEC`.

## lwasm “Bad operand” after opening a `.BIN`

Older CoCoIDE disassemblies used forms lwasm rejects, e.g. `TFR #$98` instead of
`TFR B,A`, or stuck tokens like `BNEL3F21`.

**Fix:**

1. **Build → Disassemble BIN file…** again on the original `.bin` (or re-import).  
2. Prefer the new listing: labels on their own lines, `tfr B,A`, `puls A,B`, full
   memory ops (`inc $60D8`, …).  
3. If errors remain, they are often **data-as-code** — mark tables as `fcb`/`fdb`,
   or install **f9dasm** on `PATH` and re-disassemble.

See [12 — Assembly](12-assembly.md).

## File dialogs show empty squares / no icons

Qt’s file dialog toolbar is six buttons (Back, Forward, **Up**, New folder, List,
Detail). If the icon theme does not load, they look like blank squares.

**Fix (current builds):** CoCoIDE uses its own file dialog with a light local
theme and **text labels** on those buttons (`Back`, `Up`, `New folder`, …), so
they stay usable without icons.

Restart CoCoIDE after updating. Buttons next to “Look in” should read
**Back · Forward · Up · New folder · List · Detail**.

## GUI will not start

```bash
# From CoCoIDE root
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python -m cocoide.app
```

On headless systems, a display (or X11/Wayland) is required for the GUI.

## Getting help

- User guide index: [README.md](README.md)  
- Design notes: [../UI.md](../UI.md)  
- File an issue on the project repository (when published) with: OS, tool versions (`xroar -h`, `decb`), and Build log text.  
