# SFX Lab demo

Short DAC sound effects built with **Tools → Sound / SFX Lab**.

## Run

1. Open this project in CoCoIDE.
2. **Build Disk** then **Run in XRoar** (or load `build/work.dsk`).
3. Press **1** / **2** / **3** for blip / splash / dive; **Q** to exit.

## Authoring

- Patches: `src/sfx/*.sfx.json`
- Export (from SFX Lab): `src/sfx.asm` + `src/sfx_tables.bin`
- Call from your game: `lbsr SoundInit` once, then `lda #id` / `lbsr PlaySfx`

Mux-safe player (ORA #$08 only). Tables are 256 samples × 0–63 (6-bit DAC model).
