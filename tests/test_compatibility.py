from nightreign_relics.catalog.loader import Catalog
from nightreign_relics.catalog.models import HERO_ORDER, Color, EffectDef, Hero, RelicDef, VesselDef
from nightreign_relics.compatibility import compute_compatibility, effect_level_compatibility, relic_matches_slot


def _catalog(relics=None, effects=None, vessels=None) -> Catalog:
    return Catalog(relics=relics or {}, effects=effects or {}, vessels=vessels or {}, pool_rollable_effects={})


def _relic(id_: int, color: Color, is_deep: bool) -> RelicDef:
    curse_pools = (0, -1, -1) if is_deep else (-1, -1, -1)
    return RelicDef(id=id_, color=color, is_deep=is_deep, is_salable=True, effect_pool_ids=(0, 0, 0), curse_pool_ids=curse_pools)


def test_relic_matches_slot_white_is_wildcard():
    red_relic = _relic(1, Color.RED, is_deep=False)
    assert relic_matches_slot(red_relic, Color.WHITE, "normal") is True
    assert relic_matches_slot(red_relic, Color.RED, "normal") is True
    assert relic_matches_slot(red_relic, Color.BLUE, "normal") is False


def test_relic_matches_slot_respects_deep_vs_normal():
    normal_relic = _relic(1, Color.RED, is_deep=False)
    deep_relic = _relic(2, Color.RED, is_deep=True)

    assert relic_matches_slot(normal_relic, Color.RED, "normal") is True
    assert relic_matches_slot(normal_relic, Color.RED, "deep") is False
    assert relic_matches_slot(deep_relic, Color.RED, "deep") is True
    assert relic_matches_slot(deep_relic, Color.RED, "normal") is False


def test_effect_level_universal_effect_passes_for_every_hero():
    universal = EffectDef(id=100, text_id=1, compatibility_id=-1, sort_id=0, allowed_heroes=frozenset(HERO_ORDER))
    catalog = _catalog(effects={100: universal})
    for hero in HERO_ORDER:
        eligible, failing = effect_level_compatibility([100], catalog, hero)
        assert eligible is True
        assert failing == []


def test_effect_level_restricted_effect_fails_for_other_heroes():
    restricted = EffectDef(id=200, text_id=2, compatibility_id=-1, sort_id=0, allowed_heroes=frozenset({Hero.WYLDER}))
    catalog = _catalog(effects={200: restricted})

    eligible, failing = effect_level_compatibility([200], catalog, Hero.WYLDER)
    assert eligible is True
    assert failing == []

    for hero in HERO_ORDER:
        if hero is Hero.WYLDER:
            continue
        eligible, failing = effect_level_compatibility([200], catalog, hero)
        assert eligible is False
        assert failing == [200]


def test_effect_level_ignores_empty_slots():
    catalog = _catalog(effects={})
    eligible, failing = effect_level_compatibility([0, 0xFFFFFFFF], catalog, Hero.WYLDER)
    assert eligible is True
    assert failing == []


def test_compute_compatibility_slot_and_effect_axes_are_independent():
    relic = _relic(1, Color.RED, is_deep=False)
    restricted = EffectDef(id=200, text_id=2, compatibility_id=-1, sort_id=0, allowed_heroes=frozenset({Hero.GUARDIAN}))
    vessel = VesselDef(
        id=9600,
        hero_type=1,  # Wylder
        goods_id=9600,
        unlock_flag=0,
        slot_colors=(Color.RED, Color.WHITE, Color.BLUE, Color.GREEN, Color.WHITE, Color.YELLOW),
    )
    catalog = _catalog(relics={1: relic}, effects={200: restricted}, vessels={9600: vessel})

    compat = compute_compatibility(relic, [200, 0xFFFFFFFF, 0xFFFFFFFF], catalog, Hero.WYLDER)

    assert compat.slot_eligible is True  # Red matches slot 0 (Red) and slot 1 (White wildcard)
    assert compat.effect_eligible is False  # Effect 200 is Guardian-only
    assert compat.failing_effect_ids == [200]

    matched_slot_indices = {m.slot_index for m in compat.matching_slots}
    assert matched_slot_indices == {0, 1}
