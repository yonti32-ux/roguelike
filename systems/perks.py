# systems/perks.py
"""
Perk system: small, modular bonuses that layer on top of HeroStats.

Design:
- Each perk is a Perk object with:
    id, name, description, unlock_level, branch, requires, grant_skills, apply_fn
- HeroStats stores only a list of perk ids.
- This module knows how to:
    * apply a perk to a HeroStats-like object
    * pick a few perk options on level up
    * (optionally) auto-assign perks (legacy helper)
    * describe a hero's perk list for UI

Branches (trees) so far:
- vitality: HP / tank line
- blade:    weapon / damage line
- ward:     defense / control line
- focus:    skill-power / “caster” line
- mobility: evasive / footwork line
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Iterable, Optional
import random

# Type alias for the apply function:
# it receives a hero_stats-like object that has `base` with StatBlock-ish fields.
ApplyFn = Callable[[object], None]


@dataclass
class Perk:
    id: str
    name: str
    description: str
    unlock_level: int = 1
    branch: str = "general"          # perk tree / path, e.g. "vitality", "blade"
    requires: List[str] = field(default_factory=list)  # prerequisite perk ids
    grant_skills: List[str] = field(default_factory=list)  # ids from systems.skills
    tags: List[str] = field(default_factory=list)
    apply_fn: Optional[ApplyFn] = None

    def apply(self, hero_stats: object) -> None:
        if self.apply_fn is not None:
            self.apply_fn(hero_stats)


# --- Perk registry ----------------------------------------------------------

_PERKS: Dict[str, Perk] = {}


def register(perk: Perk) -> None:
    if perk.id in _PERKS:
        # Overwrite if duplicated id; fine for early dev.
        pass
    _PERKS[perk.id] = perk


def get(perk_id: str) -> Perk:
    return _PERKS[perk_id]


def all_perks() -> Iterable[Perk]:
    return _PERKS.values()


# --- Concrete perk effects (stat changes) -----------------------------------


def _apply_toughness_1(hero_stats: object) -> None:
    hero_stats.base.max_hp += 10


def _apply_toughness_2(hero_stats: object) -> None:
    hero_stats.base.max_hp += 15


def _apply_toughness_3(hero_stats: object) -> None:
    hero_stats.base.max_hp += 20


def _apply_weapon_training_1(hero_stats: object) -> None:
    hero_stats.base.attack += 2


def _apply_weapon_training_2(hero_stats: object) -> None:
    hero_stats.base.attack += 2


def _apply_weapon_training_3(hero_stats: object) -> None:
    hero_stats.base.attack += 3


def _apply_iron_guard_1(hero_stats: object) -> None:
    hero_stats.base.defense += 1


def _apply_iron_guard_2(hero_stats: object) -> None:
    hero_stats.base.defense += 2


def _apply_battle_focus_1(hero_stats: object) -> None:
    hero_stats.base.skill_power += 0.15


def _apply_battle_focus_2(hero_stats: object) -> None:
    hero_stats.base.skill_power += 0.20


def _apply_fleet_footwork_1(hero_stats: object) -> None:
    # First mobility perk: slight defense bump + a touch of initiative
    hero_stats.base.defense += 1
    hero_stats.base.initiative += 2


def _apply_fleet_footwork_2(hero_stats: object) -> None:
    # Second mobility perk: more defense + a bit of HP + more initiative
    hero_stats.base.defense += 1
    hero_stats.base.max_hp += 5
    hero_stats.base.initiative += 3


# --- Regeneration perk effects --------------------------------------------

def _apply_stamina_regen_1(hero_stats: object) -> None:
    hero_stats.base.stamina_regen_bonus += 1


def _apply_stamina_regen_2(hero_stats: object) -> None:
    hero_stats.base.stamina_regen_bonus += 1


def _apply_mana_regen_1(hero_stats: object) -> None:
    hero_stats.base.mana_regen_bonus += 1


def _apply_mana_regen_2(hero_stats: object) -> None:
    hero_stats.base.mana_regen_bonus += 1


def _apply_vitality_flow(hero_stats: object) -> None:
    # Both stamina and mana regen
    hero_stats.base.stamina_regen_bonus += 1
    hero_stats.base.mana_regen_bonus += 1


# --- Other new perk effects -----------------------------------------------

def _apply_quick_reflexes(hero_stats: object) -> None:
    hero_stats.base.dodge_chance += 0.05


def _apply_precision_strike(hero_stats: object) -> None:
    hero_stats.base.crit_chance += 0.05


def _apply_iron_will(hero_stats: object) -> None:
    hero_stats.base.status_resist += 0.10


def _apply_swift_strike(hero_stats: object) -> None:
    # Faster attacks slightly improve both speed and initiative
    hero_stats.base.speed += 0.1
    hero_stats.base.initiative += 1


def _apply_quickstep_1(hero_stats: object) -> None:
    # New mobility perk: extra movement points and initiative
    # Reduced from +1 to +0.5 to make high movement rare
    hero_stats.base.movement_points_bonus += 0.5
    hero_stats.base.initiative += 2


def _apply_quickstep_2(hero_stats: object) -> None:
    # Stronger version: more movement and a bit more initiative
    # Reduced from +1 to +0.5 to make high movement rare
    hero_stats.base.movement_points_bonus += 0.5
    hero_stats.base.initiative += 3


def _apply_arcane_attunement(hero_stats: object) -> None:
    hero_stats.base.max_mana += 5
    hero_stats.base.mana_regen_bonus += 1


def _apply_endurance_training(hero_stats: object) -> None:
    hero_stats.base.max_stamina += 5
    hero_stats.base.stamina_regen_bonus += 1


# --- Skill slot expansion perks ---------------------------------------------

def _apply_combat_mastery(hero_stats: object) -> None:
    """Unlock 5th skill slot."""
    hero_stats.max_skill_slots += 1
    # Expand existing loadouts
    for loadout_name, slots in hero_stats.skill_loadouts.items():
        while len(slots) < hero_stats.max_skill_slots:
            slots.append(None)
    # Expand skill_slots for backward compatibility
    while len(hero_stats.skill_slots) < hero_stats.max_skill_slots:
        hero_stats.skill_slots.append(None)


def _apply_weapon_expertise(hero_stats: object) -> None:
    """Unlock 6th skill slot."""
    hero_stats.max_skill_slots += 1
    # Expand existing loadouts
    for loadout_name, slots in hero_stats.skill_loadouts.items():
        while len(slots) < hero_stats.max_skill_slots:
            slots.append(None)
    # Expand skill_slots for backward compatibility
    while len(hero_stats.skill_slots) < hero_stats.max_skill_slots:
        hero_stats.skill_slots.append(None)


def _apply_legendary_warrior(hero_stats: object) -> None:
    """Unlock 7th skill slot."""
    hero_stats.max_skill_slots += 1
    # Expand existing loadouts
    for loadout_name, slots in hero_stats.skill_loadouts.items():
        while len(slots) < hero_stats.max_skill_slots:
            slots.append(None)
    # Expand skill_slots for backward compatibility
    while len(hero_stats.skill_slots) < hero_stats.max_skill_slots:
        hero_stats.skill_slots.append(None)


# --- Perk trees -------------------------------------------------------------

# ----------------- Vitality tree -----------------

register(Perk(
    id="toughness_1",
    name="Toughness I",
    description="+10 Max HP.",
    unlock_level=2,
    branch="vitality",
    requires=[],
    tags=["defense", "survivability"],
    apply_fn=_apply_toughness_1,
))

register(Perk(
    id="toughness_2",
    name="Toughness II",
    description="+15 Max HP.",
    unlock_level=4,
    branch="vitality",
    requires=["toughness_1"],
    tags=["defense", "survivability"],
    apply_fn=_apply_toughness_2,
))

register(Perk(
    id="toughness_3",
    name="Toughness III",
    description="+20 Max HP.",
    unlock_level=6,
    branch="vitality",
    requires=["toughness_2"],
    tags=["defense", "survivability"],
    apply_fn=_apply_toughness_3,
))

# ----------------- Blade tree -----------------

register(Perk(
    id="weapon_training_1",
    name="Weapon Training I",
    description="+2 Attack.",
    unlock_level=2,
    branch="blade",
    requires=[],
    tags=["offense"],
    apply_fn=_apply_weapon_training_1,
))

register(Perk(
    id="weapon_training_2",
    name="Weapon Training II",
    description="+2 Attack.",
    unlock_level=4,
    branch="blade",
    requires=["weapon_training_1"],
    tags=["offense"],
    apply_fn=_apply_weapon_training_2,
))

register(Perk(
    id="weapon_training_3",
    name="Weapon Training III",
    description="+3 Attack.",
    unlock_level=6,
    branch="blade",
    requires=["weapon_training_2"],
    tags=["offense"],
    apply_fn=_apply_weapon_training_3,
))

# Blade technique: unlocks a new offensive skill
register(Perk(
    id="blade_technique_1",
    name="Blade Technique I",
    description="Unlocks the Lunge (R) battle skill.",
    unlock_level=3,
    branch="blade",
    requires=["weapon_training_1"],
    grant_skills=["lunge"],
    tags=["offense", "skills"],
))

# ----------------- Ward tree -----------------

register(Perk(
    id="iron_guard_1",
    name="Iron Guard I",
    description="+1 Defense.",
    unlock_level=2,
    branch="ward",
    requires=[],
    tags=["defense"],
    apply_fn=_apply_iron_guard_1,
))

register(Perk(
    id="iron_guard_2",
    name="Iron Guard II",
    description="+2 Defense.",
    unlock_level=5,
    branch="ward",
    requires=["iron_guard_1"],
    tags=["defense"],
    apply_fn=_apply_iron_guard_2,
))

# Ward technique: control skill (stun)
register(Perk(
    id="ward_technique_1",
    name="Ward Technique I",
    description="Unlocks the Shield Bash (E) battle skill.",
    unlock_level=3,
    branch="ward",
    requires=["iron_guard_1"],
    grant_skills=["shield_bash"],
    tags=["defense", "control", "skills"],
))

# Sentinel: Attacks of Opportunity
register(Perk(
    id="sentinel",
    name="Sentinel",
    description="You can make attacks of opportunity when enemies leave your melee range. Deals 75% damage.",
    unlock_level=4,
    branch="ward",
    requires=["iron_guard_1"],
    tags=["defense", "reactions"],
))

# ----------------- Focus tree -----------------

register(Perk(
    id="battle_focus_1",
    name="Battle Focus I",
    description="+15% Skill Power.",
    unlock_level=3,
    branch="focus",
    requires=[],
    tags=["offense", "skills"],
    apply_fn=_apply_battle_focus_1,
))

register(Perk(
    id="battle_focus_2",
    name="Battle Focus II",
    description="+20% Skill Power.",
    unlock_level=6,
    branch="focus",
    requires=["battle_focus_1"],
    tags=["offense", "skills"],
    apply_fn=_apply_battle_focus_2,
))

# Focus technique: heavy skill-power based strike
register(Perk(
    id="focus_channel_1",
    name="Focus Channeling I",
    description="Unlocks the Focus Blast (F) battle skill.",
    unlock_level=4,
    branch="focus",
    requires=["battle_focus_1"],
    grant_skills=["focus_blast"],
    tags=["offense", "skills"],
))

# ----------------- Mobility tree -----------------

register(Perk(
    id="fleet_footwork_1",
    name="Fleet Footwork I",
    description="Unlocks Nimble Step (T), +1 Defense, and +2 Initiative.",
    unlock_level=3,
    branch="mobility",
    requires=[],
    grant_skills=["nimble_step"],
    tags=["mobility", "defense", "skills"],
    apply_fn=_apply_fleet_footwork_1,
))

register(Perk(
    id="fleet_footwork_2",
    name="Fleet Footwork II",
    description="+1 Defense, +5 Max HP, and +3 Initiative.",
    unlock_level=5,
    branch="mobility",
    requires=["fleet_footwork_1"],
    tags=["mobility", "defense"],
    apply_fn=_apply_fleet_footwork_2,
))

# ----------------- Warrior-specific perks ---------------------------------

# Cleave unlock
register(Perk(
    id="quickstep_1",
    name="Quickstep I",
    description="+0.5 Movement Point and +2 Initiative per turn.",
    unlock_level=5,  # Increased from 4 to make it harder to get
    branch="mobility",
    requires=["fleet_footwork_1"],
    tags=["mobility", "initiative"],
    apply_fn=_apply_quickstep_1,
))

register(Perk(
    id="quickstep_2",
    name="Quickstep II",
    description="+0.5 additional Movement Point and +3 Initiative per turn.",
    unlock_level=8,  # Increased from 6 to make it harder to get
    branch="mobility",
    requires=["quickstep_1"],
    tags=["mobility", "initiative"],
    apply_fn=_apply_quickstep_2,
))

register(Perk(
    id="warrior_cleave",
    name="Weapon Mastery",
    description="Unlocks the Cleave skill - strike multiple enemies at once.",
    unlock_level=4,
    branch="blade",
    requires=["weapon_training_2"],
    grant_skills=["cleave"],
    tags=["offense", "skills", "warrior"],
))

# Taunt unlock
register(Perk(
    id="warrior_taunt",
    name="Intimidating Presence",
    description="Unlocks the Taunt skill - force enemies to focus on you.",
    unlock_level=3,
    branch="ward",
    requires=["iron_guard_1"],
    grant_skills=["taunt"],
    tags=["defense", "control", "skills", "warrior"],
))

# Charge unlock
register(Perk(
    id="warrior_charge",
    name="Battle Charge",
    description="Unlocks the Charge skill - rush forward and strike.",
    unlock_level=5,
    branch="blade",
    requires=["weapon_training_2"],
    grant_skills=["charge"],
    tags=["offense", "mobility", "skills", "warrior"],
))

# Shield Wall unlock
register(Perk(
    id="warrior_shield_wall",
    name="Defensive Stance",
    description="Unlocks the Shield Wall skill - boost your defense.",
    unlock_level=4,
    branch="ward",
    requires=["iron_guard_1"],
    grant_skills=["shield_wall"],
    tags=["defense", "skills", "warrior"],
))

# Second Wind unlock (Warrior)
register(Perk(
    id="warrior_second_wind",
    name="Resilience",
    description="Unlocks the Second Wind skill - restore HP and stamina.",
    unlock_level=6,
    branch="vitality",
    requires=["toughness_2"],
    grant_skills=["second_wind"],
    tags=["defense", "survivability", "skills", "warrior"],
))

# ----------------- Rogue-specific perks ---------------------------------

# Backstab unlock
register(Perk(
    id="rogue_backstab",
    name="Assassin Training",
    description="Unlocks the Backstab skill - devastating precision strike.",
    unlock_level=4,
    branch="blade",
    requires=["fleet_footwork_1"],
    grant_skills=["backstab"],
    tags=["offense", "skills", "rogue"],
))

# Shadow Strike unlock
register(Perk(
    id="rogue_shadow_strike",
    name="Shadow Mastery",
    description="Unlocks the Shadow Strike skill - strike from the shadows.",
    unlock_level=5,
    branch="mobility",
    requires=["fleet_footwork_1"],
    grant_skills=["shadow_strike"],
    tags=["offense", "mobility", "skills", "rogue"],
))

# Poison Blade unlock
register(Perk(
    id="rogue_poison_blade",
    name="Poison Mastery",
    description="Unlocks the Poison Blade skill - apply deadly toxins.",
    unlock_level=4,
    branch="blade",
    requires=["fleet_footwork_1"],
    grant_skills=["poison_blade"],
    tags=["offense", "skills", "rogue"],
))

# Evade unlock
register(Perk(
    id="rogue_evade",
    name="Evasive Reflexes",
    description="Unlocks the Evade skill - dodge the next attack.",
    unlock_level=3,
    branch="mobility",
    requires=["fleet_footwork_1"],
    grant_skills=["evade"],
    tags=["defense", "mobility", "skills", "rogue"],
))

# Second Wind unlock (Rogue)
register(Perk(
    id="rogue_second_wind",
    name="Quick Recovery",
    description="Unlocks the Second Wind skill - restore HP and stamina.",
    unlock_level=5,
    branch="mobility",
    requires=["fleet_footwork_1"],
    grant_skills=["second_wind"],
    tags=["defense", "survivability", "skills", "rogue"],
))

# ----------------- Mage-specific perks ---------------------------------

# Fireball unlock
register(Perk(
    id="mage_fireball",
    name="Pyromancy",
    description="Unlocks the Fireball skill - hurl explosive fire magic.",
    unlock_level=4,
    branch="focus",
    requires=["battle_focus_1"],
    grant_skills=["fireball"],
    tags=["offense", "skills", "mage"],
))

# Lightning Bolt unlock
register(Perk(
    id="mage_lightning",
    name="Electromancy",
    description="Unlocks the Lightning Bolt skill - chain lightning attack.",
    unlock_level=5,
    branch="focus",
    requires=["battle_focus_1"],
    grant_skills=["lightning_bolt"],
    tags=["offense", "skills", "mage"],
))

# Slow unlock
register(Perk(
    id="mage_slow",
    name="Temporal Magic",
    description="Unlocks the Slow skill - reduce enemy speed.",
    unlock_level=3,
    branch="focus",
    requires=["battle_focus_1"],
    grant_skills=["slow"],
    tags=["control", "skills", "mage"],
))

# Magic Shield unlock
register(Perk(
    id="mage_shield",
    name="Arcane Protection",
    description="Unlocks the Magic Shield skill - absorb incoming damage.",
    unlock_level=4,
    branch="focus",
    requires=["battle_focus_1"],
    grant_skills=["magic_shield"],
    tags=["defense", "skills", "mage"],
))

# Arcane Missile unlock
register(Perk(
    id="mage_missile",
    name="Arcane Mastery",
    description="Unlocks the Arcane Missile skill - quick magical projectile.",
    unlock_level=3,
    branch="focus",
    requires=["battle_focus_1"],
    grant_skills=["arcane_missile"],
    tags=["offense", "skills", "mage"],
))

# ----------------- Skill Slot Expansion perks -----------------

register(Perk(
    id="combat_mastery",
    name="Combat Mastery",
    description="Unlocks an additional skill slot (5 total).",
    unlock_level=6,
    branch="blade",
    requires=["weapon_training_2"],
    tags=["skills", "utility"],
    apply_fn=_apply_combat_mastery,
))

register(Perk(
    id="weapon_expertise",
    name="Weapon Expertise",
    description="Unlocks an additional skill slot (6 total).",
    unlock_level=10,
    branch="blade",
    requires=["combat_mastery"],
    tags=["skills", "utility"],
    apply_fn=_apply_weapon_expertise,
))

register(Perk(
    id="legendary_warrior",
    name="Legendary Warrior",
    description="Unlocks an additional skill slot (7 total).",
    unlock_level=15,
    branch="blade",
    requires=["weapon_expertise"],
    tags=["skills", "utility"],
    apply_fn=_apply_legendary_warrior,
))


# --- Helper functions used by the game --------------------------------------

def apply_perk_to_hero(hero_stats: object, perk: Perk) -> None:
    """
    Apply a single perk to a HeroStats-like object and record it as learned.

    - Ensures hero_stats.perks exists.
    - Skips if the perk is already learned.
    - Uses the Perk.apply() hook to mutate base stats (max_hp, attack, etc.)
      when the perk has an apply_fn.
    """
    # Make sure the hero has a perks list
    if not hasattr(hero_stats, "perks"):
        hero_stats.perks = []

    owned = getattr(hero_stats, "perks")

    # Don’t double-apply the same perk
    if perk.id in owned:
        return

    # Apply stat modifications (if any)
    perk.apply(hero_stats)

    # Register as learned
    owned.append(perk.id)


def apply_perk_to_companion(companion_state: object, perk: Perk) -> None:
    """
    Register a perk as learned on a CompanionState-like object.

    Companion stats are recalculated elsewhere (e.g. via
    systems.party.recalc_companion_stats_for_level) based on the
    companion_state.perks list, so this helper only updates that list.
    """
    if not hasattr(companion_state, "perks"):
        companion_state.perks = []

    owned = getattr(companion_state, "perks")

    # Avoid duplicates
    if perk.id in owned:
        return

    owned.append(perk.id)


def auto_assign_perks(hero_stats: object) -> List[str]:
    """
    (Legacy helper, not used right now.)

    Ensure the hero has all perks whose unlock_level <= current level
    AND whose prerequisites are satisfied.

    Returns a list of log messages describing newly learned perks.
    """
    messages: List[str] = []

    if not hasattr(hero_stats, "perks"):
        hero_stats.perks = []

    owned: List[str] = list(getattr(hero_stats, "perks", []))

    sorted_perks = sorted(all_perks(), key=lambda p: p.unlock_level)

    for perk in sorted_perks:
        if hero_stats.level < perk.unlock_level:
            continue
        if perk.id in owned:
            continue
        if any(req not in owned for req in perk.requires):
            continue

        perk.apply(hero_stats)
        owned.append(perk.id)
        messages.append(f"You learn perk: {perk.name}.")

    hero_stats.perks = owned
    return messages


def pick_perk_choices(hero_stats: object, max_choices: int = 3) -> List[Perk]:
    """
    Pick up to `max_choices` perk OPTIONS for the player to choose from.

    - Only perks with unlock_level <= hero_stats.level
    - Only perks not already learned
    - Only perks whose prerequisites are already owned
    - Tries to offer different branches first (vitality/blade/ward/focus/mobility)
    """
    if not hasattr(hero_stats, "perks"):
        hero_stats.perks = []

    owned = set(getattr(hero_stats, "perks", []))

    candidates: List[Perk] = [
        p for p in all_perks()
        if p.unlock_level <= hero_stats.level
        and p.id not in owned
        and all(req in owned for req in p.requires)
    ]

    if not candidates:
        return []

    random.shuffle(candidates)

    # Group by branch to encourage variety
    by_branch: Dict[str, List[Perk]] = {}
    for p in candidates:
        by_branch.setdefault(p.branch, []).append(p)

    choices: List[Perk] = []

    # First pass: one perk per different branch
    branches = list(by_branch.keys())
    random.shuffle(branches)
    for br in branches:
        if len(choices) >= max_choices:
            break
        choice = random.choice(by_branch[br])
        choices.append(choice)

    # Second pass: if still below max_choices, fill from remaining
    if len(choices) < max_choices:
        remaining = [p for p in candidates if p not in choices]
        random.shuffle(remaining)
        for p in remaining:
            if len(choices) >= max_choices:
                break
            choices.append(p)

    return choices


def describe_perk_list(perk_ids: Iterable[str], short: bool = True) -> List[str]:
    """
    Turn a list of perk ids into human-readable lines for the character sheet.
    """
    lines: List[str] = []
    for pid in perk_ids:
        perk = _PERKS.get(pid)
        if perk is None:
            continue
        if short:
            lines.append(perk.name)
        else:
            lines.append(f"{perk.name}: {perk.description}")
    return lines


# --- New helper for companions ----------------------------------------------


class _DummyBaseStats:
    """
    Minimal stand-in for HeroStats.base so we can reuse perk apply functions
    to compute pure stat modifiers for companions.
    """
    def __init__(self) -> None:
        self.max_hp: int = 0
        self.attack: int = 0
        self.defense: int = 0
        self.skill_power: float = 0.0
        self.max_mana: int = 0
        self.max_stamina: int = 0
        self.stamina_regen_bonus: int = 0
        self.mana_regen_bonus: int = 0
        self.initiative: int = 0
        self.movement_points_bonus: int = 0


class _DummyHeroLike:
    def __init__(self) -> None:
        self.base = _DummyBaseStats()


def total_stat_modifiers_for_perks(perk_ids: Iterable[str]) -> Dict[str, float]:
    """
    Compute aggregate stat bonuses granted by the given perk ids.

    The result is a dict with keys:
        - "max_hp" (int)
        - "attack" (int)
        - "defense" (int)
        - "skill_power" (float)

    Implementation detail:
    We reuse the existing Perk.apply functions by applying them to a
    dummy hero_stats object whose base stats start at zero. Because our
    current perk effects are all additive (+=), the final values on the
    dummy object represent the total modifiers.
    """
    dummy = _DummyHeroLike()

    for pid in perk_ids:
        perk = _PERKS.get(pid)
        if perk is None:
            continue
        if perk.apply_fn is None:
            continue
        perk.apply(dummy)

    base = dummy.base
    return {
        "max_hp": int(base.max_hp),
        "attack": int(base.attack),
        "defense": int(base.defense),
        "skill_power": float(base.skill_power),
        "max_mana": int(getattr(base, "max_mana", 0)),
        "max_stamina": int(getattr(base, "max_stamina", 0)),
        "stamina_regen_bonus": int(getattr(base, "stamina_regen_bonus", 0)),
        "mana_regen_bonus": int(getattr(base, "mana_regen_bonus", 0)),
        "initiative": int(getattr(base, "initiative", 0)),
        "movement_points_bonus": int(getattr(base, "movement_points_bonus", 0)),
    }
