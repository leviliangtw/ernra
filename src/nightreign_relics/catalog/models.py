"""Domain dataclasses for the Relic/Effect/Vessel Catalog.

See /CONTEXT.md for the definitions of Relic, Effect, Curse, Vessel, Slot,
Hero, and Relic-Hero Compatibility these types represent.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

EMPTY_EFFECT_IDS = frozenset({0, 0xFFFFFFFF})
"""Sentinel values meaning "this Effect/Curse slot is empty"."""


class Color(StrEnum):
    RED = "Red"
    BLUE = "Blue"
    YELLOW = "Yellow"
    GREEN = "Green"
    WHITE = "White"


COLOR_BY_INDEX: tuple[Color, ...] = (Color.RED, Color.BLUE, Color.YELLOW, Color.GREEN, Color.WHITE)


class Hero(StrEnum):
    WYLDER = "Wylder"
    GUARDIAN = "Guardian"
    IRONEYE = "Ironeye"
    DUCHESS = "Duchess"
    RAIDER = "Raider"
    REVENANT = "Revenant"
    RECLUSE = "Recluse"
    EXECUTOR = "Executor"
    SCHOLAR = "Scholar"
    UNDERTAKER = "Undertaker"


HERO_ORDER: tuple[Hero, ...] = (
    Hero.WYLDER,
    Hero.GUARDIAN,
    Hero.IRONEYE,
    Hero.DUCHESS,
    Hero.RAIDER,
    Hero.REVENANT,
    Hero.RECLUSE,
    Hero.EXECUTOR,
    Hero.SCHOLAR,
    Hero.UNDERTAKER,
)
"""Index i (0-based) corresponds to AntiqueStandParam `heroType` == i + 1."""

UNIVERSAL_HERO_TYPE = 11
"""`heroType` value on a Vessel usable by any Hero ("All")."""

HERO_ALLOW_COLUMN: dict[Hero, str] = {
    Hero.WYLDER: "allowWylder",
    Hero.GUARDIAN: "allowGuardian",
    Hero.IRONEYE: "allowIroneye",
    Hero.DUCHESS: "allowDuchess",
    Hero.RAIDER: "allowRaider",
    Hero.REVENANT: "allowRevenant",
    Hero.RECLUSE: "allowRecluse",
    Hero.EXECUTOR: "allowExecutor",
    Hero.SCHOLAR: "allowScholar",
    Hero.UNDERTAKER: "allowUndertaker",
}


def hero_from_type(hero_type: int) -> Hero:
    """Map an AntiqueStandParam-style `heroType` (1-10) to a Hero."""
    if hero_type not in range(1, 11):
        raise ValueError(f"heroType must be 1-10 for a specific Hero, got {hero_type}")
    return HERO_ORDER[hero_type - 1]


def parse_hero_name(raw: str) -> Hero:
    """Case-insensitive lookup of a Hero by name, for CLI input."""
    normalized = raw.strip().lower()
    for hero in HERO_ORDER:
        if hero.value.lower() == normalized:
            return hero
    raise ValueError(f"Unknown Hero {raw!r}. Choose one of: {', '.join(h.value for h in HERO_ORDER)}")


@dataclass(frozen=True)
class RelicDef:
    id: int
    color: Color
    is_deep: bool
    is_salable: bool
    effect_pool_ids: tuple[int, int, int]
    """`attachEffectTableId_1..3` — effect *pool* references, not fixed effects."""
    curse_pool_ids: tuple[int, int, int]
    """`attachEffectTableId_curse1..3`."""


@dataclass(frozen=True)
class EffectDef:
    id: int
    text_id: int
    compatibility_id: int
    sort_id: int
    allowed_heroes: frozenset[Hero]
    """The exact set of Heroes flagged as allowed in the game data. All 10
    means unrestricted; the game data sets all 10 flags true for the vast
    majority of Effects, only ~6% are restricted to a single Hero."""

    @property
    def is_universal(self) -> bool:
        return len(self.allowed_heroes) == len(HERO_ORDER)

    def usable_by(self, hero: Hero) -> bool:
        return hero in self.allowed_heroes


SlotKind = Literal["normal", "deep"]


@dataclass(frozen=True)
class VesselDef:
    id: int
    hero_type: int
    """1-10 for a specific Hero, 11 for a universal ("All") Vessel."""
    goods_id: int
    unlock_flag: int
    slot_colors: tuple[Color, Color, Color, Color, Color, Color]
    """(normal0, normal1, normal2, deep0, deep1, deep2)."""

    @property
    def is_universal(self) -> bool:
        return self.hero_type == UNIVERSAL_HERO_TYPE

    @property
    def hero(self) -> Hero | None:
        return None if self.is_universal else hero_from_type(self.hero_type)

    def slots(self) -> list[tuple[int, SlotKind, Color]]:
        """(slot_index 0-5, kind, color) for all 6 Slots."""
        return [
            (i, "normal" if i < 3 else "deep", color) for i, color in enumerate(self.slot_colors)
        ]
