# SFX Lab demo

Short DAC sound effects built with **Tools → Sound / SFX Lab**.

## Run

1. Open this project in CoCoIDE.
2. **Build Disk** then **Run in XRoar** (or load `build/work.dsk`).
3. After `EXEC`, you should hear **three effects in a row** (blip, splash, dive), then return to BASIC.

If you only heard two short speaker pops and a freeze, rebuild from current `main` — older demos waited forever for a key after init.

## Authoring

- Patches: `src/sfx/*.sfx.json`
- Export (from SFX Lab): `src/sfx.asm` + `src/sfx_tables.bin`
- Call from your game: `lbsr SoundInit` once, then `lda #id` / `lbsr PlaySfx`

Mux-safe player (ORA #$08 only). Tables are 256 samples × 0–63 (6-bit DAC model).
