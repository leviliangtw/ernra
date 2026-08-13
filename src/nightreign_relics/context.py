"""Shared game-mechanics context: a short glossary plus recommendation
guidance, used by both `llm.py` (folded into the Anthropic system prompt for
`--call-llm`) and `report.py` (embedded directly in the JSON report for the
default no-`--call-llm` flow).

Without this, a "cold" LLM reading the report on its own — e.g. pasted into
Claude Code or another model — has no way to know what "Delicate/Polished/
Grand" mean, what the Art Gauge is, or that the two `compatibility` flags
are independent checks that both must pass. Keeping the wording here as the
single source means the API path and the paste-it-yourself path never
drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalog.hero_lore import HERO_LORE
from .catalog.models import HERO_ORDER, Hero

GLOSSARY: dict[str, str] = {
    "relic_quality_prefix": (
        "A Relic's name prefix encodes how many Effects it rolled: "
        "'Delicate' = 1, 'Polished' = 2, 'Grand' = 3."
    ),
    "resource_systems": (
        "FP fuels Weapon Skills (戰技/Ashes of War), Sorceries (魔法), and "
        "Incantations (禱告) only. A Hero's Character Skill and Ultimate Art "
        "do NOT consume FP - each instead fills its own gauge that "
        "passively recovers over time (the Ultimate Art's is the 'Art "
        "Gauge'; Character Skill recovers the same way, often described as "
        "a cooldown). Many Relic Effects speed up gauge fill further - on "
        "critical hits, kills, etc. - which is itself a form of burst "
        "damage/utility. Don't assume an 'FP regen' Relic Effect helps "
        "Skill or Ultimate Art uptime; it doesn't - only gauge-fill Effects do."
    ),
    "effect_conflict": (
        "A single Relic can't hold two Effects from the same family (e.g. "
        "two 'Attack Power Up' Effects). This is already enforced by the "
        "is_illegal diagnostic flag; don't re-derive it yourself."
    ),
    "compatibility_axes": (
        "Each owned Relic's `compatibility` block has two independent "
        "checks: slot_eligible (Color/Normal-Deep matches an available "
        "Vessel Slot) and effect_eligible (every Effect/Curse is allowed "
        "for this Hero). Only recommend a Relic where both are true."
    ),
    "effect_hero_restriction": (
        "Most Effects/Curses are usable by every Hero. The rare ones that "
        "aren't carry an `allowed_heroes` field listing exactly which "
        "Heroes can use them (the field is omitted when unrestricted). If "
        "an owned Relic fails effect_eligible, check its failing effect's "
        "`allowed_heroes` to see which other Hero it's actually meant for - "
        "cross-reference `context.all_heroes_kit` below for what that Hero "
        "does, rather than treating the Relic as simply broken."
    ),
}

RECOMMENDATION_GUIDANCE = (
    "Recommend exactly one Vessel and up to 6 owned Relics to fill its "
    "Slots, respecting each Slot's Color and Normal/Deep type, matched to "
    "both the player's stated playstyle and the Hero's actual kit (see "
    "hero_kit below) - favor Relics that suit their weapon focus, Skill, "
    "and Ultimate Art rather than discounting a weapon-specific Relic just "
    "because you're unsure what the player is using. Only recommend Relics "
    "where both slot_eligible and effect_eligible are true, and never "
    "recommend a Relic flagged is_illegal. Briefly explain your reasoning. "
    "Respond in the same language as the playstyle description."
)


def hero_kit_dict(hero: Hero) -> dict:
    lore = HERO_LORE[hero]
    return {
        "passive": lore.passive,
        "weapon_focus": lore.weapon_focus,
        "skill": lore.skill,
        "ultimate": lore.ultimate,
        "role": lore.role,
    }


def all_heroes_kit_dict() -> dict[str, dict]:
    """Brief kit reference for all 10 Heroes, not just the target one.

    Without this, a Relic Effect restricted to e.g. Guardian is meaningless
    noise to a reader who only knows about the target Hero - they can't
    judge whether that Effect (and by extension the Relic carrying it) is
    worth keeping for later, or why it's excluded here at all.
    """
    return {hero.value: hero_kit_dict(hero) for hero in HERO_ORDER}


@dataclass(frozen=True)
class CoreRelic:
    catalog_id: int
    name_zh_TW: str
    why: str


@dataclass(frozen=True)
class CommunityNotes:
    """Player-community build consensus for one Hero, distinct from
    `HERO_LORE`: this is informal, opinion-based, and can go stale after
    balance patches, whereas `HERO_LORE` is stable official kit info from
    the wiki. Kept as a separate, explicitly-labeled block so a reader (LLM
    or human) knows to weigh it as a starting bias, not authoritative data.
    """

    disclaimer: str
    core_relics: list[CoreRelic]
    build_variants: list[str]
    priority_principle: str


# Sourced from Traditional-Chinese PTT C_Chat board discussions:
# https://disp.cc/ptt/C_Chat/1ffTEmpf
# https://disp.cc/ptt/C_Chat/1ffaP9CP
# https://disp.cc/ptt/C_Chat/1ffehoF8
# Only Wylder has been researched so far - deliberately incomplete rather
# than guessed for the other 9 Heroes. Add more entries here as they're
# researched from equally concrete sources.
COMMUNITY_NOTES: dict[Hero, CommunityNotes] = {
    Hero.WYLDER: CommunityNotes(
        disclaimer=(
            "Player-community consensus (Traditional-Chinese PTT C_Chat "
            "board), not official game data. Reflects one point in time and "
            "may be outdated after balance patches. Treat as a starting "
            "bias, not a hard rule - still respect slot_eligible, "
            "effect_eligible, and is_illegal from the report before this."
        ),
        core_relics=[
            CoreRelic(
                catalog_id=2071,
                name_zh_TW="安定的遺志（紅安定）",
                why=(
                    "Melee Attack Up + Weapon Skill Attack Up + occasionally "
                    "negates an enemy attack when damage reduction drops"
                ),
            ),
            CoreRelic(
                catalog_id=2070,
                name_zh_TW="安定者的遺志（藍安定）",
                why="Melee Attack Up + Weapon Skill Attack Up + continuous FP regen",
            ),
            CoreRelic(
                catalog_id=11001,
                name_zh_TW="追蹤者的耳環",
                why=(
                    "Skill charge +1 (more Claw Shot uses), stamina restore on "
                    "hit, ignites the area on Ultimate Art use - considered "
                    "near-mandatory ('焊死') by the community"
                ),
            ),
        ],
        build_variants=[
            "Single Certainty (單安定) + a Night-Invasion damage buff: more flexible early on, leans on teammates for extra damage.",
            "Double Certainty (雙安定, both 2070 and 2071) + the Earring: highest ceiling, but demands strong parry/mechanical skill against minibosses (Black Blade, Samurai Hero, Grafted Nobility) and gives up early-game utility.",
            "Support ('道具追'): Earring + one Certainty + a Deep Relic HP/lifeline piece + kill-refunds-Art-Gauge + Skill-inflicts-Bleed; prioritizes Skill/Ultimate uptime and survivability over raw damage - closest fit for a rescue/support playstyle.",
        ],
        priority_principle=(
            "Community priority order for Relic effects on Wylder: Skill "
            "uptime > Ultimate Art uptime > survival, then raw damage - "
            "i.e. '活著才有輸出' (staying alive is what lets you deal damage "
            "at all)."
        ),
    ),
}


def community_notes_dict(hero: Hero) -> dict | None:
    """None if this Hero hasn't been researched yet - omit the key entirely
    in the report rather than emitting a misleading empty block."""
    notes = COMMUNITY_NOTES.get(hero)
    if notes is None:
        return None
    return {
        "disclaimer": notes.disclaimer,
        "core_relics": [
            {"catalog_id": r.catalog_id, "name_zh_TW": r.name_zh_TW, "why": r.why} for r in notes.core_relics
        ],
        "build_variants": notes.build_variants,
        "priority_principle": notes.priority_principle,
    }
