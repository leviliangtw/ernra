from pathlib import Path

from nightreign_relics import context as game_context
from nightreign_relics.catalog.loader import Catalog
from nightreign_relics.catalog.models import HERO_ORDER, Hero
from nightreign_relics.catalog.names import BilingualNames
from nightreign_relics.report import SaveMeta, build_report
from nightreign_relics.save.inventory import OwnedRelic


def _save_meta() -> SaveMeta:
    return SaveMeta(
        save_path=Path("/tmp/NR0000.sl2"),
        slot_index=0,
        slot_player_name="Tester",
        populated_slots=[0],
    )


def test_report_embeds_context_for_default_no_call_llm_flow(resources_dir):
    catalog = Catalog.load(resources_dir)
    names = BilingualNames.load(resources_dir / "Text")

    report = build_report(
        hero=Hero.WYLDER,
        owned=[],
        diagnostics={},
        catalog=catalog,
        names=names,
        playstyle="我要當救護車",
        save_meta=_save_meta(),
    )

    assert "context" in report
    assert report["context"]["glossary"] == game_context.GLOSSARY
    assert report["context"]["hero_kit"] == game_context.hero_kit_dict(Hero.WYLDER)
    assert report["context"]["all_heroes_kit"] == game_context.all_heroes_kit_dict()
    assert set(report["context"]["all_heroes_kit"].keys()) == {h.value for h in HERO_ORDER}
    assert report["context"]["recommendation_guidance"] == game_context.RECOMMENDATION_GUIDANCE

    # 7 Hero-specific + 4 universal Vessels.
    assert len(report["hero_vessels"]) == 11
    assert report["owned_relics"] == []


def test_report_context_hero_kit_changes_per_hero(resources_dir):
    catalog = Catalog.load(resources_dir)
    names = BilingualNames.load(resources_dir / "Text")

    wylder_report = build_report(
        hero=Hero.WYLDER,
        owned=[],
        diagnostics={},
        catalog=catalog,
        names=names,
        playstyle="test",
        save_meta=_save_meta(),
    )
    guardian_report = build_report(
        hero=Hero.GUARDIAN,
        owned=[],
        diagnostics={},
        catalog=catalog,
        names=names,
        playstyle="test",
        save_meta=_save_meta(),
    )

    assert wylder_report["context"]["hero_kit"] != guardian_report["context"]["hero_kit"]


def test_wylder_report_includes_community_notes_with_real_catalog_ids(resources_dir):
    catalog = Catalog.load(resources_dir)
    names = BilingualNames.load(resources_dir / "Text")

    report = build_report(
        hero=Hero.WYLDER,
        owned=[],
        diagnostics={},
        catalog=catalog,
        names=names,
        playstyle="test",
        save_meta=_save_meta(),
    )

    notes = report["context"]["community_notes"]
    assert "disclaimer" in notes
    core_ids = {r["catalog_id"] for r in notes["core_relics"]}
    assert core_ids == {2070, 2071, 11001}
    # The catalog_ids referenced must actually exist as real Relics.
    for relic_id in core_ids:
        assert relic_id in catalog.relics


def test_hero_restricted_effect_carries_allowed_heroes_annotation(resources_dir):
    catalog = Catalog.load(resources_dir)
    names = BilingualNames.load(resources_dir / "Text")

    # Find a real Effect restricted to exactly one Hero that isn't Wylder,
    # and a real (any) Relic to attach it to for the test.
    restricted_effect_id, restricted_effect = next(
        (eid, e)
        for eid, e in catalog.effects.items()
        if len(e.allowed_heroes) == 1 and Hero.WYLDER not in e.allowed_heroes
    )
    any_relic_id = next(iter(catalog.relics))

    owned = [
        OwnedRelic(
            ga_handle=0xC0000001,
            catalog_id=any_relic_id,
            effects=(restricted_effect_id, 0xFFFFFFFF, 0xFFFFFFFF),
            curses=(0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
            is_favorite=False,
            is_new=True,
        )
    ]

    report = build_report(
        hero=Hero.WYLDER,
        owned=owned,
        diagnostics={},
        catalog=catalog,
        names=names,
        playstyle="test",
        save_meta=_save_meta(),
    )

    relic_entry = report["owned_relics"][0]
    effect_entry = relic_entry["effects"][0]
    assert effect_entry["id"] == restricted_effect_id
    assert effect_entry["allowed_heroes"] == [h.value for h in HERO_ORDER if h in restricted_effect.allowed_heroes]
    assert "Wylder" not in effect_entry["allowed_heroes"]

    # No precomputed compatibility block - the reader derives eligibility
    # from the raw Color/is_deep/allowed_heroes fields instead (ADR-0002).
    assert "compatibility" not in relic_entry


def test_universal_effect_omits_allowed_heroes_key(resources_dir):
    catalog = Catalog.load(resources_dir)
    names = BilingualNames.load(resources_dir / "Text")

    universal_effect_id = next(eid for eid, e in catalog.effects.items() if e.is_universal and eid != 0)
    any_relic_id = next(iter(catalog.relics))

    owned = [
        OwnedRelic(
            ga_handle=0xC0000002,
            catalog_id=any_relic_id,
            effects=(universal_effect_id, 0xFFFFFFFF, 0xFFFFFFFF),
            curses=(0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
            is_favorite=False,
            is_new=True,
        )
    ]

    report = build_report(
        hero=Hero.WYLDER,
        owned=owned,
        diagnostics={},
        catalog=catalog,
        names=names,
        playstyle="test",
        save_meta=_save_meta(),
    )

    effect_entry = report["owned_relics"][0]["effects"][0]
    assert "allowed_heroes" not in effect_entry


def test_heroes_without_researched_community_notes_omit_the_key(resources_dir):
    catalog = Catalog.load(resources_dir)
    names = BilingualNames.load(resources_dir / "Text")

    report = build_report(
        hero=Hero.GUARDIAN,
        owned=[],
        diagnostics={},
        catalog=catalog,
        names=names,
        playstyle="test",
        save_meta=_save_meta(),
    )

    assert "community_notes" not in report["context"]
