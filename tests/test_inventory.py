import struct

from nightreign_relics.save.inventory import (
    ENTRY_SIZE,
    ENTRY_SLOT_COUNT,
    ITEM_TYPE_RELIC,
    START_OFFSET,
    STATE_SLOT_COUNT,
    get_player_name,
    parse_owned_relics,
)

_GAP_AFTER_STATES = 0x94
_NAME_TO_ENTRY_COUNT_REGION = 0x5B8


def _relic_state_bytes(ga_handle: int, real_item_id: int, effects: tuple[int, int, int], curses: tuple[int, int, int]) -> bytes:
    data = bytearray(80)
    item_id = 0x80000000 | (real_item_id & 0x00FFFFFF)
    struct.pack_into("<I", data, 0, ga_handle)
    struct.pack_into("<I", data, 4, item_id)
    struct.pack_into("<I", data, 8, item_id)
    struct.pack_into("<I", data, 12, 0xFFFFFFFF)
    struct.pack_into("<III", data, 16, *effects)
    struct.pack_into("<III", data, 56, *curses)
    struct.pack_into("<I", data, 68, 0xFFFFFFFF)
    return bytes(data)


def _entry_bytes(ga_handle: int, item_amount: int = 1, acquisition_id: int = 1, is_favorite: bool = False, is_new: bool = True) -> bytes:
    data = bytearray(ENTRY_SIZE)
    struct.pack_into("<III", data, 0, ga_handle, item_amount, acquisition_id)
    data[12] = int(is_favorite)
    data[13] = int(is_new)
    return bytes(data)


def build_userdata(
    relics: list[tuple[int, int, tuple[int, int, int], tuple[int, int, int]]],
    player_name: str = "Tester",
    entry_count_override: int | None = None,
) -> bytearray:
    """Build a synthetic decrypted USERDATA buffer with the given owned Relics
    placed in the first N Item State / Item Entry slots."""
    buf = bytearray()
    buf += b"\x00" * START_OFFSET

    for i in range(STATE_SLOT_COUNT):
        if i < len(relics):
            ga, rid, eff, cur = relics[i]
            buf += _relic_state_bytes(ga, rid, eff, cur)
        else:
            buf += b"\x00" * 8

    buf += b"\x00" * _GAP_AFTER_STATES
    name_offset = len(buf)
    buf += b"\x00" * _NAME_TO_ENTRY_COUNT_REGION
    entry_count_offset = len(buf)

    name_bytes = player_name.encode("utf-16-le") + b"\x00\x00"
    buf[name_offset : name_offset + len(name_bytes)] = name_bytes

    count = entry_count_override if entry_count_override is not None else len(relics)
    buf += struct.pack("<I", count)
    assert len(buf) == entry_count_offset + 4

    for i in range(ENTRY_SLOT_COUNT):
        if i < len(relics):
            ga, _rid, _eff, _cur = relics[i]
            buf += _entry_bytes(ga)
        else:
            buf += b"\x00" * ENTRY_SIZE

    return buf


def test_parse_owned_relics_reads_known_effects():
    ga = ITEM_TYPE_RELIC | 1
    relics = [(ga, 1004017, (7000001, 0xFFFFFFFF, 0xFFFFFFFF), (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF))]
    userdata = build_userdata(relics)

    owned = parse_owned_relics(bytes(userdata))

    assert len(owned) == 1
    relic = owned[0]
    assert relic.ga_handle == ga
    assert relic.catalog_id == 1004017
    assert relic.effects == (7000001, 0xFFFFFFFF, 0xFFFFFFFF)
    assert relic.curses == (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
    assert relic.is_new is True
    assert relic.is_favorite is False


def test_parse_owned_relics_skips_non_relic_entries():
    userdata = build_userdata([])
    owned = parse_owned_relics(bytes(userdata))
    assert owned == []


def test_get_player_name_round_trips():
    userdata = build_userdata([], player_name="TestPlayer")
    assert get_player_name(bytes(userdata)) == "TestPlayer"


def test_entry_count_mismatch_is_non_fatal(caplog):
    ga = ITEM_TYPE_RELIC | 2
    relics = [(ga, 1004017, (7000001, 0xFFFFFFFF, 0xFFFFFFFF), (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF))]
    userdata = build_userdata(relics, entry_count_override=999)

    original = bytes(userdata)
    owned = parse_owned_relics(original)

    # Must not raise, must not mutate the input buffer, and must still return the relic.
    assert bytes(userdata) == original
    assert len(owned) == 1
