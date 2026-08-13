# Adapted from alfizari/Elden-Ring-Nightreign-Save-Editor (MIT License).
# See /THIRD_PARTY_NOTICES for the full license text.
"""Load the Relic/Effect/Vessel Catalog from bundled game-data CSVs.

Replaces the reference project's pandas-based `SourceDataHandler` with plain
`csv.DictReader` + dataclasses: this tool only ever needs one-shot dict
lookups by ID, not a sortable/filterable table.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .models import COLOR_BY_INDEX, HERO_ALLOW_COLUMN, HERO_ORDER, Color, EffectDef, Hero, RelicDef, VesselDef


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _color(raw: str) -> Color:
    return COLOR_BY_INDEX[int(raw)]


def _load_relics(param_dir: Path) -> dict[int, RelicDef]:
    relics: dict[int, RelicDef] = {}
    for row in _read_csv_rows(param_dir / "EquipParamAntique.csv"):
        relic_id = int(row["ID"])
        relics[relic_id] = RelicDef(
            id=relic_id,
            color=_color(row["relicColor"]),
            is_deep=row["isDeepRelic"] == "1",
            is_salable=row["isSalable"] == "1",
            effect_pool_ids=(
                int(row["attachEffectTableId_1"]),
                int(row["attachEffectTableId_2"]),
                int(row["attachEffectTableId_3"]),
            ),
            curse_pool_ids=(
                int(row["attachEffectTableId_curse1"]),
                int(row["attachEffectTableId_curse2"]),
                int(row["attachEffectTableId_curse3"]),
            ),
        )
    return relics


def _load_effects(param_dir: Path) -> dict[int, EffectDef]:
    effects: dict[int, EffectDef] = {}
    for row in _read_csv_rows(param_dir / "AttachEffectParam.csv"):
        effect_id = int(row["ID"])
        allowed = frozenset(hero for hero in HERO_ORDER if row[HERO_ALLOW_COLUMN[hero]] == "1")
        effects[effect_id] = EffectDef(
            id=effect_id,
            text_id=int(row["attachTextId"]),
            compatibility_id=int(row["compatibilityId"]),
            sort_id=int(row["overrideEffectId"]),
            allowed_heroes=allowed,
        )
    return effects


def _load_vessels(param_dir: Path) -> dict[int, VesselDef]:
    vessels: dict[int, VesselDef] = {}
    for row in _read_csv_rows(param_dir / "AntiqueStandParam.csv"):
        vessel_id = int(row["ID"])
        slot_colors = (
            _color(row["relicSlot1"]),
            _color(row["relicSlot2"]),
            _color(row["relicSlot3"]),
            _color(row["deepRelicSlot1"]),
            _color(row["deepRelicSlot2"]),
            _color(row["deepRelicSlot3"]),
        )
        vessels[vessel_id] = VesselDef(
            id=vessel_id,
            hero_type=int(row["heroType"]),
            goods_id=int(row["goodsId"]),
            unlock_flag=int(row["unlockFlag"]),
            slot_colors=slot_colors,
        )
    return vessels


def _load_pool_rollable_effects(param_dir: Path) -> dict[int, frozenset[int]]:
    """Pool ID -> Effect IDs with nonzero roll weight in that pool."""
    pools: dict[int, set[int]] = {}
    for row in _read_csv_rows(param_dir / "AttachEffectTableParam.csv"):
        pool_id = int(row["ID"])
        effect_id = int(row["attachEffectId"])
        chance_weight = int(row["chanceWeight"])
        chance_weight_dlc = int(row["chanceWeight_dlc"])
        # chanceWeight_dlc, when >0, overrides the base chanceWeight for
        # whether an Effect can actually roll in this pool.
        rollable = chance_weight_dlc > 0 or (chance_weight != 0 and chance_weight_dlc == -1)
        if not rollable:
            continue
        pools.setdefault(pool_id, set()).add(effect_id)
    return {pool_id: frozenset(effect_ids) for pool_id, effect_ids in pools.items()}


@dataclass(frozen=True)
class Catalog:
    relics: dict[int, RelicDef]
    effects: dict[int, EffectDef]
    vessels: dict[int, VesselDef]
    pool_rollable_effects: dict[int, frozenset[int]]

    @classmethod
    def load(cls, resources_dir: Path) -> "Catalog":
        param_dir = resources_dir / "Param"
        return cls(
            relics=_load_relics(param_dir),
            effects=_load_effects(param_dir),
            vessels=_load_vessels(param_dir),
            pool_rollable_effects=_load_pool_rollable_effects(param_dir),
        )

    def vessels_for_hero(self, hero: Hero) -> list[VesselDef]:
        """Hero-specific Vessels plus universal ("All") Vessels, for one Hero."""
        hero_type = HERO_ORDER.index(hero) + 1
        return [v for v in self.vessels.values() if v.hero_type == hero_type or v.is_universal]
