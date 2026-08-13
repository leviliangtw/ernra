# Nightreign Relic Analysis Tool

Dumps a player's *Elden Ring Nightreign* save data into structured form and hands it to an LLM to recommend Relic/Vessel loadouts, replacing manual sorting through the in-game Relic inventory.

## Language

**Relic**:
A collectible item with up to 3 Effects and up to 3 Curses, one of five Colors (Red/Blue/Yellow/Green/White), and a Normal or Deep variant. Sourced from the game's `EquipParamAntique` data. Called "Antique" internally by the game data, but "Relic" is the in-game player-facing term and the one to use.
_Avoid_: Antique, item

**Deep Relic**:
A Relic variant that only fits a Vessel's deep Slots and may carry Deep-only Effects, which require a paired Curse. Contrasts with a **Normal Relic**.
_Avoid_: Deep antique

**Effect**:
A single buff/property a Relic carries in one of its 3 non-curse slots. Some Effects are restricted to specific Heroes (see Relic-Hero Compatibility).
_Avoid_: Ability, stat, buff

**Curse**:
A drawback a Relic carries in one of its 3 curse slots, sometimes required as the cost of an Effect that is Deep-only.
_Avoid_: Debuff, penalty

**Vessel**:
A loadout container with 6 Relic Slots (3 Normal + 3 Deep), each Slot fixed to one Color (or wildcard). A Vessel belongs to one Hero, or is universal ("All") and usable by any Hero.
_Avoid_: Stand, container, loadout slot holder

**Slot**:
One of a Vessel's 6 fixed positions that a Relic can be placed into; has a required Color and a Normal/Deep type that a Relic must match to be placed there.
_Avoid_: Socket

**Hero**:
One of the 10 playable characters (Wylder, Guardian, Ironeye, Duchess, Raider, Revenant, Recluse, Executor, Scholar, Undertaker). Distinct from a Save Profile Slot.
_Avoid_: Character, Nightfarer, class

**Relic-Hero Compatibility**:
Whether a given Relic can usefully go to a given Hero. Requires passing *both* independent checks: (1) Slot-level — the Relic's Color matches the target Slot's Color (or the Slot is wildcard) and its Normal/Deep type matches the Slot's type; (2) Effect-level — every Effect/Curse on the Relic is flagged as allowed for that Hero in the game's Effect data. A Relic can pass (1) and still fail (2), or vice versa.
_Avoid_: Relic eligibility (use for either check alone if disambiguation is needed), equippable

**Save Profile Slot**:
One of up to 10 independent, separately-named playthroughs that can coexist inside a single `NR0000.sl2` save file, each with its own complete set of 10 Heroes and their own Relic inventory. Distinct from a Hero.
_Avoid_: Character slot, save slot (ambiguous with Hero), profile

**Relic Catalog**:
The full space of Relic definitions that exist in the game itself, independent of what any player owns. Sourced from the game's bundled param data, not from a save file.
_Avoid_: Relic database, master list

**Owned Relic**:
A concrete Relic instance in a player's save inventory, with its own rolled Effects/Curses; a player may own duplicate Owned Relics of the same Catalog entry.
_Avoid_: Relic instance, inventory item

**Illegal Relic**:
An Owned Relic whose rolled Effects/Curses could not actually occur through normal gameplay for its Catalog entry — a data-quality flag, not a Relic property to recommend around.
_Avoid_: Invalid relic, corrupted relic
