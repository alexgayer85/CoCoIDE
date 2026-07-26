"""Tests for bundled-tool discovery and platform audio defaults."""

from __future__ import annotations

from pathlib import Path

import cocoide.tools as tools_mod
from cocoide.tools import ToolPaths, build_xroar_command, default_xroar_ao


def test_prefers_bundled_over_path(tmp_path, monkeypatch):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    fake = tools_dir / "decb"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setattr(tools_mod, "_bundle_tools_dir", lambda: tools_dir)
    monkeypatch.delenv("COCOIDE_DECB", raising=False)
    monkeypatch.setattr(
        "shutil.which", lambda n: "/usr/bin/decb" if n == "decb" else None
    )
    t = ToolPaths().resolve()
    assert t.decb == str(fake.resolve())


def test_env_override_beats_bundled(tmp_path, monkeypatch):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    bundled = tools_dir / "xroar"
    bundled.write_text("#!/bin/sh\n")
    bundled.chmod(0o755)
    override = tmp_path / "custom-xroar"
    override.write_text("#!/bin/sh\n")
    override.chmod(0o755)
    monkeypatch.setattr(tools_mod, "_bundle_tools_dir", lambda: tools_dir)
    monkeypatch.setenv("COCOIDE_XROAR", str(override))
    t = ToolPaths().resolve()
    assert t.xroar == str(override.resolve())


def test_paths_line_shows_missing(monkeypatch):
    monkeypatch.setattr(tools_mod, "_bundle_tools_dir", lambda: None)
    monkeypatch.setattr("shutil.which", lambda n: None)
    for name in ("xroar", "decb", "lwasm", "os9"):
        monkeypatch.delenv(f"COCOIDE_{name.upper()}", raising=False)
    t = ToolPaths().resolve()
    assert "xroar=missing" in t.paths_line()
    assert t.status_line().startswith("xroar=missing")


def test_build_xroar_includes_pulse_on_linux(monkeypatch, tmp_path):
    monkeypatch.setattr(tools_mod.sys, "platform", "linux")
    monkeypatch.delenv("COCOIDE_XROAR_AO", raising=False)
    disk = tmp_path / "work.dsk"
    disk.write_bytes(b"")
    cmd = build_xroar_command(
        "/usr/bin/xroar",
        target="coco3",
        memory_kb=512,
        disk=disk,
        auto_run=False,
        ao=None,
    )
    assert "-ao" in cmd
    assert cmd[cmd.index("-ao") + 1] == "pulse"
    assert "-ao-gain" in cmd


def test_build_xroar_omits_ao_on_windows_default(monkeypatch, tmp_path):
    monkeypatch.setattr(tools_mod.sys, "platform", "win32")
    monkeypatch.delenv("COCOIDE_XROAR_AO", raising=False)
    disk = tmp_path / "work.dsk"
    disk.write_bytes(b"")
    cmd = build_xroar_command(
        "xroar.exe",
        target="coco3",
        memory_kb=512,
        disk=disk,
        auto_run=False,
        ao="",
    )
    assert "-ao" not in cmd
    assert "-ao-gain" in cmd


def test_default_xroar_ao_linux(monkeypatch):
    monkeypatch.setattr(tools_mod.sys, "platform", "linux")
    monkeypatch.delenv("COCOIDE_XROAR_AO", raising=False)
    assert default_xroar_ao() == "pulse"


def test_bundle_tools_parent_of_embeddable_python(tmp_path, monkeypatch):
    """Windows embeddable layout: <root>/python/python.exe + <root>/tools/."""
    root = tmp_path / "CoCoIDE-win"
    (root / "python").mkdir(parents=True)
    tools = root / "tools"
    tools.mkdir()
    fake = tools / "decb.exe"
    fake.write_bytes(b"MZ")
    py = root / "python" / "python.exe"
    py.write_bytes(b"")
    monkeypatch.setattr(tools_mod.sys, "executable", str(py))
    monkeypatch.setattr(tools_mod.sys, "frozen", False, raising=False)
    monkeypatch.delenv("COCOIDE_DECB", raising=False)
    monkeypatch.setattr("shutil.which", lambda n: None)
    # Force Windows-style names for this test
    monkeypatch.setattr(tools_mod, "_tool_filenames", lambda name: [f"{name}.exe", name])
    monkeypatch.setattr(tools_mod, "_is_runnable", lambda p: p.is_file())
    t = ToolPaths().resolve()
    assert t.decb == str(fake.resolve())
