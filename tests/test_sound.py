"""Tests for CoCoIDE SFX synthesis and export."""

from __future__ import annotations

from pathlib import Path

from cocoide.sound import (
    SfxPatch,
    export_project_sfx,
    generate_table,
    load_sfx,
    save_sfx,
)


def test_sine_table_length_and_range():
    t = generate_table("sine", volume=63)
    assert len(t) == 256
    assert all(0 <= b <= 63 for b in t)
    assert max(t) >= 50


def test_noise_not_all_zero():
    t = generate_table("noise", volume=40)
    assert any(t)
    assert all(0 <= b <= 40 for b in t)


def test_square_duty():
    t = generate_table("square", volume=60, duty=0.25)
    assert t[0] >= 50
    assert t[200] <= 10


def test_json_roundtrip(tmp_path: Path):
    p = SfxPatch(name="hit", wave="noise", pitch=40, pitch_end=10, length=300, volume=50)
    path = tmp_path / "hit.sfx.json"
    save_sfx(path, p)
    q = load_sfx(path)
    assert q.name == "hit"
    assert q.wave == "noise"
    assert q.length == 300


def test_export_writes_player_and_tables(tmp_path: Path):
    patches = [
        SfxPatch(name="hit", id=0, wave="square", pitch=30, pitch_end=30, length=100, volume=50),
        SfxPatch(name="boom", id=1, wave="noise", pitch=20, pitch_end=5, length=400, volume=48),
    ]
    paths = export_project_sfx(tmp_path, patches, include_demo_loop=True)
    assert (tmp_path / "sfx.asm").is_file()
    assert (tmp_path / "sfx_tables.bin").is_file()
    assert (tmp_path / "sfx_tables.bin").stat().st_size == 512
    text = (tmp_path / "sfx.asm").read_text(encoding="utf-8")
    assert "PlaySfx" in text
    assert "SoundInit" in text
    assert "includebin sfx_tables.bin" in text
    assert "ora     #$08" in text
    assert "sta     #$3C" not in text.lower().replace(" ", "")
    assert any(p.name == "sfx.asm" for p in paths)


def test_preview_pcm_differs_by_wave():
    from cocoide.sound import render_pcm_preview

    a = render_pcm_preview(
        SfxPatch(name="a", wave="square", pitch=48, pitch_end=48, length=500, volume=50)
    )
    b = render_pcm_preview(
        SfxPatch(name="b", wave="noise", pitch=40, pitch_end=10, length=500, volume=40, volume_end=5)
    )
    c = render_pcm_preview(
        SfxPatch(name="c", wave="whoosh", pitch=90, pitch_end=20, length=500, volume=45, volume_end=8)
    )
    assert len(a) > 100 and len(b) > 100 and len(c) > 100
    assert a != b and b != c


def test_simulate_volume_steps_toward_end():
    from cocoide.sound import simulate_playsfx_levels

    levels = simulate_playsfx_levels(
        SfxPatch(
            name="fade",
            wave="square",
            pitch=32,
            pitch_end=32,
            length=100,
            volume=40,
            volume_end=0,
        )
    )
    # average energy should drop toward the end
    head = sum(levels[:20]) / 20
    tail = sum(levels[-20:]) / 20
    assert head > tail
