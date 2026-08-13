"""Two-axis Relic-Hero Compatibility.

See CONTEXT.md's "Relic-Hero Compatibility" entry: a Relic is only useful to
a Hero if it passes BOTH checks:

1. Slot-level: the Relic's Color matches an available Vessel Slot's Color
   (or the Slot is White/wildcard) AND the Relic's Normal/Deep type matches
   that Slot's Normal/Deep position.
2. Effect-level: every Effect/Curse the Relic carries is allowed for that
   Hero in the game's Effect data.

These are independent — a Relic can pass one and fail the other.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from .catalog.loader import Catalog
from .catalog.models import EMPTY_EFFECT_IDS, Color, Hero, RelicDef, SlotKind, VesselDef

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SlotMatch:
    vessel_id: int
    slot_index: int
    slot_kind: SlotKind
    slot_color: Color


@dataclass(frozen=True)
class RelicHeroCompatibility:
    hero: Hero
    slot_eligible: bool
    matching_slots: list[SlotMatch]
    effect_eligible: bool
    failing_effect_ids: list[int]


def hero_vessels(catalog: Catalog, hero: Hero) -> list[VesselDef]:
    """A Hero's own Vessels plus universal ("All") Vessels."""
    return catalog.vessels_for_hero(hero)


def relic_matches_slot(relic: RelicDef, slot_color: Color, slot_kind: SlotKind) -> bool:
    color_ok = slot_color == Color.WHITE or relic.color == slot_color
    kind_ok = relic.is_deep == (slot_kind == "deep")
    return color_ok and kind_ok


def slot_level_compatibility(relic: RelicDef, vessels: Iterable[VesselDef]) -> list[SlotMatch]:
    matches: list[SlotMatch] = []
    for vessel in vessels:
        for slot_index, slot_kind, slot_color in vessel.slots():
            if relic_matches_slot(relic, slot_color, slot_kind):
                matches.append(
                    SlotMatch(
                        vessel_id=vessel.id,
                        slot_index=slot_index,
                        slot_kind=slot_kind,
                        slot_color=slot_color,
                    )
                )
    return matches


def effect_level_compatibility(
    effect_ids: Iterable[int], catalog: Catalog, hero: Hero
) -> tuple[bool, list[int]]:
    failing: list[int] = []
    for effect_id in effect_ids:
        if effect_id in EMPTY_EFFECT_IDS:
            continue
        effect_def = catalog.effects.get(effect_id)
        if effect_def is None:
            logger.warning("Unknown Effect ID %d; treating as universally allowed.", effect_id)
            continue
        if not effect_def.usable_by(hero):
            failing.append(effect_id)
    return (len(failing) == 0, failing)


def compute_compatibility(
    relic: RelicDef, effect_ids: Iterable[int], catalog: Catalog, hero: Hero
) -> RelicHeroCompatibility:
    vessels = hero_vessels(catalog, hero)
    matching_slots = slot_level_compatibility(relic, vessels)
    effect_eligible, failing_effect_ids = effect_level_compatibility(effect_ids, catalog, hero)
    return RelicHeroCompatibility(
        hero=hero,
        slot_eligible=len(matching_slots) > 0,
        matching_slots=matching_slots,
        effect_eligible=effect_eligible,
        failing_effect_ids=failing_effect_ids,
    )
