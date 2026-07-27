# 13 — Sound / SFX Lab

**Docs last updated:** 2026-07-26

Design short **DAC sound effects** in CoCoIDE, export **6809 assembly + wavetables**, and play them under **XRoar** or on real hardware.

## Open the lab

**Tools → Sound / SFX Lab…**

Requires a project open to save under `src/sfx/` and export into `src/`.

## Concepts

| Idea | CoCo reality |
|------|----------------|
| DAC | 6-bit audio at `$FF20` (bits 7–2) |
| Wavetable | 256 samples, values **0–63** (room for mixing later) |
| Mux | Enable with **`ORA #$08`** on PIA control regs — never smash with `$3C` |
| Player | Blocking busy-loop (`PlaySfx`) — fine for game SFX |

Authoring is inspired by Paul Fiscarelli’s [CoCo Waveform Generator](https://github.com/pfiscarelli/CoCo_Waveform_Generator) (tables + 6-bit model). CoCoIDE does **not** require VCC; exports target XRoar/real CoCo.

## Authoring a patch

1. **New** — create an effect  
2. Set **wave** (`sine`, `square`, `saw`, `noise`), **pitch**, **pitch end** (slide), **length**, **volume**  
3. **Save patch** → `src/sfx/<name>.sfx.json`  
4. **Export ASM to project** → `src/sfx.asm` + `src/sfx_tables.bin`  
5. **Build Disk** — assembles to **`SFX.BIN`**

## Runtime API

```asm
        lbsr    SoundInit       ; once at startup
        lda     #0              ; effect id
        lbsr    PlaySfx         ; blocks until finished
```

- **A** = effect id `0 .. N-1` (order of patches at export)  
- Clobbers **A,B,X,Y,U,CC**  
- Masks IRQs during playback  

### BASIC smoke test

```basic
CLEAR200,&H3F00
AUDIO ON
LOADM"SFX":EXEC
```

The **sfx-lab** example auto-plays every effect once, then returns to BASIC (so a failed keyboard poll cannot hang). For games, call `PlaySfx` yourself on events.

## Files

```text
src/
  sfx/
    blip.sfx.json      ; authoring (edit in SFX Lab)
    splash.sfx.json
  sfx.asm              ; generated player + catalog
  sfx_tables.bin       ; generated 256×N sample tables
```

Do not hand-edit `sfx.asm` for long; change JSON and **Export** again.

## Integrate into a game

1. Export SFX into the game project’s `src/`  
2. Either:
   - **Separate BIN:** `LOADM"SFX"` then your game ML, **or**
   - **One binary:** copy `SoundInit` / `PlaySfx` / tables into your ASM (advanced)  
3. Call `SoundInit` once; call `PlaySfx` on events  

See `examples/sfx-lab` for a complete disk.

## Limits (v1)

- One voice, **blocking** playback (game pauses during SFX)  
- No FIRQ/IRQ multi-voice background music (future)  
- Host-side speaker preview not required — use XRoar after Build  

## Safety notes

- Prefer short lengths (under ~2000 ticks) for snappy UI  
- Volume/pitch clamped 0–63 / 1–255 in the lab  
- If silent: check `AUDIO ON`, ROMs, and XRoar app stream mute (Linux Pulse)  
