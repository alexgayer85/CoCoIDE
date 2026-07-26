# Third-party components

CoCoIDE itself is **MIT** (see `LICENSE` / `licenses/LICENSE-CoCoIDE.txt` in
portable packages). Portable builds may also redistribute the tools below as
**separate binaries** in a `tools/` directory. That aggregation does not change
CoCoIDE’s MIT license.

**CoCo ROM images are never shipped.** You must supply legal dumps for XRoar
(see the user guide troubleshooting section).

## Bundled / integrated tools

| Component | Role | License | Upstream | Pin (v0.1.0) |
|-----------|------|---------|----------|--------------|
| XRoar | Emulator | GNU GPL v3 or later | https://www.6809.org.uk/xroar/ | 1.11 |
| Toolshed `decb` | DECB disk images | Public domain | https://github.com/nitros9project/toolshed | 2.4.2 |
| LWTOOLS `lwasm` | 6809 assembler | See upstream COPYING | https://www.lwtools.ca/ | 4.24 or 4.25 |
| PySide6 / Qt | GUI | LGPL / GPL (Qt) | https://www.qt.io/ | freeze-time |

Exact binary versions in a given zip are listed in `tools/VERSIONS.txt` when
present (written by `scripts/fetch_tools_*.sh`).

## XRoar — GPL source offer

XRoar is free software under the **GNU General Public License version 3 or
later**. If this package includes an XRoar binary, corresponding source is
available from:

- https://www.6809.org.uk/xroar/
- https://www.6809.org.uk/git/xroar.git/

You may also request the matching source used for a CoCoIDE release via the
GitHub issue tracker on https://github.com/alexgayer85/CoCoIDE. License text:
`licenses/gpl-3.0.txt` (portable layout) or
https://www.gnu.org/licenses/gpl-3.0.html

## Toolshed

ToolShed is redistributed as public-domain software from the NitrOS-9 project.
Homepage: https://github.com/nitros9project/toolshed

## LWTOOLS

LWTOOLS is redistributed under the terms of its upstream license (see the
COPYING file in the LWTOOLS source tree). Official releases and Windows
binaries: https://www.lwtools.ca/

## PySide6 / Qt

Portable freezes include PySide6 and Qt libraries under their respective
licenses (LGPL/GPL). See the Qt licensing pages and the licenses shipped
inside the PyInstaller bundle.

## How to refresh license files

See `packaging/licenses/README.md`.
