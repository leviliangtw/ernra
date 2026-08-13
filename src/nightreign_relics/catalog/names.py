# Adapted from alfizari/Elden-Ring-Nightreign-Save-Editor (MIT License).
# See /THIRD_PARTY_NOTICES for the full license text.
"""Bilingual (en_US + zh_TW) name lookups from the game's `.fmg.xml` text files.

Unlike the reference project's `SourceDataHandler`, which loads one language
into shared instance state at a time, this loads both locales simultaneously
into plain dicts, since the report output is always bilingual.

Name IDs:
- Relic names are keyed by the Relic Catalog ID itself (`AntiqueName.fmg.xml`).
- Effect names are keyed by `EffectDef.text_id` (`attachTextId`), NOT the
  Effect ID (`AttachEffectName.fmg.xml`).
- Vessel names are keyed by `VesselDef.goods_id`, filtered to the 9600-9956
  range that actually holds Vessel display names (`GoodsName.fmg.xml`).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

LOCALES = ("en_US", "zh_TW")

_NULL_TEXT = "%null%"
_VESSEL_GOODS_ID_RANGE = range(9600, 9957)


def _parse_fmg_xml(path: Path) -> dict[int, str]:
    if not path.exists():
        return {}
    tree = ET.parse(path)
    result: dict[int, str] = {}
    for text_el in tree.getroot().findall("./entries/text"):
        id_attr = text_el.get("id")
        if id_attr is None:
            continue
        text = text_el.text
        if text is None or text == _NULL_TEXT:
            continue
        result[int(id_attr)] = text
    return result


def _load_merged(locale_dir: Path, base_name: str) -> dict[int, str]:
    merged = _parse_fmg_xml(locale_dir / f"{base_name}.fmg.xml")
    merged.update(_parse_fmg_xml(locale_dir / f"{base_name}_dlc01.fmg.xml"))
    return merged


NameMap = dict[int, dict[str, str]]


def _merge_locale_into(target: NameMap, locale: str, values: dict[int, str]) -> None:
    for id_, text in values.items():
        target.setdefault(id_, {})[locale] = text


@dataclass(frozen=True)
class BilingualNames:
    relic: NameMap
    """Relic Catalog ID -> {locale: name}."""
    effect: NameMap
    """Effect `text_id` (attachTextId) -> {locale: name}."""
    vessel: NameMap
    """Vessel `goods_id` -> {locale: name}."""

    @classmethod
    def load(cls, text_dir: Path) -> "BilingualNames":
        relic: NameMap = {}
        effect: NameMap = {}
        vessel: NameMap = {}
        for locale in LOCALES:
            locale_dir = text_dir / locale
            _merge_locale_into(relic, locale, _load_merged(locale_dir, "AntiqueName"))
            _merge_locale_into(effect, locale, _load_merged(locale_dir, "AttachEffectName"))
            goods = _load_merged(locale_dir, "GoodsName")
            vessel_names = {gid: text for gid, text in goods.items() if gid in _VESSEL_GOODS_ID_RANGE}
            _merge_locale_into(vessel, locale, vessel_names)
        return cls(relic=relic, effect=effect, vessel=vessel)

    def relic_name(self, relic_id: int) -> dict[str, str]:
        return self.relic.get(relic_id, {})

    def effect_name(self, text_id: int) -> dict[str, str]:
        return self.effect.get(text_id, {})

    def vessel_name(self, goods_id: int) -> dict[str, str]:
        return self.vessel.get(goods_id, {})
