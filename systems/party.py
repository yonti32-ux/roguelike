# systems/party.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING

from systems.perks import total_stat_modifiers_for_perks
from systems.inventory import get_item_def
from systems import perks as perk_system
from systems.skills import get_skill_rank_cost
from settings import (
    DEFAULT_PLAYER_MAX_HP,
    DEFAULT_PLAYER_ATTACK,
    DEFAULT_COMPANION_STAMINA,
    DEFAULT_COMPANION_HP_FACTOR,
    DEFAULT_COMPANION_ATTACK_FACTOR,
)

if TYPE_CHECKING:
    from world.entities import Player


@dataclass
class CompanionDef:
    """
    Companion template definition.
    
    Now uses classes (like hero classes) for stat calculation and skill access.
    - class_id: References a ClassDef from systems.classes (e.g., "warrior", "rogue", "mage")
    - Legacy factors (hp_factor, etc.) are kept for backwards compatibility but
      class-based stats take precedence if class_id is set.
    """
    id: str
    name: str
    role: str

    # Class-based progression (preferred)
    class_id: Optional[str] = None  # References ClassDef.id

    # Legacy stat factors (used if class_id is None, or as multipliers)
    hp_factor: float = 0.8
    attack_factor: float = 0.7
    defense_factor: float = 1.0
    skill_power_factor: float = 1.0

    # Base skill list this companion knows (from template, before class/perks)
    skill_ids: List[str] = field(default_factory=list)


@dataclass
class CompanionState:
    """
    Runtime state for a recruited companion.

    - template_id points at a CompanionDef in the registry.
    - class_id: The companion's class (inherited from template or set explicitly)
    - level / xp track this specific companion's progression.
    - perks: list of perk ids this companion owns.
    - equipped: simple per-companion equipment slots.
    - max_hp / attack_power / defense / skill_power / resources are this
      specific companion's stats (used by battle + UI).
    """
    template_id: str
    name_override: Optional[str] = None
    level: int = 1
    xp: int = 0

    # Companion class (inherited from template or set explicitly)
    class_id: Optional[str] = None

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

    # Hotbar-style skill layout; indices 0–3 map to SKILL_1..SKILL_4.
    # Values are skill IDs (strings) or None.
    skill_slots: List[Optional[str]] = field(
        default_factory=lambda: [None, None, None, None]
    )

    # Skill progression system
    # Available skill points to spend on upgrading skills
    skill_points: int = 0
    
    # Track skill ranks: skill_id -> current_rank (0 = unranked, max 5)
    skill_ranks: Dict[str, int] = field(default_factory=dict)

    # Runtime stats for this companion (filled by helper functions).
    max_hp: int = 0
    attack_power: int = 0
    defense: int = 0
    skill_power: float = 1.0
    max_mana: int = 0
    max_stamina: int = 0

    # --- XP / Level helpers -------------------------------------------------

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
            
            # Grant skill points on level up (same formula as hero)
            # Formula: 1 + (level // 5) points per level
            points_gained = 1 + (self.level // 5)
            self.skill_points += points_gained
            
            levels_gained += 1

        return levels_gained

    # --- Skill rank helpers ----------------------------------------------------

    def get_skill_rank(self, skill_id: str) -> int:
        """Get the current rank of a skill (0 if not ranked)."""
        return self.skill_ranks.get(skill_id, 0)

    def can_upgrade_skill(self, skill_id: str) -> bool:
        """
        Check if a skill can be upgraded.
        
        Requirements:
        - Skill must exist
        - Current rank must be less than max_rank
        - Must have enough skill points for the next rank
        """
        from .skills import get
        
        try:
            skill = get(skill_id)
        except KeyError:
            return False
        
        current_rank = self.get_skill_rank(skill_id)
        if current_rank >= skill.max_rank:
            return False
        
        next_rank = current_rank + 1
        cost = get_skill_rank_cost(next_rank)
        return self.skill_points >= cost

    def upgrade_skill(self, skill_id: str) -> bool:
        """
        Upgrade a skill by one rank.
        
        Returns True if upgrade was successful, False otherwise.
        """
        if not self.can_upgrade_skill(skill_id):
            return False
        
        from .skills import get
        
        current_rank = self.get_skill_rank(skill_id)
        next_rank = current_rank + 1
        cost = get_skill_rank_cost(next_rank)
        
        self.skill_points -= cost
        self.skill_ranks[skill_id] = next_rank
        return True


def auto_allocate_companion_skill_points(state: CompanionState, template: CompanionDef) -> List[str]:
    """
    Automatically allocate skill points for a companion based on their role/template.
    
    Strategy:
    - Prioritize skills that match the companion's template (from skill_ids)
    - Upgrade skills evenly across available skills
    - Prefer skills with lower ranks first (to maximize total upgrades)
    - Only allocates to skills available for the companion's class
    
    Returns:
        List of messages describing what was upgraded.
    """
    from .skills import get, get_skill_rank_cost, is_skill_available_for_class
    
    messages: List[str] = []
    
    if state.skill_points <= 0:
        return messages
    
    # Get companion's class for filtering
    companion_class_id = getattr(state, "class_id", None) or getattr(template, "class_id", None)
    
    # Get available skills for this companion (using the same logic as skill screen)
    from ui.skill_screen import get_unlocked_skills_for_companion
    available_skills = get_unlocked_skills_for_companion(state)
    
    if not available_skills:
        return messages
    
    # Sort by current rank (lowest first) to upgrade evenly
    available_skills.sort(key=lambda sid: state.get_skill_rank(sid))
    
    # Allocate points until we run out
    while state.skill_points > 0:
        upgraded = False
        
        for skill_id in available_skills:
            if state.can_upgrade_skill(skill_id):
                if state.upgrade_skill(skill_id):
                    current_rank = state.get_skill_rank(skill_id)
                    try:
                        skill = get(skill_id)
                        messages.append(f"{template.name} upgraded {skill.name} to rank {current_rank}.")
                    except KeyError:
                        messages.append(f"{template.name} upgraded skill to rank {current_rank}.")
                    upgraded = True
                    break
        
        # If we couldn't upgrade anything, we're done
        if not upgraded:
            break
    
    return messages


# --- Companion stat helpers --------------------------------------------------


def recalc_companion_stats_for_level(state: CompanionState, template: CompanionDef) -> None:
    """
    Recompute stats based on the companion's level, template, perks
    and any equipment they have.
    
    If companion has a class_id, uses class-based stats (like hero).
    Otherwise falls back to factor-based calculation.
    """
    level = max(1, int(state.level))
    
    # Determine companion's class (from state or template)
    companion_class_id = getattr(state, "class_id", None) or getattr(template, "class_id", None)
    
    # Try to use class-based stats if class is available
    if companion_class_id:
        try:
            from .classes import get_class
            class_def = get_class(companion_class_id)
            
            # Use class base stats as starting point
            base_stats = class_def.base_stats
            
            # Calculate level-based growth (same as hero)
            hp = base_stats.max_hp + (level - 1) * 5
            atk = base_stats.attack + (level - 1) * 1
            defense = base_stats.defense  # Defense grows via perks/items mostly
            skill_power = base_stats.skill_power  # Skill power grows via perks mostly
            
            # Resource pools from class (scaled appropriately)
            stamina = base_stats.max_stamina + (level - 1) * 3  # Reduced growth: 3 per level
            mana = base_stats.max_mana + (level - 1) * 2  # Reduced growth: 2 per level
            
            # Apply template factors as multipliers (for companion balance)
            hp = int(hp * float(template.hp_factor))
            atk = int(atk * float(template.attack_factor))
            defense = int(defense * float(template.defense_factor))
            skill_power = float(skill_power * float(template.skill_power_factor))
            # Companions get slightly reduced resource pools (0.9x multiplier)
            stamina = int(stamina * float(template.hp_factor) * 0.9)  # Slight reduction
            mana = int(mana * float(template.skill_power_factor) * 0.9)  # Slight reduction
            
        except (KeyError, AttributeError):
            # Class not found or invalid, fall back to factor-based
            companion_class_id = None
    
    # Fallback: factor-based calculation (legacy)
    if not companion_class_id:
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

        # Baseline resource pools (reduced for balance)
        BASE_STAMINA = 24  # Reduced from 36
        BASE_MANA = 8  # Reduced from 12

        stamina_linear = BASE_STAMINA + (level - 1) * 3  # Reduced growth
        mana_linear = BASE_MANA + (level - 1) * 2  # Reduced growth

        # Scale with template specialisation
        stamina = stamina_linear * float(template.hp_factor) * 0.9  # Slight reduction
        mana = mana_linear * float(template.skill_power_factor) * 0.9  # Slight reduction

    # Apply per-companion perk bonuses, if any.
    stamina_regen_bonus = 0
    mana_regen_bonus = 0
    if state.perks:
        mods = total_stat_modifiers_for_perks(state.perks)
        hp += mods.get("max_hp", 0)
        atk += mods.get("attack", 0)
        defense += mods.get("defense", 0)
        skill_power += mods.get("skill_power", 0.0)
        mana += int(mods.get("max_mana", 0))
        stamina += int(mods.get("max_stamina", 0))
        stamina_regen_bonus = int(mods.get("stamina_regen_bonus", 0))
        mana_regen_bonus = int(mods.get("mana_regen_bonus", 0))

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
        mana += int(item_stats.get("max_mana", 0))
        stamina += int(item_stats.get("max_stamina", 0))

    state.max_hp = max(1, int(hp))
    state.attack_power = max(1, int(atk))
    state.defense = max(0, int(defense))
    state.skill_power = max(0.1, float(skill_power))
    state.max_mana = max(0, int(mana))
    state.max_stamina = max(0, int(stamina))
    state.stamina_regen_bonus = stamina_regen_bonus
    state.mana_regen_bonus = mana_regen_bonus


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

    # Also seed a default skill-slot layout if we don't have one yet.
    init_companion_skill_slots(state, template)


def ensure_companion_stats(state: CompanionState, template: CompanionDef) -> None:
    """
    Make sure a companion has valid stats; if not, recompute them.

    This is a safety net so that if we ever introduce companions into an
    old save or forget to initialise them somewhere, they won't end up
    with 0 HP / ATK.
    """
    if state.max_hp <= 0 or state.attack_power <= 0 or state.skill_power <= 0:
        recalc_companion_stats_for_level(state, template)


def create_companion_entity(
    template: CompanionDef,
    state: Optional[CompanionState] = None,
    reference_player: Optional["Player"] = None,
    hero_base_hp: Optional[int] = None,
    hero_base_attack: Optional[int] = None,
    hero_base_defense: int = 0,
    hero_base_skill_power: float = 1.0,
) -> "Player":
    """
    Create a Player entity from companion data for use in battle or exploration.
    
    Args:
        template: CompanionDef template with stat factors
        state: Optional CompanionState with runtime stats (preferred if available)
        reference_player: Optional Player entity to copy dimensions/color from
        hero_base_hp, hero_base_attack, hero_base_defense, hero_base_skill_power:
            Hero stats for legacy path when state is None
    
    Returns:
        A Player entity configured as a companion with appropriate stats.
    """
    from world.entities import Player
    
    # Ensure stats are initialized if we have a state
    if state is not None:
        try:
            ensure_companion_stats(state, template)
        except Exception:
            # Fallback to stored values if recalculation fails
            pass
    
    # Extract or derive companion stats
    if state is not None:
        # Use state's computed stats (preferred path)
        comp_max_hp = max(1, int(getattr(state, "max_hp", 1)))
        comp_hp = comp_max_hp
        comp_atk = max(1, int(getattr(state, "attack_power", 1)))
        comp_defense = max(0, int(getattr(state, "defense", 0)))
        comp_sp = max(0.1, float(getattr(state, "skill_power", 1.0)))
        
        # Resource pools from state
        comp_max_mana = int(getattr(state, "max_mana", 0) or 0)
        comp_max_stamina = int(getattr(state, "max_stamina", 0) or 0)
    else:
        # Legacy path: derive from hero stats + template factors
        base_hp = hero_base_hp if hero_base_hp is not None else DEFAULT_PLAYER_MAX_HP
        base_atk = hero_base_attack if hero_base_attack is not None else DEFAULT_PLAYER_ATTACK
        
        comp_max_hp = max(1, int(base_hp * template.hp_factor))
        comp_hp = comp_max_hp
        comp_atk = max(1, int(base_atk * template.attack_factor))
        comp_defense = int(hero_base_defense * template.defense_factor)
        comp_sp = max(0.1, hero_base_skill_power * template.skill_power_factor)
        
        # No resource pools for legacy path (will use defaults)
        comp_max_mana = 0
        comp_max_stamina = 0
    
    # Apply resource pool defaults if needed
    if comp_max_stamina <= 0:
        comp_max_stamina = DEFAULT_COMPANION_STAMINA
    if comp_max_mana < 0:
        comp_max_mana = 0
    
    # Use reference player for dimensions/color, or defaults
    if reference_player is not None:
        width = reference_player.width
        height = reference_player.height
        color = reference_player.color
    else:
        # Default dimensions (32x32 typical for entities)
        width = 24
        height = 24
        color = (200, 200, 200)
    
    # Get companion level for regeneration scaling
    comp_level = 1
    if state is not None:
        comp_level = max(1, int(getattr(state, "level", 1)))
    
    # Create the Player entity
    companion_entity = Player(
        x=0,  # Position should be set by caller
        y=0,
        width=width,
        height=height,
        speed=0.0,  # Companions don't move independently in exploration
        color=color,
        max_hp=comp_max_hp,
        hp=comp_hp,
        attack_power=comp_atk,
    )
    
    # Set additional stats as attributes
    setattr(companion_entity, "defense", comp_defense)
    setattr(companion_entity, "skill_power", comp_sp)
    setattr(companion_entity, "max_mana", comp_max_mana)
    setattr(companion_entity, "max_stamina", comp_max_stamina)
    setattr(companion_entity, "level", comp_level)  # For regeneration scaling
    
    # Set regeneration bonuses from companion state (if available)
    if state is not None:
        # Get regeneration bonuses from state (calculated from perks in recalc_companion_stats_for_level)
        stamina_regen = getattr(state, "stamina_regen_bonus", 0)
        mana_regen = getattr(state, "mana_regen_bonus", 0)
        setattr(companion_entity, "stamina_regen_bonus", stamina_regen)
        setattr(companion_entity, "mana_regen_bonus", mana_regen)
    else:
        setattr(companion_entity, "stamina_regen_bonus", 0)
        setattr(companion_entity, "mana_regen_bonus", 0)
    
    return companion_entity


# --- Companion registry & templates -----------------------------------------

_COMPANIONS: Dict[str, CompanionDef] = {}


def init_companion_skill_slots(state: CompanionState, template: CompanionDef) -> None:
    """
    Ensure the companion has a reasonable default skill-slot layout.

    - Uses template.skill_ids and perk-granted skills where possible.
    - Skips 'guard' (handled by the dedicated GUARD action).
    - Only fills empty layouts; existing layouts are preserved.
    """
    # If there is already at least one real slot, don't overwrite.
    if any(state.skill_slots):
        return

    available: List[str] = []

    # Base skills from template, excluding guard
    for sid in template.skill_ids:
        if not sid or sid == "guard":
            continue
        if sid not in available:
            available.append(sid)

    # Skills unlocked from perks (grant_skills on perk definitions)
    if state.perks:
        for pid in state.perks:
            try:
                perk = perk_system.get(pid)
            except Exception:
                continue
            for sid in getattr(perk, "grant_skills", []):
                if not sid or sid == "guard":
                    continue
                if sid not in available:
                    available.append(sid)

    # Build up to 4 slots from the available skills
    slots: List[Optional[str]] = []
    for sid in available:
        slots.append(sid)
        if len(slots) >= 4:
            break

    # Pad with Nones so the list is always length 4
    while len(slots) < 4:
        slots.append(None)

    state.skill_slots = slots


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

# Very basic ally; stats derived from hero-ish baselines.
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
    
    Companions inherit their class from their template.
    """
    states: List[CompanionState] = []
    for comp_def in default_party_for_class(hero_class_id):
        # Inherit class_id from template
        companion_class_id = getattr(comp_def, "class_id", None)
        
        state = CompanionState(
            template_id=comp_def.id,
            level=hero_level,
            xp=0,
            class_id=companion_class_id,  # Set companion's class
        )
        # Pre-seed a simple skill-slot layout from the template.
        init_companion_skill_slots(state, comp_def)
        states.append(state)
    return states
