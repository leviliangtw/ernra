"""Curated, concise per-Hero kit knowledge, sourced from the community wiki
(eldenringnightreign.wiki.fextralife.com), used to ground `llm.py`'s prompt
in real game mechanics instead of the model's own (sometimes wrong)
assumptions about a Hero's weapon focus or ability names.

None of this is in the game's bundled Param CSVs — it's narrative/kit
information, not save-format or Relic-Catalog data, so it lives here rather
than in `catalog/loader.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Hero


@dataclass(frozen=True)
class HeroLore:
    passive: str
    weapon_focus: str
    skill: str
    ultimate: str
    role: str


HERO_LORE: dict[Hero, HeroLore] = {
    Hero.WYLDER: HeroLore(
        passive="Sixth Sense: cheats death once - a would-be lethal hit is auto-dodged (status ailments still apply); resets at Sites of Grace/respawn",
        weapon_focus="Greatswords; balanced Strength/Dexterity, flexes into most melee weapons",
        skill="Claw Shot: grapples small enemies in or launches Wylder at large enemies/terrain (mobility/gap-closer)",
        ultimate="Onslaught Stake: single heavy strike + explosion; more charge = more damage/stance damage, no self-knockback",
        role="All-rounder melee/mobility Hero",
    ),
    Hero.GUARDIAN: HeroLore(
        passive="Steel Guard: plant feet and brace with shield for a more powerful guard",
        weapon_focus="Halberds; Strength-focused (B), high Vigor/Endurance",
        skill="Whirlwind: wing-beat creates a wind cyclone",
        ultimate="Wings of Salvation: leap and dive down to raise a protective area",
        role="Durable frontline tank: damage mitigation, crowd control, team protection",
    ),
    Hero.IRONEYE: HeroLore(
        passive="Eagle Eye: keen observation discovers more items obtained from foes",
        weapon_focus="Bows; high Dexterity (A), strong Arcane (B) for status effects",
        skill="Marking: dagger cut creates a temporary weak point (+10% damage taken)",
        ultimate="Single Shot: powerful sound-piercing, defense-ignoring arrow with impact AoE",
        role="Ranged archer: weakpoint marking for team damage amp, safe backline damage",
    ),
    Hero.DUCHESS: HeroLore(
        passive="Magnificent Poise: enables consecutive dodges with enhanced i-frames and speed",
        weapon_focus="Daggers; Dexterity (B) + Intelligence (A)",
        skill="Restage: reapplies 50% of recent damage dealt to nearby enemies",
        ultimate="Finale: grants self + allies ~15s invisibility",
        role="Agile assassin: rapid strikes, evasion, damage-amp + stealth support",
    ),
    Hero.RAIDER: HeroLore(
        passive="Fighter's Resolve: damage taken boosts Retaliate's potency and prevents knockdown while using it",
        weapon_focus="Colossal weapons, greataxes, great hammers; S-rank Strength",
        skill="Retaliate: attack stance with damage reduction, stronger when already damaged",
        ultimate="Totem Stela: summons a tombstone that buffs allies and damages enemies in an area",
        role="Slow heavy-hitting tank: face-tank + counteroffensive burst",
    ),
    Hero.REVENANT: HeroLore(
        passive="Necromancy: raise enemy ghosts to fight as allies",
        weapon_focus="Faith incantations/sacred seals; no fixed weapon preference",
        skill="Summon Spirit: summons up to 3 spectral allies (Helen/Frederick/Sebastian) to fight",
        ultimate="Immortal March: self + nearby allies become immortal for ~15s",
        role="Backline summoner/support: spectral allies + team-wide immortality window",
    ),
    Hero.RECLUSE: HeroLore(
        passive="Elemental Defense: discover affinity residues from enemies, collectible to replenish FP",
        weapon_focus="Staves/sacred seals; Intelligence + Faith both S-rank",
        skill="Magic Cocktail: collects affinity residues from targets, fires an affinity-exploiting spell",
        ultimate="Soulblood Song: brands nearby foes with sigils that heal HP/FP when struck",
        role="Ranged spellcaster: elemental damage combos, self-sustains FP via enemy interaction",
    ),
    Hero.EXECUTOR: HeroLore(
        passive="Tenacity: recovering from a status ailment grants ~20% attack power and stamina recovery for ~20s",
        weapon_focus="Katanas; Dexterity (S) + Arcane (S)",
        skill="Suncatcher: Sekiro-style no-cooldown parry/deflect",
        ultimate="Aspects of the Crucible: Beast: beast-form melee combos + roar + AoE slash",
        role="High-risk/high-reward duelist: precise deflection + status application, strong 1v1 burst",
    ),
    Hero.SCHOLAR: HeroLore(
        passive="Bagcraft: store additional resources; using items levels up their power/effect",
        weapon_focus="Thrusting swords; S-rank Arcane",
        skill="Analyze: studying an enemy builds a combat advantage over time",
        ultimate="Communion: damage shared among linked enemies, can heal linked allies",
        role="Tactical item/debuff support: item enhancement (Bagcraft) + battlefield control over raw damage",
    ),
    Hero.UNDERTAKER: HeroLore(
        passive="Confluence: an ally using their Art enables Undertaker to activate her own Art too, regardless of her gauge",
        weapon_focus="Hammers; Strength + Faith both A-rank",
        skill="Trance: temporary speed/poise/defense + attack power after consecutive hits",
        ultimate="Loathsome Hex: charging strike, usable mid-air for mobility+damage",
        role="Aggressive melee: heavy damage, synergizes with allies' ultimates to refresh her own",
    ),
}
