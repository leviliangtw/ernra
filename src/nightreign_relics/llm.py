"""Optional direct call to the Anthropic API for a full Vessel/Relic
recommendation. Only used when the CLI is run with `--call-llm`; the default
flow just writes the JSON report for the user to paste into Claude Code.
"""

from __future__ import annotations

import json

DEFAULT_MODEL = "claude-opus-5"

_SYSTEM_PROMPT = (
    "You are helping an Elden Ring Nightreign player choose a Relic loadout. "
    "You will be given a JSON report. Its `context` field carries a "
    "game-term glossary (including `compatibility_axes`), the target Hero's "
    "kit reference (weapon focus, Skill, Ultimate Art, role), and "
    "recommendation guidance - read and follow `context.recommendation_"
    "guidance` precisely. The rest of the report lists the Hero's available "
    "Vessels (each with 6 Relic Slots, a fixed Color and Normal/Deep type "
    "per Slot) and every Relic the player owns, each with diagnostic flags; "
    "work out Hero compatibility yourself from each Relic's Color/`is_deep` "
    "against the Vessel Slots and each Effect/Curse's `allowed_heroes`."
)


def build_user_prompt(report: dict, playstyle: str) -> str:
    return f"Playstyle: {playstyle}\n\nReport (JSON):\n{json.dumps(report, ensure_ascii=False, indent=2)}"


def call_anthropic(report: dict, playstyle: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    import anthropic  # lazy import: only required for --call-llm

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(report, playstyle)}],
    )

    if getattr(message, "stop_reason", None) == "refusal":
        raise RuntimeError("The model refused to answer this request.")

    text_blocks = [block.text for block in message.content if getattr(block, "type", None) == "text"]
    if not text_blocks:
        raise RuntimeError("The model returned no text content.")
    return "\n".join(text_blocks)
