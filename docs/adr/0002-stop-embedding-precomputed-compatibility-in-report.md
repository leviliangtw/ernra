# Stop embedding precomputed Relic-Hero Compatibility in the LLM report

`report.py` used to attach a precomputed `compatibility` block (`slot_eligible`/`effect_eligible`/`matching_slots`/`failing_effect_ids`) to every owned Relic entry. We decided to drop that block and let the LLM derive both axes itself from raw fields already present elsewhere in the report — `owned_relics[].color`/`is_deep` against `hero_vessels[].slots`, and `effects[].allowed_heroes` (omitted = universally usable) — rather than pre-computing and annotating it in code. Motivation: the annotation didn't just cost tokens, it added structured detail on top of data the LLM already has to read anyway, and that extra structure was judged to be noise competing with the model's own judgment rather than a help to it.

## Considered Options

- **Keep the precomputed block as-is** — safest for correctness (deterministic, can't be mis-derived), but keeps the report larger and denser than the alternatives.
- **Pre-filter `owned_relics` using the slot-level check, keep effect-level as annotation** — reduces report size by dropping physically-inequippable Relics outright. Rejected for now: no evidence yet that report size from unfiltered Relics is the actual problem, and it re-introduces a precomputed field for the effect axis.
- **Drop the block entirely (chosen)** — smallest report, most trust placed in the LLM's reasoning over the two independent axes.

## Consequences

- `compatibility.py`'s two-axis functions (`compute_compatibility`, `slot_level_compatibility`, `effect_level_compatibility`) are intentionally kept but are no longer called from any production path — only `hero_vessels()` still is (for listing a Hero's own Vessels). They remain as tested library code for a possible future non-LLM use (e.g. a CLI filtering feature), not dead code to delete.
- `context.py`'s `compatibility_axes` glossary entry and `RECOMMENDATION_GUIDANCE` were trimmed from an algorithm walkthrough to a single reminder sentence — the same "less structure, trust the model" call, applied to the prompt as well as the report.
- The Relic-Hero Compatibility domain concept in `CONTEXT.md` is unaffected — it describes the game mechanic, not this report's shape.
