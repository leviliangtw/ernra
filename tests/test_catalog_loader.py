from nightreign_relics.catalog.loader import Catalog
from nightreign_relics.catalog.models import HERO_ORDER
from nightreign_relics.catalog.names import BilingualNames


def test_catalog_loads_expected_row_counts(resources_dir):
    catalog = Catalog.load(resources_dir)
    assert len(catalog.relics) > 1000
    assert len(catalog.effects) > 1000
    assert len(catalog.vessels) == 74
    assert len(catalog.pool_rollable_effects) > 0


def test_hero_restricted_effect_flags_parse_correctly(resources_dir):
    catalog = Catalog.load(resources_dir)
    restricted = [e for e in catalog.effects.values() if len(e.allowed_heroes) == 1]
    assert restricted, "expected at least one hero-restricted Effect in the real data"
    for effect in restricted[:20]:
        assert effect.allowed_heroes <= frozenset(HERO_ORDER)
        assert not effect.is_universal

    universal = [e for e in catalog.effects.values() if e.is_universal]
    assert len(universal) > len(restricted)


def test_vessel_distribution_per_hero(resources_dir):
    catalog = Catalog.load(resources_dir)
    for index, hero in enumerate(HERO_ORDER):
        hero_specific = [v for v in catalog.vessels.values() if v.hero_type == index + 1]
        assert len(hero_specific) == 7, f"{hero} should have 7 Vessels"

    universal = [v for v in catalog.vessels.values() if v.is_universal]
    assert len(universal) == 4


def test_vessels_for_hero_combines_specific_and_universal(resources_dir):
    catalog = Catalog.load(resources_dir)
    wylder_vessels = catalog.vessels_for_hero(HERO_ORDER[0])
    assert len(wylder_vessels) == 11  # 7 Wylder-specific + 4 universal


def test_bilingual_names_resolve_for_same_id(resources_dir):
    names = BilingualNames.load(resources_dir / "Text")
    entry = names.relic_name(10)
    assert entry.get("en_US")
    assert entry.get("zh_TW")
