# SFX Lab demo

Short DAC sound effects built with **Tools → Sound / SFX Lab**.

## Run

1. Open this project in CoCoIDE.
2. **Build Disk** then **Run in XRoar**.
3. After `EXEC` you hear all effects in order, then return to BASIC:

| # | Name | Character |
|---|------|-----------|
| 1 | blip | square buzzer |
| 2 | splash | noise burst |
| 3 | dive | falling machinery |
| 4 | **shoo** | breathy whoosh (`whoosh` wave, volume fade) |
| 5 | **sink** | long descending saw + volume fall |

Use **Tools → Sound / SFX Lab → ▶ Preview** to audition on the PC without XRoar.

## Authoring

- Patches: `src/sfx/*.sfx.json`
- Export: `src/sfx.asm` + `src/sfx_tables.bin`
- Game API: `lbsr SoundInit` once; `lda #id` / `lbsr PlaySfx`

Pitch = phase step through a 256-sample table (`f ≈ Fs × pitch / 256`).
