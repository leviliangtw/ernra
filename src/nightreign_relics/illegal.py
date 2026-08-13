# Adapted from alfizari/Elden-Ring-Nightreign-Save-Editor (MIT License).
# See /THIRD_PARTY_NOTICES for the full license text.
"""Diagnostic flags for owned Relics: Illegal (rolled effects the game
couldn't actually produce) and Unique (can't be freely re-farmed).

Ports the read-only validity logic from `relic_checker.py`'s `RelicChecker`
and `inventory_handler.py`'s `set_illegal_relics`, adapted to the new
`Catalog` type. The reference project's auto-fix helpers (`get_valid_order`,
`find_replacement_effect`, `sort_effects`, ...) are intentionally not
ported — this tool only reports diagnostics, it never edits a save.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto, unique

from .catalog.loader import Catalog
from .catalog.models import EMPTY_EFFECT_IDS
from .save.inventory import OwnedRelic

RELIC_GROUPS: dict[str, tuple[int, int]] = {
    "store_102": (100, 199),
    "store_103": (200, 299),
    "unique_1": (1000, 2100),
    "unique_2": (10000, 19999),
    "illegal": (20000, 30035),
    "reward_0": (1000000, 1000999),
    "reward_1": (1001000, 1001999),
    "reward_2": (1002000, 1002999),
    "reward_3": (1003000, 1003999),
    "reward_4": (1004000, 1004999),
    "reward_5": (1005000, 1005999),
    "reward_6": (1006000, 1006999),
    "reward_7": (1007000, 1007999),
    "reward_8": (1008000, 1008999),
    "reward_9": (1009000, 1009999),
    "deep_102": (2000000, 2009999),
    "deep_103": (2010000, 2019999),
}

UNIQUENESS_IDS: frozenset[int] = frozenset(
    i
    for group_name in ("unique_1", "unique_2")
    for i in range(RELIC_GROUPS[group_name][0], RELIC_GROUPS[group_name][1] + 1)
)

_DEEP_POOLS = frozenset({2000000, 2100000, 2200000})
_CURSE_REQUIRED_POOL = 2000000
_CURSE_FREE_POOLS = frozenset({2100000, 2200000})

_POSSIBLE_SEQUENCES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (0, 2, 1),
    (1, 0, 2),
    (1, 2, 0),
    (2, 0, 1),
    (2, 1, 0),
)


@unique
class InvalidReason(IntEnum):
    VALIDATION_ERROR = -1
    NONE = 0
    IN_ILLEGAL_RANGE = auto()
    INVALID_ITEM = auto()
    EFF_MUST_EMPTY = auto()
    EFF_NOT_ASSIGNED = auto()
    EFF_NOT_IN_ROLLABLE_POOL = auto()
    EFF_CONFLICT = auto()
    CURSE_MUST_EMPTY = auto()
    CURSE_REQUIRED_BY_EFFECT = auto()
    CURSE_NOT_IN_ROLLABLE_POOL = auto()
    CURSE_CONFLICT = auto()
    CURSES_NOT_ENOUGH = auto()
    CURSE_SLOT_UNNECESSARY = auto()
    EFFS_NOT_SORTED = auto()


def is_curse_invalid(reason: InvalidReason) -> bool:
    return reason in (
        InvalidReason.CURSE_MUST_EMPTY,
        InvalidReason.CURSE_REQUIRED_BY_EFFECT,
        InvalidReason.CURSE_NOT_IN_ROLLABLE_POOL,
        InvalidReason.CURSE_CONFLICT,
        InvalidReason.CURSES_NOT_ENOUGH,
        InvalidReason.CURSE_SLOT_UNNECESSARY,
    )


class RelicChecker:
    """Read-only relic-effect validity checker, against a loaded `Catalog`."""

    RELIC_RANGE: tuple[int, int] = (100, 2013322)

    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self._effect_to_rollable_pools: dict[int, set[int]] = {}
        for pool_id, effect_ids in catalog.pool_rollable_effects.items():
            for effect_id in effect_ids:
                self._effect_to_rollable_pools.setdefault(effect_id, set()).add(pool_id)

    def _rollable_effects(self, pool_id: int) -> frozenset[int]:
        if pool_id == -1:
            return frozenset()
        if pool_id in _DEEP_POOLS:
            merged: set[int] = set()
            for deep_pool in _DEEP_POOLS:
                merged |= self.catalog.pool_rollable_effects.get(deep_pool, frozenset())
            return frozenset(merged)
        return self.catalog.pool_rollable_effects.get(pool_id, frozenset())

    def _effect_needs_curse(self, effect_id: int) -> bool:
        if effect_id in EMPTY_EFFECT_IDS:
            return False
        pools = self._effect_to_rollable_pools.get(effect_id, set())
        in_required = False
        in_free = False
        for pool in pools:
            if pool == effect_id:
                continue
            if pool == _CURSE_REQUIRED_POOL:
                in_required = True
            elif pool in _CURSE_FREE_POOLS:
                in_free = True
        return in_required and not in_free

    def _sequence_reasons(
        self, pools: tuple[int, int, int, int, int, int], effs: list[int], curses: list[int], seq: tuple[int, int, int]
    ) -> list[InvalidReason]:
        cur_effs = [effs[i] for i in seq]
        cur_curses = [curses[i] for i in seq]
        reasons: list[InvalidReason] = []
        for idx in range(3):
            eff = cur_effs[idx]
            pool = pools[idx]
            if pool == -1:
                reasons.append(InvalidReason.NONE if eff in EMPTY_EFFECT_IDS else InvalidReason.EFF_MUST_EMPTY)
            elif eff in EMPTY_EFFECT_IDS:
                reasons.append(InvalidReason.EFF_NOT_ASSIGNED)
            elif eff not in self._rollable_effects(pool):
                reasons.append(InvalidReason.EFF_NOT_IN_ROLLABLE_POOL)
            else:
                reasons.append(InvalidReason.NONE)
        for idx in range(3):
            curse = cur_curses[idx]
            eff = cur_effs[idx]
            curse_pool = pools[idx + 3]
            if curse_pool == -1:
                reasons.append(InvalidReason.NONE if curse in EMPTY_EFFECT_IDS else InvalidReason.CURSE_MUST_EMPTY)
            elif curse in EMPTY_EFFECT_IDS:
                reasons.append(
                    InvalidReason.CURSE_REQUIRED_BY_EFFECT
                    if self._effect_needs_curse(eff)
                    else InvalidReason.CURSE_SLOT_UNNECESSARY
                )
            elif curse not in self._rollable_effects(curse_pool):
                reasons.append(InvalidReason.CURSE_NOT_IN_ROLLABLE_POOL)
            else:
                reasons.append(InvalidReason.NONE)
        return reasons

    def check_invalidity(self, relic_id: int, effects: list[int]) -> InvalidReason:
        """`effects` is `[effect_1, effect_2, effect_3, curse_1, curse_2, curse_3]`."""
        if relic_id in range(RELIC_GROUPS["illegal"][0], RELIC_GROUPS["illegal"][1] + 1):
            return InvalidReason.IN_ILLEGAL_RANGE
        if relic_id not in range(self.RELIC_RANGE[0], self.RELIC_RANGE[1] + 1):
            return InvalidReason.INVALID_ITEM

        relic = self.catalog.relics.get(relic_id)
        if relic is None:
            return InvalidReason.VALIDATION_ERROR

        pools = relic.effect_pool_ids + relic.curse_pool_ids
        effs, curses = effects[:3], effects[3:]

        first_seq_reasons: list[InvalidReason] | None = None
        valid_found = False
        for seq in _POSSIBLE_SEQUENCES:
            reasons = self._sequence_reasons(pools, effs, curses, seq)
            if first_seq_reasons is None:
                first_seq_reasons = reasons
            if all(reason == InvalidReason.NONE for reason in reasons):
                valid_found = True
                break

        if not valid_found:
            assert first_seq_reasons is not None
            return next(
                (reason for reason in first_seq_reasons if reason != InvalidReason.NONE),
                InvalidReason.VALIDATION_ERROR,
            )

        deep_only_effects = sum(1 for eff in effs if self._effect_needs_curse(eff))
        curses_provided = sum(1 for curse in curses if curse not in EMPTY_EFFECT_IDS)
        if deep_only_effects > curses_provided:
            return InvalidReason.CURSES_NOT_ENOUGH

        conflict_ids: list[int] = []
        for idx, effect_id in enumerate(effects):
            if effect_id in EMPTY_EFFECT_IDS:
                continue
            effect_def = self.catalog.effects.get(effect_id)
            conflict_id = effect_def.compatibility_id if effect_def else -1
            if conflict_id in conflict_ids and conflict_id != -1:
                return InvalidReason.EFF_CONFLICT if idx < 3 else InvalidReason.CURSE_CONFLICT
            conflict_ids.append(conflict_id)

        sort_ids: list[float] = []
        for effect_id in effs:
            if effect_id in EMPTY_EFFECT_IDS:
                sort_ids.append(float("inf"))
            else:
                effect_def = self.catalog.effects.get(effect_id)
                sort_ids.append(float(effect_def.sort_id) if effect_def else float("inf"))
        sorted_effects = sorted(zip(sort_ids, effs), key=lambda pair: (pair[0], pair[1]))
        for i, (_sort_id, effect_id) in enumerate(sorted_effects):
            if effect_id != effs[i]:
                return InvalidReason.EFFS_NOT_SORTED

        return InvalidReason.NONE


@dataclass(frozen=True)
class RelicDiagnostics:
    ga_handle: int
    is_illegal: bool
    illegal_reason: InvalidReason | None
    """None when `is_illegal` is True but the cause is an extra duplicate
    copy of a Unique Relic, rather than an invalid effect roll."""
    is_unique: bool


def diagnose_owned_relics(owned: list[OwnedRelic], catalog: Catalog) -> dict[int, RelicDiagnostics]:
    checker = RelicChecker(catalog)

    base_reason: dict[int, InvalidReason] = {}
    illegal_gas: set[int] = set()
    for relic in owned:
        effects = list(relic.effects) + list(relic.curses)
        reason = checker.check_invalidity(relic.catalog_id, effects)
        base_reason[relic.ga_handle] = reason
        if reason != InvalidReason.NONE:
            illegal_gas.add(relic.ga_handle)

    by_catalog_id: dict[int, list[OwnedRelic]] = {}
    for relic in owned:
        by_catalog_id.setdefault(relic.catalog_id, []).append(relic)

    for catalog_id, relics in by_catalog_id.items():
        if catalog_id not in UNIQUENESS_IDS or len(relics) <= 1:
            continue
        legal_found = False
        for relic in relics:
            if relic.ga_handle in illegal_gas:
                continue
            if not legal_found:
                legal_found = True
                continue
            # A second-or-later *legal* copy of a Unique Relic shouldn't
            # exist; flag it illegal even though its own effects are valid.
            illegal_gas.add(relic.ga_handle)

    diagnostics: dict[int, RelicDiagnostics] = {}
    for relic in owned:
        reason = base_reason[relic.ga_handle]
        diagnostics[relic.ga_handle] = RelicDiagnostics(
            ga_handle=relic.ga_handle,
            is_illegal=relic.ga_handle in illegal_gas,
            illegal_reason=reason if reason != InvalidReason.NONE else None,
            is_unique=relic.catalog_id in UNIQUENESS_IDS,
        )
    return diagnostics
