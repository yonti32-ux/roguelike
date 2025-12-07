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
    # First mobility perk: slight defense bump
    hero_stats.base.defense += 1


def _apply_fleet_footwork_2(hero_stats: object) -> None:
    # Second mobility perk: more defense + a bit of HP
    hero_stats.base.defense += 1
    hero_stats.base.max_hp += 5


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
    description="Unlocks Nimble Step (T) and +1 Defense.",
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
    description="+1 Defense and +5 Max HP.",
    unlock_level=5,
    branch="mobility",
    requires=["fleet_footwork_1"],
    tags=["mobility", "defense"],
    apply_fn=_apply_fleet_footwork_2,
))


# --- Helper functions used by the game --------------------------------------


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
    }
