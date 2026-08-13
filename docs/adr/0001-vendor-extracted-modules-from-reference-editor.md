# Vendor extracted parsing modules from alfizari's save editor, not a submodule or from-scratch rewrite

The Nightreign save format (BND4 container, AES-CBC with a hardcoded key, fixed-offset binary structs for inventory/vessels) is already reverse-engineered and working in [alfizari/Elden-Ring-Nightreign-Save-Editor](https://github.com/alfizari/Elden-Ring-Nightreign-Save-Editor) (MIT licensed). We chose to copy and adapt just the data-layer modules (decryption, `SourceDataHandler`, `InventoryHandler`, the bundled `Resources/Param/*.csv` + `.fmg.xml` game data) into this repo, rather than:

- **Full git submodule dependency** — would pull in the GUI (`tkinter`, `Final.py`, `ui/`), PyInstaller build specs, and Excel import/export we don't need, and couples our read-only analysis tool to upstream's release cadence and any future GUI/editing-focused changes.
- **From-scratch reimplementation** — the byte-offset reverse engineering (AES key, BND4 layout, `ItemState`/`ItemEntry` struct offsets) is nontrivial prior art; redoing it independently would be pure risk with no benefit.

This repo is Apache-2.0 licensed; the vendored MIT-licensed files/data keep their original MIT license notice and attribution to alfizari and contributors (per MIT's terms), which is compatible with inclusion in an Apache-2.0 project.
