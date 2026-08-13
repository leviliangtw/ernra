# Adapted from alfizari/Elden-Ring-Nightreign-Save-Editor (MIT License).
# See /THIRD_PARTY_NOTICES for the full license text.
"""Parse owned Relics out of one decrypted Save Profile Slot (`USERDATA_N`).

Rewritten as pure functions over an explicit `bytes` buffer (no shared
mutable `globals.data`, no singleton, no self-healing writes back into the
buffer) — this tool only ever reads a save, once, per run.
"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass

logger = logging.getLogger(__name__)

BASE_STATE_SIZE = 8
WEAPON_STATE_SIZE = 88
ARMOR_STATE_SIZE = 16
RELIC_STATE_SIZE = 80

ITEM_TYPE_EMPTY = 0x00000000
ITEM_TYPE_WEAPON = 0x80000000
ITEM_TYPE_ARMOR = 0x90000000
ITEM_TYPE_RELIC = 0xC0000000
ITEM_TYPE_GOODS = 0xB0000000

START_OFFSET = 0x14
STATE_SLOT_COUNT = 5120
ENTRY_SLOT_COUNT = 3065
ENTRY_SIZE = 14

_PLAYER_NAME_REGION = 0x94
_ENTRY_COUNT_REGION = 0x5B8


@dataclass(frozen=True)
class OwnedRelic:
    ga_handle: int
    catalog_id: int
    """Relic Catalog ID (`EquipParamAntique` row ID)."""
    effects: tuple[int, int, int]
    """Raw effect_1..3 IDs. `0` or `0xFFFFFFFF` mean an empty slot."""
    curses: tuple[int, int, int]
    """Raw curse_1..3 IDs. `0` or `0xFFFFFFFF` mean an empty slot."""
    is_favorite: bool
    is_new: bool


@dataclass(frozen=True)
class _StateRecord:
    ga_handle: int
    type_bits: int
    real_item_id: int
    effects: tuple[int, int, int]
    curses: tuple[int, int, int]
    size: int


def _read_state(buffer: bytes, offset: int) -> _StateRecord:
    ga_handle, item_id = struct.unpack_from("<II", buffer, offset)
    type_bits = ga_handle & 0xF0000000
    real_item_id = item_id & 0x00FFFFFF

    if ga_handle == 0:
        return _StateRecord(ga_handle, type_bits, real_item_id, (0, 0, 0), (0, 0, 0), BASE_STATE_SIZE)

    if type_bits == ITEM_TYPE_WEAPON:
        size = WEAPON_STATE_SIZE
    elif type_bits == ITEM_TYPE_ARMOR:
        size = ARMOR_STATE_SIZE
    elif type_bits == ITEM_TYPE_RELIC:
        size = RELIC_STATE_SIZE
    else:
        size = BASE_STATE_SIZE

    if type_bits != ITEM_TYPE_RELIC:
        return _StateRecord(ga_handle, type_bits, real_item_id, (0, 0, 0), (0, 0, 0), size)

    effect_1, effect_2, effect_3 = struct.unpack_from("<III", buffer, offset + 16)
    curse_1, curse_2, curse_3 = struct.unpack_from("<III", buffer, offset + 56)
    return _StateRecord(
        ga_handle, type_bits, real_item_id, (effect_1, effect_2, effect_3), (curse_1, curse_2, curse_3), size
    )


def _walk_states(buffer: bytes) -> tuple[dict[int, _StateRecord], int]:
    """Walk the fixed-count, variable-size Item State region.

    Returns (ga_handle -> state, cursor_after_states).
    """
    cursor = START_OFFSET
    states_by_handle: dict[int, _StateRecord] = {}
    for _ in range(STATE_SLOT_COUNT):
        state = _read_state(buffer, cursor)
        if state.ga_handle != 0:
            states_by_handle[state.ga_handle] = state
        cursor += state.size
    return states_by_handle, cursor


def parse_owned_relics(userdata: bytes) -> list[OwnedRelic]:
    """Parse every owned Relic (across all Vessels/Presets, not just equipped ones)."""
    states_by_handle, cursor = _walk_states(userdata)

    cursor += _PLAYER_NAME_REGION
    cursor += _ENTRY_COUNT_REGION
    entry_count_offset = cursor
    cursor += 4
    entry_offset = cursor

    owned: list[OwnedRelic] = []
    counted = 0
    for i in range(ENTRY_SLOT_COUNT):
        base = entry_offset + i * ENTRY_SIZE
        ga_handle, _item_amount, _acquisition_id = struct.unpack_from("<III", userdata, base)
        is_favorite = bool(userdata[base + 12])
        is_new = bool(userdata[base + 13])

        if ga_handle == 0:
            continue
        counted += 1

        if (ga_handle & 0xF0000000) != ITEM_TYPE_RELIC:
            continue

        state = states_by_handle.get(ga_handle)
        if state is None:
            logger.warning("Relic entry 0x%08X has no matching Item State; skipping.", ga_handle)
            continue

        owned.append(
            OwnedRelic(
                ga_handle=ga_handle,
                catalog_id=state.real_item_id,
                effects=state.effects,
                curses=state.curses,
                is_favorite=is_favorite,
                is_new=is_new,
            )
        )

    stored_count = struct.unpack_from("<I", userdata, entry_count_offset)[0]
    if counted != stored_count:
        logger.warning(
            "Item Entry count mismatch: counted %d, save reports %d. "
            "Continuing read-only; not attempting to correct the save.",
            counted,
            stored_count,
        )

    return owned


def get_player_name(userdata: bytes) -> str | None:
    """Read the Save Profile Slot's player-chosen name, or None if unset/empty."""
    _states_by_handle, cursor = _walk_states(userdata)
    cursor += _PLAYER_NAME_REGION

    max_chars = 16
    for cur in range(cursor, cursor + max_chars * 2, 2):
        if userdata[cur : cur + 2] == b"\x00\x00":
            max_chars = (cur - cursor) // 2
            break

    raw_name = userdata[cursor : cursor + max_chars * 2]
    name = raw_name.decode("utf-16-le", errors="ignore").rstrip("\x00")
    return name if name else None
