# nightreign-relics

A read-only command-line tool for *Elden Ring Nightreign* that decrypts your
save file, dumps your owned Relics for one Hero (annotated with which
Vessel/Relic slots they're actually eligible for), and hands that to an LLM
to recommend a Vessel + Relic loadout — so you don't have to manually sort
through your Relic inventory.

See [`CONTEXT.md`](./CONTEXT.md) for the domain glossary (Relic, Vessel,
Hero, Save Profile Slot, etc.), [`docs/relic-mechanics.md`](./docs/relic-mechanics.md)
for how the Relic/Vessel/compatibility system actually works and what to
look for when picking Relics (繁中), and [`docs/adr/`](./docs/adr/) for
architectural decisions.

## Install

```bash
uv sync
# or: python3 -m venv .venv && source .venv/bin/activate && pip install -e .
```

For the optional direct-LLM-call mode:

```bash
uv sync --extra llm
```

## Usage

```bash
# Default: writes a JSON report you can paste into Claude Code chat.
uv run nightreign-relics --hero Wylder --playstyle "我要當救護車，肉追與救援玩法"

# Advanced: script calls the Anthropic API directly for a full report.
uv run nightreign-relics --hero Wylder --playstyle "我要當救護車，肉追與救援玩法" \
    --call-llm --api-key sk-ant-...
```

`--hero` accepts any of the 10 Heroes, case-insensitive:

| Hero | 中文 |
|---|---|
| Wylder | 追蹤者 |
| Guardian | 守護者 |
| Ironeye | 鐵之眼 |
| Duchess | 女爵 |
| Raider | 無賴 |
| Revenant | 復仇者 |
| Recluse | 隱士 |
| Executor | 執行者 |
| Scholar | 學者 |
| Undertaker | 送葬者 |

The save file is auto-detected at the standard Steam location
(`%AppData%\Nightreign\<SteamID>\NR0000.sl2`, or its WSL-mounted
equivalent). Use `--save-path` to override. If your save contains more than
one populated Save Profile Slot, the tool will prompt you to pick one (or
pass `--slot`).

Run `nightreign-relics --help` for the full flag list.

## Data provenance

The bundled game-data files under `resources/` (relic/effect/vessel
definitions, localized names) and the save-decryption logic in
`src/nightreign_relics/save/` and `src/nightreign_relics/catalog/` are
adapted from the MIT-licensed
[alfizari/Elden-Ring-Nightreign-Save-Editor](https://github.com/alfizari/Elden-Ring-Nightreign-Save-Editor)
project. See [`THIRD_PARTY_NOTICES`](./THIRD_PARTY_NOTICES) and
[ADR 0001](./docs/adr/0001-vendor-extracted-modules-from-reference-editor.md).

## Development

```bash
uv sync --group dev
uv run pytest
```
