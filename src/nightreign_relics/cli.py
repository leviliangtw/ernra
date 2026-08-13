"""`nightreign-relics` CLI entrypoint.

Flow: parse args -> decrypt save -> pick Save Profile Slot -> parse owned
Relics -> load Catalog + bilingual names -> diagnose -> build report ->
write report -> optionally call the LLM directly.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .catalog.loader import Catalog
from .catalog.models import parse_hero_name
from .catalog.names import BilingualNames
from .illegal import diagnose_owned_relics
from .llm import DEFAULT_MODEL, call_anthropic
from .report import SaveMeta, build_report, write_report
from .save.bnd4 import decrypt_save
from .save.inventory import get_player_name, parse_owned_relics
from .save.locator import (
    AmbiguousSavePathError,
    AmbiguousSlotError,
    find_populated_slots,
    populated_indices,
    resolve_save_path,
    resolve_slot,
)

logger = logging.getLogger(__name__)


def _default_resources_dir() -> Path:
    packaged = Path(__file__).parent / "resources"
    if packaged.is_dir():
        return packaged
    dev = Path(__file__).resolve().parents[2] / "resources"
    if dev.is_dir():
        return dev
    raise FileNotFoundError("Could not locate the bundled resources/ directory. Pass --resources-dir explicitly.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nightreign-relics",
        description=(
            "Decrypt an Elden Ring Nightreign save, dump owned Relics with "
            "diagnostic flags, and hand the result to an LLM for a Vessel + "
            "Relic loadout recommendation."
        ),
    )
    parser.add_argument("--hero", required=True, help="Target Hero, e.g. Wylder (case-insensitive).")
    parser.add_argument(
        "--playstyle",
        required=True,
        help='Free-text playstyle description, e.g. "我要爆發輸出". Pass "-" to read from stdin.',
    )
    parser.add_argument("--save-path", type=Path, default=None, help="Override the auto-detected NR0000.sl2 path.")
    parser.add_argument(
        "--slot",
        default=None,
        help="Save Profile Slot index (0-9) or player name; prompted for if omitted and more than one slot has data.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Where to write the JSON report.")
    parser.add_argument("--call-llm", action="store_true", help="Also call the Anthropic API directly for a recommendation.")
    parser.add_argument("--api-key", default=None, help="Anthropic API key; falls back to the ANTHROPIC_API_KEY env var.")
    parser.add_argument("--provider", choices=["anthropic"], default="anthropic")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--llm-output", type=Path, default=None, help="Where to write the LLM's recommendation text.")
    parser.add_argument(
        "--resources-dir", type=Path, default=None, help="Override the bundled game-data directory (mainly for tests)."
    )
    parser.add_argument(
        "--no-interactive", action="store_true", help="Fail instead of prompting on ambiguous Save Profile Slot selection."
    )
    return parser


def _read_playstyle(raw: str) -> str:
    if raw == "-":
        return sys.stdin.read().strip()
    return raw


def _prompt_for_slot(indices: list[int], names: dict[int, str | None]) -> int:
    print("Multiple Save Profile Slots have data:")
    for idx in indices:
        print(f"  [{idx}] {names.get(idx) or '(unnamed)'}")
    while True:
        choice = input("Pick a slot index: ").strip()
        try:
            value = int(choice)
        except ValueError:
            print("Enter a number.")
            continue
        if value in indices:
            return value
        print(f"{value} is not one of {indices}.")


def _resolve_slot_index(
    populated: tuple[bool, ...],
    requested: str | None,
    decrypted: dict[str, bytes],
    no_interactive: bool,
) -> int:
    indices = populated_indices(populated)

    if requested is not None:
        try:
            requested_index = int(requested)
        except ValueError:
            for idx in indices:
                name = get_player_name(decrypted[f"USERDATA_{idx}"])
                if name and name.lower() == requested.lower():
                    return idx
            raise ValueError(f"No populated Save Profile Slot has player name {requested!r}.")
        return resolve_slot(populated, requested_index)

    try:
        return resolve_slot(populated, None)
    except AmbiguousSlotError:
        if no_interactive:
            raise
        names = {idx: get_player_name(decrypted[f"USERDATA_{idx}"]) for idx in indices}
        return _prompt_for_slot(indices, names)


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        hero = parse_hero_name(args.hero)
    except ValueError as exc:
        parser.error(str(exc))

    playstyle = _read_playstyle(args.playstyle)

    try:
        save_path = resolve_save_path(args.save_path)
    except (AmbiguousSavePathError, FileNotFoundError) as exc:
        parser.error(str(exc))

    decrypted = decrypt_save(save_path)
    populated = find_populated_slots(decrypted["USERDATA_10"])

    try:
        slot_index = _resolve_slot_index(populated, args.slot, decrypted, args.no_interactive)
    except (AmbiguousSlotError, ValueError) as exc:
        parser.error(str(exc))

    userdata = decrypted[f"USERDATA_{slot_index}"]
    owned = parse_owned_relics(userdata)
    slot_player_name = get_player_name(userdata)

    resources_dir = args.resources_dir or _default_resources_dir()
    catalog = Catalog.load(resources_dir)
    names = BilingualNames.load(resources_dir / "Text")

    diagnostics = diagnose_owned_relics(owned, catalog)

    save_meta = SaveMeta(
        save_path=save_path,
        slot_index=slot_index,
        slot_player_name=slot_player_name,
        populated_slots=populated_indices(populated),
    )
    report = build_report(
        hero=hero,
        owned=owned,
        diagnostics=diagnostics,
        catalog=catalog,
        names=names,
        playstyle=playstyle,
        save_meta=save_meta,
    )

    output_path = args.output or Path(f"nightreign-report-{hero.value.lower()}-{_timestamp_slug()}.json")
    write_report(report, output_path)
    print(f"Report written to {output_path}")
    print("Paste it into Claude Code chat for a recommendation, or re-run with --call-llm.")

    if args.call_llm:
        api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            parser.error("--call-llm requires --api-key or the ANTHROPIC_API_KEY environment variable.")
        recommendation = call_anthropic(report, playstyle, api_key, args.model)
        llm_output_path = args.llm_output or Path(f"nightreign-recommendation-{hero.value.lower()}-{_timestamp_slug()}.md")
        llm_output_path.write_text(recommendation, encoding="utf-8")
        print(f"Recommendation written to {llm_output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
