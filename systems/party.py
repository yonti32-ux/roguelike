# systems/party.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from systems.perks import total_stat_modifiers_for_perks
from systems.inventory import get_item_def



@dataclass
class CompanionDef:
    """
    Simple companion template for now.

    For P1:
    - Stats are derived from the hero and scaled by these factors.
    - skill_ids are skill ids from systems.skills.

    Later we can extend this into full heroes with:
    - their own StatBlock
    - their own inventory / perks / class
    """
    id: str
    name: str
    role: str

    hp_factor: float = 0.8
    attack_factor: float = 0.7
    defense_factor: float = 1.0
    skill_power_factor: float = 1.0

    skill_ids: List[str] = field(default_factory=list)


@dataclass
class CompanionState:
    """
    Runtime state for a recruited companion.

    - template_id points at a CompanionDef in the registry.
    - level / xp track this specific companion's progression.
    - perks: list of perk ids this companion owns.
    - equipped: simple per-companion equipment slots.
    - max_hp / attack_power / defense / skill_power are this specific
      companion's stats (used by battle + UI).
    """
    template_id: str
    name_override: Optional[str] = None
    level: int = 1
    xp: int = 0

    # Per-companion perks (stat bonuses will be derived from these).
    perks: List[str] = field(default_factory=list)

    # Simple per-companion equipment slots. These mirror the hero's core
    # slots so the same items can be reused.
    equipped: Dict[str, Optional[str]] = field(
        default_factory=lambda: {
            "weapon": None,
            "armor": None,
            "trinket": None,
        }
    )

    # Runtime stats for this companion (filled by helper functions).
    max_hp: int = 0
    attack_power: int = 0
    defense: int = 0
    skill_power: float = 1.0

    # --- XP / Level helpers -----------------------------------------

    def xp_to_next(self) -> int:
        """
        XP needed for this companion's next level.

        Matches the hero's curve for now:
            level 1 -> 2: 10 XP
            level 2 -> 3: 15 XP
            level 3 -> 4: 20 XP
        etc.
        """
        return 10 + (self.level - 1) * 5

    def grant_xp(self, amount: int) -> int:
        """
        Give XP to this companion and handle level ups.

        Returns:
            int: how many levels were gained (0 if none).
        """
        amount = int(amount)
        if amount <= 0:
            return 0

        self.xp += amount
        levels_gained = 0

        # Allow multiple level-ups from one big XP chunk
        while True:
            needed = self.xp_to_next()
            if self.xp < needed:
                break

            self.xp -= needed
            self.level += 1
            levels_gained += 1

        return levels_gained


# --- Companion stat helpers -----------------------------------------------


def init_companion_stats(state: CompanionState, template: CompanionDef) -> None:
    """
    Initialise stats for a *fresh* companion at its current level.

    This is intended to be called when the companion is first created
    (e.g. at the start of a run or on recruitment).
    """
    # Ensure a sane level
    if state.level < 1:
        state.level = 1

    recalc_companion_stats_for_level(state, template)


def recalc_companion_stats_for_level(state: CompanionState, template: CompanionDef) -> None:
    """
    Recompute stats based on the companion's level, template, perks
    and any equipment they have.
    """
    level = max(1, int(state.level))

    # Baseline hero-ish values
    BASE_HP = 30
    BASE_ATK = 5
    BASE_DEF = 1
    BASE_SP = 1.0

    # Growth per level before template scaling
    hp_linear = BASE_HP + (level - 1) * 5
    atk_linear = BASE_ATK + (level - 1) * 1
    # Defense grows slowly; every ~3 levels
    def_linear = BASE_DEF + (level - 1) // 3
    sp_linear = BASE_SP + 0.05 * (level - 1)

    # Apply template specialisation
    hp = hp_linear * float(template.hp_factor)
    atk = atk_linear * float(template.attack_factor)
    defense = def_linear * float(template.defense_factor)
    skill_power = sp_linear * float(template.skill_power_factor)

    # Apply per-companion perk bonuses, if any.
    if state.perks:
        mods = total_stat_modifiers_for_perks(state.perks)
        hp += mods.get("max_hp", 0)
        atk += mods.get("attack", 0)
        defense += mods.get("defense", 0)
        skill_power += mods.get("skill_power", 0.0)

    # Apply equipment bonuses, if this companion has any gear equipped.
    equipped = getattr(state, "equipped", None) or {}
    for slot, item_id in equipped.items():
        if not item_id:
            continue
        item_def = get_item_def(item_id)
        if item_def is None:
            continue
        item_stats = getattr(item_def, "stats", {}) or {}
        hp += int(item_stats.get("max_hp", 0))
        atk += int(item_stats.get("attack", 0))
        defense += int(item_stats.get("defense", 0))
        skill_power += float(item_stats.get("skill_power", 0.0))

    state.max_hp = max(1, int(hp))
    state.attack_power = max(1, int(atk))
    state.defense = max(0, int(defense))
    state.skill_power = max(0.1, float(skill_power))


def ensure_companion_stats(state: CompanionState, template: CompanionDef) -> None:
    """
    Make sure a companion has valid stats; if not, recompute them.

    This is a safety net so that if we ever introduce companions into an
    old save or forget to initialise them somewhere, they won't end up
    with 0 HP / ATK.
    """
    if state.max_hp <= 0 or state.attack_power <= 0 or state.skill_power <= 0:
        recalc_companion_stats_for_level(state, template)


# --- Companion registry & templates ----------------------------------------


_COMPANIONS: Dict[str, CompanionDef] = {}


def register_companion(defn: CompanionDef) -> CompanionDef:
    if defn.id in _COMPANIONS:
        raise ValueError(f"Companion id already registered: {defn.id}")
    _COMPANIONS[defn.id] = defn
    return defn


def get_companion(companion_id: str) -> CompanionDef:
    return _COMPANIONS[companion_id]


def all_companions() -> List[CompanionDef]:
    return list(_COMPANIONS.values())


# --- Concrete companion templates -------------------------------------------

# Very basic ally; stats derived from hero.
DEFAULT_MERCENARY = register_companion(
    CompanionDef(
        id="mercenary",
        name="Sellsword",
        role="Ally",
        skill_ids=["guard"],
        hp_factor=0.8,
        attack_factor=0.7,
        defense_factor=1.0,
        skill_power_factor=1.0,
    )
)


def default_party_for_class(hero_class_id: str) -> List[CompanionDef]:
    """
    For now, every class starts with the same basic ally.

    Later we can:
    - Vary companions per hero class
    - Add 2nd/3rd party member
    - Use events to recruit instead of always-on
    """
    return [DEFAULT_MERCENARY]


def default_party_states_for_class(hero_class_id: str, hero_level: int = 1) -> List[CompanionState]:
    """
    Build the initial runtime party for a given hero class.

    This wraps the CompanionDef templates in CompanionState objects.
    For B2 we simply seed their level/xp from the hero so they stay in lockstep.
    """
    states: List[CompanionState] = []
    for comp_def in default_party_for_class(hero_class_id):
        states.append(
            CompanionState(
                template_id=comp_def.id,
                level=hero_level,
                xp=0,
            )
        )
    return states
