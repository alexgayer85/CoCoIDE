"""Project model: project.cocoide JSON on disk."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_ENTRY = "src/main.mbas"
PROJECT_FILENAME = "project.cocoide"


@dataclass
class Project:
    name: str = "untitled"
    target: str = "coco3"  # coco1 | coco2 | coco3
    memory_kb: int = 512
    dialect: str = "decb"
    entry: str = DEFAULT_ENTRY
    disk_image: str = "build/work.dsk"
    auto_run: bool = True
    preprocessor: bool = True
    standalone: list[str] = field(default_factory=list)
    asm_sources: list[str] = field(default_factory=list)  # optional explicit list; else auto src/**/*.asm
    roms: dict[str, str] = field(default_factory=dict)
    # XRoar audio (optional; empty ao = platform default, e.g. pulse on Linux)
    xroar_ao: str = ""  # pulse | alsa | oss | null | "" (auto)
    xroar_ao_gain: str = "0"  # dB relative to 0 dBFS (XRoar default is often -3)
    root: Path | None = field(default=None, repr=False)

    @property
    def entry_path(self) -> Path | None:
        if not self.root:
            return None
        return self.root / self.entry

    @property
    def disk_path(self) -> Path | None:
        if not self.root:
            return None
        return self.root / self.disk_image

    @property
    def target_chip(self) -> str:
        machine = {"coco1": "CoCo 1", "coco2": "CoCo 2", "coco3": "CoCo 3"}.get(
            self.target, self.target
        )
        return f"{machine} · {self.memory_kb}K · {self.dialect.upper()}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("root", None)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: Path | None = None) -> Project:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known and k != "root"}
        proj = cls(**filtered)
        proj.root = root
        # Clamp illegal pairs (e.g. coco2 · 128K) so Run/diagnostics stay sane
        try:
            from cocoide.tools import normalize_target_ram

            t, m = normalize_target_ram(proj.target, int(proj.memory_kb or 64))
            proj.target, proj.memory_kb = t, m
        except Exception:
            pass
        return proj

    def save(self) -> Path:
        if not self.root:
            raise ValueError("Project has no root path")
        try:
            from cocoide.tools import normalize_target_ram

            self.target, self.memory_kb = normalize_target_ram(
                self.target, int(self.memory_kb or 64)
            )
        except Exception:
            pass
        path = self.root / PROJECT_FILENAME
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path

    @classmethod
    def load(cls, root: Path) -> Project:
        path = root / PROJECT_FILENAME
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data, root=root)

    @classmethod
    def create_new(
        cls,
        root: Path,
        name: str,
        *,
        target: str = "coco3",
        memory_kb: int = 512,
        preprocessor: bool = True,
        create_disk: bool = True,
    ) -> Project:
        root.mkdir(parents=True, exist_ok=True)
        (root / "src").mkdir(exist_ok=True)
        (root / "build").mkdir(exist_ok=True)

        entry = root / DEFAULT_ENTRY
        if not entry.exists():
            entry.write_text(
                _default_main_source(name, target, memory_kb),
                encoding="utf-8",
            )

        proj = cls(
            name=name,
            target=target,
            memory_kb=memory_kb,
            dialect="decb",
            entry=DEFAULT_ENTRY,
            disk_image="build/work.dsk",
            auto_run=True,
            preprocessor=preprocessor,
            root=root,
        )
        proj.save()

        if create_disk:
            # Disk creation is handled by tools layer when decb is available.
            pass

        return proj


def _default_main_source(name: str, target: str, memory_kb: int) -> str:
    return f"""@target {target}, {memory_kb}k, decb
@start 100
@step 10

' {name} — modern BASIC (preprocessor on)
' Use @include "other.mbas" to pull modules into this program.

procedure Main()
  cls
  print "{name.upper()}"
  print "COCOIDE / DISK EXTENDED BASIC"
  print
  print "PRESS ANY KEY"
  ' wait for key
  k$ = inkey$
  while k$ = ""
    k$ = inkey$
  wend
end
"""
