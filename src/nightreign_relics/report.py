"""Build and write the JSON report handed to the LLM.

Only owned Relics are included (not the full ~1400-entry game catalog) —
each carries its own resolved Catalog data plus diagnostic flags. Hero
compatibility isn't precomputed here (see ADR-0002); the reader derives it
from the Relic's Color/`is_deep`, `hero_vessels[].slots`, and each
Effect/Curse's `allowed_heroes`. See CONTEXT.md for terminology.

The report always embeds a `context` block (glossary, target Hero's kit
reference, a brief kit reference for all 10 Heroes, recommendation
guidance) from `context.py`, so it's self-contained even without
`--call-llm` — paste it into any LLM and it has the same grounding the
direct Anthropic call gets. Effects/Curses restricted to specific Heroes
also carry an `allowed_heroes` field so a reader can tell who a locked-out
Effect is actually for, instead of it being an opaque numeric ID.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import context as game_context
from .catalog.loader import Catalog
from .catalog.models import EMPTY_EFFECT_IDS, HERO_ORDER, Hero, VesselDef
from .catalog.names import BilingualNames
from .compatibility import hero_vessels
from .illegal import RelicDiagnostics
from .save.inventory import OwnedRelic

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2


@dataclass(frozen=True)
class SaveMeta:
    save_path: Path
    slot_index: int
    slot_player_name: str | None
    populated_slots: list[int]


def _effect_entries(effect_ids: tuple[int, int, int], catalog: Catalog, names: BilingualNames) -> list[dict]:
    entries: list[dict] = []
    for effect_id in effect_ids:
        if effect_id in EMPTY_EFFECT_IDS:
            continue
        effect_def = catalog.effects.get(effect_id)
        if effect_def is None:
            logger.warning("Unknown Effect ID %d on an owned Relic.", effect_id)
            entries.append({"id": effect_id, "name": {}})
            continue
        entry = {"id": effect_id, "name": names.effect_name(effect_def.text_id)}
        if not effect_def.is_universal:
            entry["allowed_heroes"] = [hero.value for hero in HERO_ORDER if hero in effect_def.allowed_heroes]
        entries.append(entry)
    return entries


def _vessel_dict(vessel: VesselDef, names: BilingualNames) -> dict:
    return {
        "vessel_id": vessel.id,
        "name": names.vessel_name(vessel.goods_id),
        "hero": vessel.hero.value if vessel.hero is not None else "ALL",
        "unlock_flag": vessel.unlock_flag,
        "slots": [{"index": index, "kind": kind, "color": color.value} for index, kind, color in vessel.slots()],
    }


def build_report(
    *,
    hero: Hero,
    owned: list[OwnedRelic],
    diagnostics: dict[int, RelicDiagnostics],
    catalog: Catalog,
    names: BilingualNames,
    playstyle: str,
    save_meta: SaveMeta,
) -> dict:
    vessels = hero_vessels(catalog, hero)

    owned_entries: list[dict] = []
    for relic in owned:
        relic_def = catalog.relics.get(relic.catalog_id)
        if relic_def is None:
            logger.warning(
                "Owned relic 0x%08X references unknown Catalog ID %d; skipping.",
                relic.ga_handle,
                relic.catalog_id,
            )
            continue

        diag = diagnostics.get(relic.ga_handle)

        owned_entries.append(
            {
                "ga_handle": f"0x{relic.ga_handle:08X}",
                "catalog_id": relic.catalog_id,
                "name": names.relic_name(relic.catalog_id),
                "color": relic_def.color.value,
                "is_deep": relic_def.is_deep,
                "is_favorite": relic.is_favorite,
                "effects": _effect_entries(relic.effects, catalog, names),
                "curses": _effect_entries(relic.curses, catalog, names),
                "diagnostics": {
                    "is_illegal": diag.is_illegal if diag else False,
                    "illegal_reason": diag.illegal_reason.name if diag and diag.illegal_reason else None,
                    "is_unique": diag.is_unique if diag else False,
                },
            }
        )

    context_block = {
        "glossary": game_context.GLOSSARY,
        "hero_kit": game_context.hero_kit_dict(hero),
        "all_heroes_kit": game_context.all_heroes_kit_dict(),
        "recommendation_guidance": game_context.RECOMMENDATION_GUIDANCE,
    }
    community_notes = game_context.community_notes_dict(hero)
    if community_notes is not None:
        context_block["community_notes"] = community_notes

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hero": hero.value,
        "playstyle": playstyle,
        "context": context_block,
        "save": {
            "save_path": str(save_meta.save_path),
            "slot_index": save_meta.slot_index,
            "slot_player_name": save_meta.slot_player_name,
            "populated_slots": save_meta.populated_slots,
        },
        "hero_vessels": [_vessel_dict(v, names) for v in vessels],
        "owned_relics": owned_entries,
    }


def write_report(report: dict, output_path: Path) -> None:
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
