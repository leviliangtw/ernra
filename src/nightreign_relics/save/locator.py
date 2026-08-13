# Adapted from alfizari/Elden-Ring-Nightreign-Save-Editor (MIT License).
# See /THIRD_PARTY_NOTICES for the full license text.
"""Locate a Nightreign save file, and pick which Save Profile Slot to use.

A `.sl2` save can hold up to 10 independent Save Profile Slots
(`USERDATA_0`..`USERDATA_9`), each a separately-named playthrough with its
own full set of Heroes and Relics. `USERDATA_10` ("the regulation slot")
holds, among other things, a 10-byte flag array saying which of those slots
actually have data — that's what `find_populated_slots` reads.
"""

from __future__ import annotations

import re
import struct
from pathlib import Path

_CHARACTER_SLOTS_MAGIC = re.compile(b"'\x00\x00FACE")
_CHARACTER_SLOTS_MAGIC_OFFSET = -61


class SavePathNotFoundError(FileNotFoundError):
    """Raised when no Nightreign save file could be auto-detected."""


class AmbiguousSavePathError(ValueError):
    def __init__(self, candidates: list[Path]):
        self.candidates = candidates
        super().__init__(
            "Multiple Nightreign save files found; pass --save-path to pick one: "
            + ", ".join(str(c) for c in candidates)
        )


class AmbiguousSlotError(ValueError):
    def __init__(self, populated_indices: list[int]):
        self.populated_indices = populated_indices
        super().__init__(
            "Multiple Save Profile Slots have data; pass --slot to pick one: "
            + ", ".join(str(i) for i in populated_indices)
        )


class SlotNotPopulatedError(ValueError):
    def __init__(self, slot_index: int):
        super().__init__(f"Save Profile Slot {slot_index} has no data.")


def default_save_paths() -> list[Path]:
    """Glob the standard Steam save location, natively and under WSL's /mnt mounts."""
    candidates: list[Path] = []

    import os

    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.extend(Path(appdata, "Nightreign").glob("*/NR0000.sl2"))

    mnt = Path("/mnt")
    if mnt.is_dir():
        for drive in mnt.glob("*"):
            candidates.extend(
                drive.glob("Users/*/AppData/Roaming/Nightreign/*/NR0000.sl2")
            )

    seen: set[Path] = set()
    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(candidate)
    return unique


def resolve_save_path(explicit: Path | None) -> Path:
    """Return the save path to use: `explicit` if given, else auto-detected.

    Raises SavePathNotFoundError if none is found, or AmbiguousSavePathError
    if more than one candidate exists and none was explicitly given.
    """
    if explicit is not None:
        if not explicit.is_file():
            raise SavePathNotFoundError(f"No such file: {explicit}")
        return explicit

    candidates = default_save_paths()
    if not candidates:
        raise SavePathNotFoundError(
            "No Nightreign save file found at the standard Steam location. "
            "Pass --save-path to point at your NR0000.sl2 directly."
        )
    if len(candidates) > 1:
        raise AmbiguousSavePathError(candidates)
    return candidates[0]


def find_populated_slots(userdata10: bytes) -> tuple[bool, ...]:
    """Which of the 10 Save Profile Slots (USERDATA_0..9) have data.

    Reads the decrypted USERDATA_10 ("regulation") entry.
    """
    for match in _CHARACTER_SLOTS_MAGIC.finditer(userdata10):
        offset = match.start() + _CHARACTER_SLOTS_MAGIC_OFFSET
        if not (0 <= offset <= len(userdata10) - 10):
            continue
        slots = struct.unpack_from("<10B", userdata10, offset)
        if any(value not in (0, 1) for value in slots):
            continue
        return tuple(value == 1 for value in slots)
    raise ValueError("Unable to determine populated Save Profile Slots (magic pattern not found).")


def populated_indices(populated: tuple[bool, ...]) -> list[int]:
    return [i for i, is_populated in enumerate(populated) if is_populated]


def resolve_slot(populated: tuple[bool, ...], requested: int | None) -> int:
    """Pick a Save Profile Slot index.

    If `requested` is given, validate it's populated and return it. Otherwise,
    auto-pick if exactly one slot is populated; raise AmbiguousSlotError if
    more than one is (the caller should prompt, or re-invoke with `--slot`).
    """
    indices = populated_indices(populated)
    if requested is not None:
        if requested not in range(10):
            raise ValueError(f"Slot index must be 0-9, got {requested}.")
        if requested not in indices:
            raise SlotNotPopulatedError(requested)
        return requested

    if not indices:
        raise ValueError("No Save Profile Slot has data.")
    if len(indices) > 1:
        raise AmbiguousSlotError(indices)
    return indices[0]
