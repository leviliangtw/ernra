from nightreign_relics.catalog.hero_lore import HERO_LORE
from nightreign_relics.catalog.models import HERO_ORDER
from nightreign_relics.llm import build_user_prompt


def test_hero_lore_covers_every_hero():
    assert set(HERO_LORE.keys()) == set(HERO_ORDER)
    for lore in HERO_LORE.values():
        assert lore.passive
        assert lore.weapon_focus
        assert lore.skill
        assert lore.ultimate
        assert lore.role


def test_build_user_prompt_includes_playstyle_and_report():
    report = {"hero": "Wylder", "owned_relics": [], "hero_vessels": []}
    prompt = build_user_prompt(report, "我要當救護車")

    assert "我要當救護車" in prompt
    assert '"hero": "Wylder"' in prompt
