from nightreign_relics.catalog.loader import Catalog
from nightreign_relics.illegal import RELIC_GROUPS, InvalidReason, RelicChecker, UNIQUENESS_IDS, is_curse_invalid

_EMPTY_EFFECTS = [0xFFFFFFFF] * 6


def test_is_curse_invalid_membership():
    assert is_curse_invalid(InvalidReason.CURSES_NOT_ENOUGH) is True
    assert is_curse_invalid(InvalidReason.CURSE_MUST_EMPTY) is True
    assert is_curse_invalid(InvalidReason.EFF_CONFLICT) is False
    assert is_curse_invalid(InvalidReason.NONE) is False


def test_relic_id_in_illegal_range_is_rejected(resources_dir):
    catalog = Catalog.load(resources_dir)
    checker = RelicChecker(catalog)

    illegal_id = RELIC_GROUPS["illegal"][0]
    assert checker.check_invalidity(illegal_id, _EMPTY_EFFECTS) == InvalidReason.IN_ILLEGAL_RANGE


def test_relic_id_below_valid_range_is_rejected(resources_dir):
    catalog = Catalog.load(resources_dir)
    checker = RelicChecker(catalog)

    assert checker.check_invalidity(1, _EMPTY_EFFECTS) == InvalidReason.INVALID_ITEM


def test_uniqueness_ids_derived_from_relic_groups():
    unique_1 = range(RELIC_GROUPS["unique_1"][0], RELIC_GROUPS["unique_1"][1] + 1)
    unique_2 = range(RELIC_GROUPS["unique_2"][0], RELIC_GROUPS["unique_2"][1] + 1)
    assert unique_1.start in UNIQUENESS_IDS
    assert unique_2.start in UNIQUENESS_IDS
    assert 100 not in UNIQUENESS_IDS  # a store_102-range id, not unique


def test_known_valid_single_effect_relic_combo_from_real_catalog(resources_dir):
    """Find a real, non-deep, single-effect-slot Relic and a rollable Effect
    for it, and confirm the checker accepts that combination as legal."""
    catalog = Catalog.load(resources_dir)
    checker = RelicChecker(catalog)

    found = None
    for relic in catalog.relics.values():
        if relic.is_deep:
            continue
        if relic.effect_pool_ids[1] != -1 or relic.effect_pool_ids[2] != -1:
            continue
        if any(pool != -1 for pool in relic.curse_pool_ids):
            continue
        rollable = catalog.pool_rollable_effects.get(relic.effect_pool_ids[0])
        if not rollable:
            continue
        for effect_id in rollable:
            effects = [effect_id, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF]
            if checker.check_invalidity(relic.id, effects) == InvalidReason.NONE:
                found = (relic.id, effects)
                break
        if found:
            break

    assert found is not None, "expected at least one valid single-effect Relic/Effect combo in the real catalog"
