# systems/skills.py

from dataclasses import dataclass, field
from typing import Optional, Literal, Callable, Dict, List, Tuple

import pygame

from .statuses import StatusEffect


TargetMode = Literal["self", "adjacent_enemy", "any_enemy"]
RangeMetric = Literal["manhattan", "chebyshev"]


@dataclass
class Skill:
    """
    Generic combat skill definition.

    - id:          internal id used for cooldown tracking
    - name:        display name
    - description: UI / tooltip text
    - key:         pygame key constant to trigger it (None = AI only)
    - target_mode: "self", "adjacent_enemy", or "any_enemy" (ranged targeting)
    - base_power:  multiplier on the user's attack stat
    - uses_skill_power: if True, multiplies damage by entity.skill_power
    - cooldown:    number of that unit's turns before reuse
    - max_rank:    maximum rank this skill can be upgraded to (default 5)
    - class_restrictions: List of class IDs that can use this skill.
                          Empty list means all classes can use it.
    - make_self_status / make_target_status: factories returning
      StatusEffect instances to apply when the skill fires.
    - aoe_radius:  If > 0, skill has AoE effect. Radius in tiles (0 = single target).
    - aoe_shape:   Shape of AoE: "circle" or "square" (default: "circle")
    - aoe_affects_allies: If True, AoE affects friendly units (default: False)
    - aoe_affects_enemies: If True, AoE affects enemy units (default: True)
    - aoe_affects_self: If True, AoE affects the caster (default: False)
    - range_tiles: Maximum targeting range in tiles (default 1).
    - range_metric: Distance metric for targeting:
        - "chebyshev": 8-directional / diagonal-friendly (default; good for melee/adjacent)
        - "manhattan": 4-directional diamond (good for ranged-by-tiles)
    """
    id: str
    name: str
    description: str
    key: Optional[int]
    target_mode: TargetMode
    base_power: float = 1.0
    uses_skill_power: bool = False
    cooldown: int = 0
    mana_cost: int = 0
    stamina_cost: int = 0
    max_rank: int = 5
    class_restrictions: List[str] = field(default_factory=list)

    make_self_status: Optional[Callable[[], StatusEffect]] = None
    make_target_status: Optional[Callable[[], StatusEffect]] = None
    
    # AoE fields
    aoe_radius: int = 0  # 0 = single target, >0 = AoE radius in tiles
    aoe_shape: Literal["circle", "square"] = "circle"
    aoe_affects_allies: bool = False
    aoe_affects_enemies: bool = True
    aoe_affects_self: bool = False

    # Targeting range fields
    range_tiles: int = 1
    range_metric: RangeMetric = "chebyshev"
    
    # Weapon requirement fields
    requires_ranged_weapon: bool = False  # If True, unit must have a ranged weapon equipped


SKILLS: Dict[str, Skill] = {}


def register(skill: Skill) -> Skill:
    """
    Register a skill in the global registry and return it.
    """
    SKILLS[skill.id] = skill
    return skill


def get(skill_id: str) -> Skill:
    return SKILLS[skill_id]


def is_skill_available_for_class(skill_id: str, class_id: str) -> bool:
    """
    Check if a skill is available for a given class.
    
    Returns True if:
    - The skill has no class restrictions (empty list), OR
    - The class_id is in the skill's class_restrictions list
    """
    try:
        skill = get(skill_id)
        if not skill.class_restrictions:
            return True  # No restrictions = all classes can use
        return class_id in skill.class_restrictions
    except KeyError:
        return False


# --- Skill rank helpers -----------------------------------------------------

@dataclass
class SkillRankEffects:
    """
    Defines how a skill's properties change with rank.
    Each skill can have custom rank effects for more meaningful upgrades.
    """
    # Power scaling (multiplier per rank, or None to use default)
    power_per_rank: Optional[float] = None  # e.g., 0.15 = +15% per rank
    
    # Cooldown reduction (turns reduced per rank, or None for default)
    cooldown_reduction_per_rank: Optional[float] = None  # e.g., 0.5 = -0.5 turns per rank
    
    # Cost reduction (amount reduced per rank, or None for default)
    cost_reduction_per_rank: Optional[float] = None  # e.g., 1.0 = -1 per rank
    
    # Status effect duration bonus (turns added per rank)
    status_duration_bonus: int = 0  # e.g., 1 = +1 turn per rank
    
    # Status effect strength bonus (for multipliers, flat damage, etc.)
    status_strength_bonus: float = 0.0  # e.g., 0.05 = +5% multiplier per rank
    
    # DoT damage bonus (flat damage per turn added per rank)
    dot_damage_bonus: int = 0  # e.g., 1 = +1 damage per turn per rank
    
    # AoE radius bonus (tiles added per rank)
    aoe_radius_bonus: int = 0  # e.g., 1 = +1 tile per rank (at rank 3+)
    
    # Special: rank threshold for AoE radius increase
    aoe_radius_ranks: List[int] = field(default_factory=list)  # e.g., [3, 5] = +1 at rank 3, +1 more at rank 5


# Registry of skill-specific rank effects
SKILL_RANK_EFFECTS: Dict[str, SkillRankEffects] = {}


def register_rank_effects(skill_id: str, effects: SkillRankEffects) -> None:
    """Register rank effects for a skill."""
    SKILL_RANK_EFFECTS[skill_id] = effects


def get_skill_rank_effects(skill_id: str) -> Optional[SkillRankEffects]:
    """Get rank effects for a skill, or None if using defaults."""
    return SKILL_RANK_EFFECTS.get(skill_id)


def get_skill_rank_cost(rank: int) -> int:
    """
    Get the skill point cost to upgrade to the given rank.
    
    Rank 1: 1 point
    Rank 2: 2 points
    Rank 3: 3 points
    Rank 4: 4 points
    Rank 5: 5 points
    """
    if rank < 1:
        return 0
    return rank


def calculate_skill_power_at_rank(base_power: float, rank: int, skill_id: Optional[str] = None) -> float:
    """
    Calculate the effective power of a skill at a given rank.
    
    Uses skill-specific scaling if available, otherwise defaults to +10% per rank.
    """
    if rank <= 0:
        return base_power
    
    if skill_id:
        effects = get_skill_rank_effects(skill_id)
        if effects and effects.power_per_rank is not None:
            return base_power * (1.0 + effects.power_per_rank * rank)
    
    # Default: +10% per rank
    return base_power * (1.0 + 0.1 * rank)


def calculate_skill_cooldown_at_rank(base_cooldown: int, rank: int, skill_id: Optional[str] = None) -> int:
    """
    Calculate the effective cooldown of a skill at a given rank.
    
    Uses skill-specific reduction if available, otherwise defaults to -1 every 2 ranks.
    """
    if rank <= 0:
        return max(0, base_cooldown)
    
    if skill_id:
        effects = get_skill_rank_effects(skill_id)
        if effects and effects.cooldown_reduction_per_rank is not None:
            reduction = int(effects.cooldown_reduction_per_rank * rank)
            return max(0, base_cooldown - reduction)
    
    # Default: -1 every 2 ranks
    if rank <= 1:
        return max(0, base_cooldown)
    reduction = rank // 2
    return max(0, base_cooldown - reduction)


def calculate_skill_cost_at_rank(base_cost: int, rank: int, skill_id: Optional[str] = None, cost_type: str = "stamina") -> int:
    """
    Calculate the effective cost (stamina/mana) of a skill at a given rank.
    
    Uses skill-specific reduction if available, otherwise defaults to -1 per rank.
    """
    if rank <= 0:
        return max(0, base_cost)
    
    if skill_id:
        effects = get_skill_rank_effects(skill_id)
        if effects and effects.cost_reduction_per_rank is not None:
            reduction = int(effects.cost_reduction_per_rank * rank)
            return max(0, base_cost - reduction)
    
    # Default: -1 per rank
    return max(0, base_cost - rank)


def calculate_skill_status_duration_at_rank(base_duration: int, rank: int, skill_id: Optional[str] = None) -> int:
    """
    Calculate the effective status effect duration at a given rank.
    """
    if rank <= 0:
        return base_duration
    
    if skill_id:
        effects = get_skill_rank_effects(skill_id)
        if effects and effects.status_duration_bonus > 0:
            return base_duration + (effects.status_duration_bonus * rank)
    
    return base_duration


def calculate_skill_status_strength_at_rank(base_strength: float, rank: int, skill_id: Optional[str] = None) -> float:
    """
    Calculate the effective status effect strength (multiplier) at a given rank.
    
    For damage reduction (values < 1.0), negative bonuses make it stronger.
    For damage amplification (values > 1.0), positive bonuses make it stronger.
    """
    if rank <= 0:
        return base_strength
    
    if skill_id:
        effects = get_skill_rank_effects(skill_id)
        if effects and effects.status_strength_bonus != 0:
            # Apply bonus: for reduction (base < 1.0), negative bonus improves it
            # For amplification (base > 1.0), positive bonus improves it
            return base_strength + (effects.status_strength_bonus * rank)
    
    return base_strength


def calculate_skill_dot_damage_at_rank(base_dot: int, rank: int, skill_id: Optional[str] = None) -> int:
    """
    Calculate the effective DoT damage per turn at a given rank.
    """
    if rank <= 0:
        return base_dot
    
    if skill_id:
        effects = get_skill_rank_effects(skill_id)
        if effects and effects.dot_damage_bonus > 0:
            return base_dot + (effects.dot_damage_bonus * rank)
    
    return base_dot


def calculate_skill_aoe_radius_at_rank(base_radius: int, rank: int, skill_id: Optional[str] = None) -> int:
    """
    Calculate the effective AoE radius at a given rank.
    """
    if rank <= 0 or base_radius <= 0:
        return base_radius
    
    if skill_id:
        effects = get_skill_rank_effects(skill_id)
        if effects:
            # Check if this rank triggers a radius increase
            bonus = 0
            for threshold_rank in effects.aoe_radius_ranks:
                if rank >= threshold_rank:
                    bonus += effects.aoe_radius_bonus
            return base_radius + bonus
    
    return base_radius


def create_rank_modified_status(
    base_status: StatusEffect,
    rank: int,
    skill_id: Optional[str] = None
) -> StatusEffect:
    """
    Create a status effect modified by skill rank.
    
    Applies rank bonuses to duration, strength (multipliers), and DoT damage.
    """
    if rank <= 0 or skill_id is None:
        return base_status
    
    effects = get_skill_rank_effects(skill_id)
    if not effects:
        return base_status
    
    # Calculate modified values
    modified_duration = calculate_skill_status_duration_at_rank(base_status.duration, rank, skill_id)
    modified_outgoing = base_status.outgoing_mult
    modified_incoming = base_status.incoming_mult
    
    # Apply strength bonus if applicable
    if effects.status_strength_bonus != 0:
        if base_status.outgoing_mult != 1.0:
            modified_outgoing = calculate_skill_status_strength_at_rank(base_status.outgoing_mult, rank, skill_id)
        if base_status.incoming_mult != 1.0:
            modified_incoming = calculate_skill_status_strength_at_rank(base_status.incoming_mult, rank, skill_id)
    
    modified_dot = calculate_skill_dot_damage_at_rank(base_status.flat_damage_each_turn, rank, skill_id)
    
    # Create a copy of the status with modified values
    modified = StatusEffect(
        name=base_status.name,
        duration=modified_duration,
        stacks=base_status.stacks,
        outgoing_mult=modified_outgoing,
        incoming_mult=modified_incoming,
        flat_damage_each_turn=modified_dot,
        stunned=base_status.stunned,
    )
    
    return modified


# --- Core skill definitions -------------------------------------------------


def _build_core_skills() -> None:
    # Always-available defensive skill
    guard = register(
        Skill(
            id="guard",
            name="Guard",
            description="Brace yourself, reducing incoming damage by 50% until your next turn. Higher ranks increase duration and damage reduction.",
            key=pygame.K_g,
            target_mode="self",
            base_power=0.0,
            cooldown=0,
            make_self_status=lambda: StatusEffect(
                name="guard",
                duration=1,
                incoming_mult=0.5,
            ),
        )
    )

    # Base offensive skill for the hero
    power_strike = register(
        Skill(
            id="power_strike",
            name="Power Strike",
            description="A devastating blow dealing 1.6x damage and weakening the target, reducing their damage by 30% for 2 turns. Higher ranks increase damage, weaken duration, and reduce cooldown.",
            key=pygame.K_q,
            target_mode="adjacent_enemy",
            base_power=1.6,
            uses_skill_power=True,
            cooldown=3,
            stamina_cost=3,  # Increased: basic but powerful skill
            make_target_status=lambda: StatusEffect(

                name="weakened",
                duration=2,
                outgoing_mult=0.7,
            ),
        )
    )

    # Enemy AI-only weakening attack
    crippling_blow = register(
        Skill(
            id="crippling_blow",
            name="Crippling Blow",
            description="Enemy attack that weakens you.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=1.0,
            uses_skill_power=False,
            cooldown=2,
            make_target_status=lambda: StatusEffect(
                name="weakened",
                duration=2,
                outgoing_mult=0.7,
            ),
        )
    )

    # --- Enemy archetype skills -------------------------------------------

    heavy_slam = register(
        Skill(
            id="heavy_slam",
            name="Heavy Slam",
            description="Crushing overhead blow (1.5x damage).",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=1.5,
            uses_skill_power=False,
            cooldown=2,
        )
    )

    poison_strike = register(
        Skill(
            id="poison_strike",
            name="Poison Strike",
            description="Slash that poisons the target for several turns.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=1.0,
            uses_skill_power=False,
            cooldown=3,
            make_target_status=lambda: StatusEffect(
                name="poisoned",
                duration=3,
                flat_damage_each_turn=2,
            ),
        )
    )

    dark_hex = register(
        Skill(
            id="dark_hex",
            name="Dark Hex",
            description="Curse the target, making them take more damage.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=0.9,
            uses_skill_power=True,
            cooldown=3,
            make_target_status=lambda: StatusEffect(
                name="cursed",
                duration=2,
                incoming_mult=1.25,
            ),
        )
    )

    feral_claws = register(
        Skill(
            id="feral_claws",
            name="Feral Claws",
            description="Rending claws that cause bleeding over time.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=1.1,
            uses_skill_power=False,
            cooldown=2,
            make_target_status=lambda: StatusEffect(
                name="bleeding",
                duration=2,
                flat_damage_each_turn=2,
            ),
        )
    )

    war_cry = register(
        Skill(
            id="war_cry",
            name="War Cry",
            description="Roared challenge that boosts outgoing damage for a short time.",
            key=None,  # AI-only
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=4,
            make_self_status=lambda: StatusEffect(
                name="war_cry",
                duration=2,
                outgoing_mult=1.25,
            ),
        )
    )

    # --- New skills unlocked by perks --------------------------------------

    # Blade perk: aggressive strike (Warrior/Rogue)
    lunge = register(
        Skill(
            id="lunge",
            name="Lunge",
            description="A quick forward strike dealing 1.25x damage. Higher ranks increase damage and reduce both cooldown and stamina cost, making it more spammable.",
            key=pygame.K_r,
            target_mode="adjacent_enemy",
            base_power=1.25,
            uses_skill_power=False,
            cooldown=2,
            stamina_cost=3,  # Increased: quick but costs more
            class_restrictions=["warrior", "rogue"],  # Physical melee classes
        )

    )


    # Ward perk: control skill (stun) - Warrior only
    shield_bash = register(
        Skill(
            id="shield_bash",
            name="Shield Bash",
            description="Smash your shield into the target, dealing 1.1x damage and stunning them for 1 turn. Higher ranks increase damage and stun duration, making it a powerful control tool.",
            key=pygame.K_e,
            target_mode="adjacent_enemy",
            base_power=1.1,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=4,  # Increased: control effect is powerful
            class_restrictions=["warrior"],  # Tank/defensive skill
            make_target_status=lambda: StatusEffect(
                name="stunned",
                duration=1,
                stunned=True,
            ),
        )
    )

    # Focus perk: big skill-power scaling hit - Mage/Rogue
    focus_blast = register(
        Skill(
            id="focus_blast",
            name="Focus Blast",
            description="Channel your inner power into a focused strike dealing 1.4x damage, scaling with your skill power. Higher ranks dramatically increase damage output, perfect for skill-power builds.",
            key=pygame.K_f,
            target_mode="adjacent_enemy",
            base_power=1.4,
            uses_skill_power=True,
            cooldown=3,
            stamina_cost=4,  # Increased: powerful skill-power scaling
            class_restrictions=["mage", "rogue"],  # Skill-power focused classes
        )
)

    nimble_step = register(
        Skill(
            id="nimble_step",
            name="Nimble Step",
            description="Use evasive footwork to reduce incoming damage by 50% until your next turn. Higher ranks increase duration and damage reduction, making you harder to hit.",
            key=pygame.K_t,
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=2,  # Increased: defensive utility is valuable
            class_restrictions=["rogue"],  # Mobility skill for rogues
            make_self_status=lambda: StatusEffect(

                name="nimble",
                duration=1,
                incoming_mult=0.5,
            ),
        )
    )

    # --- Warrior-specific skills ------------------------------------------------

    # Cleave: Attack multiple adjacent enemies
    cleave = register(
        Skill(
            id="cleave",
            name="Cleave",
            description="A sweeping strike that hits all adjacent enemies for 1.2x damage each. Higher ranks increase damage and expand the area of effect, devastating groups of enemies.",
            key=None,  # Will be assigned via perk or starting skill
            target_mode="adjacent_enemy",
            base_power=1.2,
            uses_skill_power=False,
            cooldown=4,
            stamina_cost=5,  # Increased: AoE is powerful
            class_restrictions=["warrior"],
            aoe_radius=1,
            aoe_shape="square",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    # Taunt: Force enemy to target you
    taunt = register(
        Skill(
            id="taunt",
            name="Taunt",
            description="Challenge the target, forcing them to attack you for 2 turns.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=3,  # Increased: control effect
            class_restrictions=["warrior"],
            make_target_status=lambda: StatusEffect(
                name="taunted",
                duration=2,
                # Note: taunt effect would need special handling in battle AI
            ),
        )
    )

    # Charge: Move and attack
    charge = register(
        Skill(
            id="charge",
            name="Charge",
            description="Rush forward and strike the target (1.3x damage).",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.3,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=4,  # Increased: mobility + damage
            class_restrictions=["warrior"],
        )
    )

    # Shield Wall: Defensive buff
    shield_wall = register(
        Skill(
            id="shield_wall",
            name="Shield Wall",
            description="Raise your guard, gaining +2 Defense for 2 turns.",
            key=None,
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=4,
            stamina_cost=3,  # Increased: defensive buff
            class_restrictions=["warrior"],
            make_self_status=lambda: StatusEffect(
                name="shield_wall",
                duration=2,
                # Defense boost would need special handling
            ),
        )
    )

    # --- Rogue-specific skills ------------------------------------------------

    # Backstab: High damage strike
    backstab = register(
        Skill(
            id="backstab",
            name="Backstab",
            description="A devastating precision strike dealing 2.0x damage when attacking from an advantageous position. Higher ranks dramatically increase damage, making it one of the most powerful single-target attacks.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=2.0,
            uses_skill_power=False,
            cooldown=4,
            stamina_cost=5,  # Increased: very high damage
            class_restrictions=["rogue"],
        )
    )

    # Shadow Strike: Teleport-like attack
    shadow_strike = register(
        Skill(
            id="shadow_strike",
            name="Shadow Strike",
            description="Strike from the shadows, dealing 1.5x damage.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.5,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=4,  # Increased: mobility + damage
            class_restrictions=["rogue"],
        )
    )

    # Poison Blade: Apply poison
    poison_blade = register(
        Skill(
            id="poison_blade",
            name="Poison Blade",
            description="Coated strike that poisons the target for 3 turns.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.0,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=3,  # Increased: DoT effect is valuable
            class_restrictions=["rogue"],
            make_target_status=lambda: StatusEffect(
                name="poisoned",
                duration=3,
                flat_damage_each_turn=2,
            ),
        )
    )

    # Evade: Next attack misses
    evade = register(
        Skill(
            id="evade",
            name="Evade",
            description="Dodge the next attack against you.",
            key=None,
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=2,  # Increased: defensive utility
            class_restrictions=["rogue"],
            make_self_status=lambda: StatusEffect(
                name="evading",
                duration=1,
                # Evade would need special handling in battle
            ),
        )
    )

    # --- Mage-specific skills ------------------------------------------------

    # Fireball: AoE damage with burn (ranged)
    fireball = register(
        Skill(
            id="fireball",
            name="Fireball",
            description="Hurl a ball of fire that explodes on impact, dealing 1.5x damage to all enemies in a large area and setting them ablaze for 2 turns. Higher ranks increase damage, burn duration, burn damage, and expand the explosion radius.",
            key=None,
            target_mode="any_enemy",
            base_power=1.5,  # Reduced slightly since it's AoE
            uses_skill_power=True,
            cooldown=4,
            mana_cost=7,  # Increased: AoE + DoT is powerful
            class_restrictions=["mage"],
            range_tiles=5,
            range_metric="manhattan",
            aoe_radius=2,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
            make_target_status=lambda: StatusEffect(
                name="burning",
                duration=2,
                flat_damage_each_turn=3,
            ),
        )
    )

    # Lightning Bolt: Chain damage (AoE, ranged)
    lightning_bolt = register(
        Skill(
            id="lightning_bolt",
            name="Lightning Bolt",
            description="Strike with lightning that arcs to nearby enemies (1.4x damage each).",
            key=None,
            target_mode="any_enemy",
            base_power=1.4,  # Reduced slightly since it's AoE
            uses_skill_power=True,
            cooldown=4,
            mana_cost=7,  # Increased: AoE damage is powerful
            class_restrictions=["mage"],
            range_tiles=5,
            range_metric="manhattan",
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    # Slow: Reduce enemy speed (melee-only touch spell)
    slow = register(
        Skill(
            id="slow",
            name="Slow",
            description="Encase the target in temporal magic, slowing them for 3 turns.",
            key=None,
            target_mode="adjacent_enemy",  # Melee-only touch spell
            base_power=0.0,
            uses_skill_power=True,
            cooldown=3,
            mana_cost=5,  # Increased: control effect
            class_restrictions=["mage"],
            make_target_status=lambda: StatusEffect(
                name="slowed",
                duration=3,
                # Speed reduction would need special handling
            ),
        )
    )

    # Magic Shield: Absorb damage (self-target, no weapon requirement)
    magic_shield = register(
        Skill(
            id="magic_shield",
            name="Magic Shield",
            description="Create a barrier that absorbs the next 20 damage.",
            key=None,
            target_mode="self",  # Self-target, no weapon requirement
            base_power=0.0,
            uses_skill_power=True,
            cooldown=4,
            mana_cost=6,  # Increased: defensive utility
            class_restrictions=["mage"],
            make_self_status=lambda: StatusEffect(
                name="magic_shield",
                duration=3,
                # Damage absorption would need special handling
            ),
        )
    )

    # Arcane Missile: Quick magic attack (ranged)
    arcane_missile = register(
        Skill(
            id="arcane_missile",
            name="Arcane Missile",
            description="Quick magical projectile (1.3x damage, low cooldown).",
            key=None,
            target_mode="any_enemy",
            base_power=1.3,
            uses_skill_power=True,
            cooldown=2,
            mana_cost=4,  # Increased: still cheap but balanced
            class_restrictions=["mage"],
            range_tiles=4,
            range_metric="manhattan",
        )
    )

    # --- Ranged Weapon Skills (for archers/ranged characters) --------------------

    # Quick Shot: Fast ranged attack
    quick_shot = register(
        Skill(
            id="quick_shot",
            name="Quick Shot",
            description="Rapid arrow shot (1.1x damage, no cooldown).",
            key=None,
            target_mode="any_enemy",
            base_power=1.1,
            uses_skill_power=False,
            cooldown=0,
            stamina_cost=2,  # Low cost for basic ranged attack
            range_tiles=4,
            range_metric="manhattan",
            requires_ranged_weapon=True,
        )
    )

    # Precise Shot: High damage ranged attack
    precise_shot = register(
        Skill(
            id="precise_shot",
            name="Precise Shot",
            description="Aimed shot dealing 1.5x damage with increased crit chance.",
            key=None,
            target_mode="any_enemy",
            base_power=1.5,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=4,  # Higher cost for better damage
            range_tiles=5,
            range_metric="manhattan",
            requires_ranged_weapon=True,
        )
    )

    # Multi-shot: Hit multiple enemies
    multi_shot = register(
        Skill(
            id="multi_shot",
            name="Multi-shot",
            description="Fire arrows at multiple enemies (1.0x damage each).",
            key=None,
            target_mode="any_enemy",
            base_power=1.0,
            uses_skill_power=False,
            cooldown=4,
            stamina_cost=5,
            range_tiles=4,
            range_metric="manhattan",
            requires_ranged_weapon=True,
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    # Piercing Shot: Line attack through enemies
    piercing_shot = register(
        Skill(
            id="piercing_shot",
            name="Piercing Shot",
            description="Arrow that pierces through enemies in a line (1.2x damage each).",
            key=None,
            target_mode="any_enemy",
            base_power=1.2,
            uses_skill_power=False,
            cooldown=4,
            stamina_cost=5,
            range_tiles=5,
            range_metric="manhattan",
            requires_ranged_weapon=True,
            # Note: Line AoE would need special handling, using circle for now
            aoe_radius=0,  # Single target for now, can be enhanced later
        )
    )

    # --- Ranged Magic Skills (for mages) -----------------------------------------

    # Magic Missile: Basic ranged magic attack (already exists, updating range)
    # Note: arcane_missile already updated above

    # Ice Bolt: Ranged ice attack with slow
    ice_bolt = register(
        Skill(
            id="ice_bolt",
            name="Ice Bolt",
            description="Hurl a bolt of ice dealing 1.4x damage and slowing the target.",
            key=None,
            target_mode="any_enemy",
            base_power=1.4,
            uses_skill_power=True,
            cooldown=3,
            mana_cost=5,
            class_restrictions=["mage"],
            range_tiles=5,
            range_metric="manhattan",
            make_target_status=lambda: StatusEffect(
                name="slowed",
                duration=2,
                # Speed reduction would need special handling
            ),
        )
    )

    # Chain Lightning: Ranged chain attack
    chain_lightning = register(
        Skill(
            id="chain_lightning",
            name="Chain Lightning",
            description="Lightning that chains between nearby enemies (1.3x damage each).",
            key=None,
            target_mode="any_enemy",
            base_power=1.3,
            uses_skill_power=True,
            cooldown=4,
            mana_cost=7,
            class_restrictions=["mage"],
            range_tiles=5,
            range_metric="manhattan",
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    # Shadow Bolt: Ranged dark magic
    shadow_bolt = register(
        Skill(
            id="shadow_bolt",
            name="Shadow Bolt",
            description="Dark magic projectile dealing 1.5x damage and weakening the target.",
            key=None,
            target_mode="any_enemy",
            base_power=1.5,
            uses_skill_power=True,
            cooldown=3,
            mana_cost=6,
            class_restrictions=["mage"],
            range_tiles=5,
            range_metric="manhattan",
            make_target_status=lambda: StatusEffect(
                name="weakened",
                duration=2,
                outgoing_mult=0.8,
            ),
        )
    )

    # --- Cross-class skills (available to multiple classes) --------------------

    # Second Wind: Restore HP and stamina
    second_wind = register(
        Skill(
            id="second_wind",
            name="Second Wind",
            description="Restore 30% HP and stamina.",
            key=None,
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=5,
            stamina_cost=2,  # Increased: healing is powerful, should cost something
            class_restrictions=["warrior", "rogue"],  # Physical classes
            # Healing would need special handling
        )
    )

    # --- Additional Enemy-Only Skills ------------------------------------------

    # Life Drain: Attack that heals the enemy
    life_drain = register(
        Skill(
            id="life_drain",
            name="Life Drain",
            description="Drain life from the target, healing yourself for 50% of damage dealt.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=1.2,
            uses_skill_power=False,
            cooldown=4,
            # Healing handled in battle AI
        )
    )

    # Mark Target: Next attack on marked target deals extra damage
    mark_target = register(
        Skill(
            id="mark_target",
            name="Mark Target",
            description="Mark the target, causing them to take 25% more damage from all sources for 3 turns.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=3,
            make_target_status=lambda: StatusEffect(
                name="marked",
                duration=3,
                incoming_mult=1.25,
            ),
        )
    )

    # Berserker Rage: Low HP triggers damage boost (self-buff)
    berserker_rage = register(
        Skill(
            id="berserker_rage",
            name="Berserker Rage",
            description="Enter a rage, increasing damage dealt by 50% for 3 turns.",
            key=None,  # AI-only
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=5,
            make_self_status=lambda: StatusEffect(
                name="berserker_rage",
                duration=3,
                outgoing_mult=1.5,
            ),
        )
    )

    # Regeneration: Passive HP regen each turn
    regeneration = register(
        Skill(
            id="regeneration",
            name="Regeneration",
            description="Begin regenerating health each turn for 4 turns.",
            key=None,  # AI-only
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=6,
            make_self_status=lambda: StatusEffect(
                name="regenerating",
                duration=4,
                # Regen handled in battle AI (heals 2 HP per turn)
            ),
        )
    )

    # Counter Attack: Retaliates when hit (status that triggers on next hit)
    counter_attack = register(
        Skill(
            id="counter_attack",
            name="Counter Stance",
            description="Prepare to counter the next attack, dealing 1.5x damage back.",
            key=None,  # AI-only
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=4,
            make_self_status=lambda: StatusEffect(
                name="counter_stance",
                duration=2,
                # Counter handled in battle AI
            ),
        )
    )

    # Disease: Stacking DoT (like poison but stacks)
    disease_strike = register(
        Skill(
            id="disease_strike",
            name="Disease Strike",
            description="Infect the target with a stacking disease that deals damage over time.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=0.9,
            uses_skill_power=False,
            cooldown=3,
            make_target_status=lambda: StatusEffect(
                name="diseased",
                duration=3,
                stacks=1,
                flat_damage_each_turn=1,  # Stacks increase damage
            ),
        )
    )

    # Fear: AoE stun effect
    fear_scream = register(
        Skill(
            id="fear_scream",
            name="Fear Scream",
            description="Scream in terror, stunning all nearby enemies for 1 turn.",
            key=None,  # AI-only
            target_mode="self",  # Affects all adjacent enemies
            base_power=0.0,
            uses_skill_power=False,
            cooldown=5,
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
            aoe_affects_self=False,
            make_target_status=lambda: StatusEffect(
                name="stunned",
                duration=1,
                stunned=True,
            ),
        )
    )

    # Heal Ally: Support skill for healing other enemies
    heal_ally = register(
        Skill(
            id="heal_ally",
            name="Heal Ally",
            description="Restore health to an injured ally.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",  # Actually targets allies, handled in AI
            base_power=0.0,
            uses_skill_power=False,
            cooldown=4,
            # Healing handled in battle AI
        )
    )

    # Buff Ally: Support skill for buffing other enemies
    buff_ally = register(
        Skill(
            id="buff_ally",
            name="Empower Ally",
            description="Grant an ally increased damage for 3 turns.",
            key=None,  # AI-only
            target_mode="adjacent_enemy",  # Actually targets allies, handled in AI
            base_power=0.0,
            uses_skill_power=False,
            cooldown=4,
            make_target_status=lambda: StatusEffect(
                name="empowered",
                duration=3,
                outgoing_mult=1.3,
            ),
        )
    )

    # --- New AoE Skills --------------------------------------------------------

    # Warrior AoE Skills
    whirlwind = register(
        Skill(
            id="whirlwind",
            name="Whirlwind",
            description="Spin attack hitting all adjacent enemies (1.1x damage each).",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.1,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=5,
            class_restrictions=["warrior"],
            aoe_radius=1,
            aoe_shape="square",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    ground_slam = register(
        Skill(
            id="ground_slam",
            name="Ground Slam",
            description="Slam the ground, dealing 1.3x damage to all enemies in a small area.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.3,
            uses_skill_power=False,
            cooldown=4,
            stamina_cost=6,
            class_restrictions=["warrior"],
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    # Rogue AoE Skills
    fan_of_knives = register(
        Skill(
            id="fan_of_knives",
            name="Fan of Knives",
            description="Throw knives in a wide arc, hitting multiple enemies (1.0x damage each).",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.0,
            uses_skill_power=False,
            cooldown=3,
            stamina_cost=4,
            class_restrictions=["rogue"],
            aoe_radius=1,
            aoe_shape="square",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    smoke_bomb = register(
        Skill(
            id="smoke_bomb",
            name="Smoke Bomb",
            description="Throw a smoke bomb, weakening all enemies in the area for 2 turns.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=4,
            stamina_cost=5,
            class_restrictions=["rogue"],
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
            make_target_status=lambda: StatusEffect(
                name="weakened",
                duration=2,
                outgoing_mult=0.7,
            ),
        )
    )

    # Mage AoE Skills
    meteor_strike = register(
        Skill(
            id="meteor_strike",
            name="Meteor Strike",
            description="Call down a meteor, dealing massive 2.0x damage in a large area.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=2.0,
            uses_skill_power=True,
            cooldown=6,
            mana_cost=10,
            class_restrictions=["mage"],
            aoe_radius=2,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    frost_nova = register(
        Skill(
            id="frost_nova",
            name="Frost Nova",
            description="Freeze all nearby enemies, dealing 1.2x damage and stunning them for 1 turn.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.2,
            uses_skill_power=True,
            cooldown=4,
            mana_cost=7,
            class_restrictions=["mage"],
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
            make_target_status=lambda: StatusEffect(
                name="stunned",
                duration=1,
                stunned=True,
            ),
        )
    )

    blizzard = register(
        Skill(
            id="blizzard",
            name="Blizzard",
            description="Summon a blizzard that damages all enemies in a large area over time (1.0x damage + DoT).",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.0,
            uses_skill_power=True,
            cooldown=5,
            mana_cost=8,
            class_restrictions=["mage"],
            aoe_radius=2,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
            make_target_status=lambda: StatusEffect(
                name="chilled",
                duration=3,
                flat_damage_each_turn=2,
            ),
        )
    )

    # Enemy-only AoE Skills
    explosive_strike = register(
        Skill(
            id="explosive_strike",
            name="Explosive Strike",
            description="Strike that explodes, damaging nearby enemies (1.3x damage).",
            key=None,  # AI-only
            target_mode="adjacent_enemy",
            base_power=1.3,
            uses_skill_power=False,
            cooldown=4,
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
        )
    )

    roar = register(
        Skill(
            id="roar",
            name="Roar",
            description="Terrifying roar that weakens all nearby enemies for 2 turns.",
            key=None,  # AI-only
            target_mode="self",
            base_power=0.0,
            uses_skill_power=False,
            cooldown=5,
            aoe_radius=1,
            aoe_shape="circle",
            aoe_affects_enemies=True,
            aoe_affects_allies=False,
            aoe_affects_self=False,
            make_target_status=lambda: StatusEffect(
                name="weakened",
                duration=2,
                outgoing_mult=0.7,
            ),
        )
    )

    # guard / power_strike / crippling_blow / heavy_slam / poison_strike / dark_hex / feral_claws / war_cry
    # plus lunge / shield_bash / focus_blast / nimble_step variables are not used further,
    # but keeping them named makes it obvious what we're defining.


def _register_skill_rank_effects() -> None:
    """
    Register custom rank effects for each skill to make upgrades meaningful and unique.
    Each skill gets logical improvements based on what it does.
    """
    
    # Guard: Defensive skill - longer duration, better damage reduction
    register_rank_effects("guard", SkillRankEffects(
        status_duration_bonus=1,  # +1 turn per rank (starts at 1, becomes 2-6)
        status_strength_bonus=-0.05,  # Better reduction: 0.5 -> 0.45 -> 0.4 -> 0.35 -> 0.3 -> 0.25
        # No cost reduction since guard has no cost
    ))
    
    # Power Strike: Damage + weaken - more damage, longer weaken duration
    register_rank_effects("power_strike", SkillRankEffects(
        power_per_rank=0.15,  # +15% per rank (better scaling)
        status_duration_bonus=1,  # Weaken lasts longer: 2 -> 3 -> 4 -> 5 -> 6 -> 7
        status_strength_bonus=-0.02,  # Weaken gets stronger: 0.7 -> 0.68 -> 0.66 -> etc.
        cooldown_reduction_per_rank=0.5,  # -0.5 turns per rank (faster cooldown)
        cost_reduction_per_rank=0.3,  # Slight stamina cost reduction
    ))
    
    # Lunge: Quick strike - faster cooldown, more damage
    register_rank_effects("lunge", SkillRankEffects(
        power_per_rank=0.10,  # Standard +10% per rank
        cooldown_reduction_per_rank=0.5,  # -0.5 turns per rank (becomes spammable)
        cost_reduction_per_rank=0.5,  # Reduce stamina cost
    ))
    
    # Shield Bash: Control skill - longer stun, more damage
    register_rank_effects("shield_bash", SkillRankEffects(
        power_per_rank=0.12,  # Better damage scaling
        status_duration_bonus=1,  # Stun lasts longer: 1 -> 2 -> 3 -> 4 -> 5 -> 6
        cooldown_reduction_per_rank=0.4,  # Better cooldown reduction
        cost_reduction_per_rank=0.3,  # Reduce stamina cost
    ))
    
    # Focus Blast: Skill-power scaling - much more damage
    register_rank_effects("focus_blast", SkillRankEffects(
        power_per_rank=0.18,  # +18% per rank (stronger scaling for skill-power builds)
        cooldown_reduction_per_rank=0.5,  # Better cooldown reduction
        cost_reduction_per_rank=0.4,  # Reduce stamina/mana cost
    ))
    
    # Nimble Step: Defensive - longer duration, better reduction
    register_rank_effects("nimble_step", SkillRankEffects(
        status_duration_bonus=1,  # +1 turn per rank
        status_strength_bonus=-0.05,  # Better reduction: 0.5 -> 0.45 -> 0.4 -> etc.
        cooldown_reduction_per_rank=0.5,
    ))
    
    # Cleave: AoE - more damage, larger radius at higher ranks
    register_rank_effects("cleave", SkillRankEffects(
        power_per_rank=0.14,  # +14% per rank (better scaling)
        aoe_radius_bonus=1,  # +1 radius
        aoe_radius_ranks=[2, 4],  # +1 at rank 2, +1 more at rank 4 (earlier radius increase)
        cooldown_reduction_per_rank=0.5,  # Better cooldown reduction
        cost_reduction_per_rank=0.4,  # Reduce stamina cost
    ))
    
    # Taunt: Control - longer duration
    register_rank_effects("taunt", SkillRankEffects(
        status_duration_bonus=1,  # +1 turn per rank: 2 -> 3 -> 4 -> 5 -> 6 -> 7
        cooldown_reduction_per_rank=0.5,
    ))
    
    # Charge: Mobility + damage - more damage, faster cooldown
    register_rank_effects("charge", SkillRankEffects(
        power_per_rank=0.12,  # +12% per rank
        cooldown_reduction_per_rank=0.5,  # -0.5 turns per rank
    ))
    
    # Shield Wall: Defensive buff - longer duration, more defense
    register_rank_effects("shield_wall", SkillRankEffects(
        status_duration_bonus=1,  # +1 turn per rank
        # Note: Defense boost would need special handling in combat
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Backstab: High damage - massive damage scaling
    register_rank_effects("backstab", SkillRankEffects(
        power_per_rank=0.25,  # +25% per rank (very high damage scaling)
        cooldown_reduction_per_rank=0.4,  # -0.4 turns per rank (faster cooldown)
        cost_reduction_per_rank=0.5,  # Reduce stamina cost
    ))
    
    # Shadow Strike: Mobility + damage - more damage
    register_rank_effects("shadow_strike", SkillRankEffects(
        power_per_rank=0.12,  # +12% per rank
        cooldown_reduction_per_rank=0.5,
    ))
    
    # Poison Blade: DoT - longer duration, more DoT damage
    register_rank_effects("poison_blade", SkillRankEffects(
        power_per_rank=0.10,  # Better damage increase
        status_duration_bonus=1,  # +1 turn per rank: 3 -> 4 -> 5 -> 6 -> 7 -> 8
        dot_damage_bonus=1,  # +1 damage per turn per rank: 2 -> 3 -> 4 -> 5 -> 6 -> 7
        cooldown_reduction_per_rank=0.4,  # Slight cooldown reduction
        cost_reduction_per_rank=0.3,  # Reduce stamina cost
    ))
    
    # Evade: Defensive - longer duration
    register_rank_effects("evade", SkillRankEffects(
        status_duration_bonus=1,  # +1 turn per rank
        cooldown_reduction_per_rank=0.5,
    ))
    
    # Fireball: AoE + DoT - more damage, larger radius, more burn damage
    register_rank_effects("fireball", SkillRankEffects(
        power_per_rank=0.15,  # +15% per rank (better scaling)
        aoe_radius_bonus=1,  # +1 radius
        aoe_radius_ranks=[2, 4],  # +1 at rank 2, +1 more at rank 4 (earlier radius increase)
        status_duration_bonus=1,  # Burn lasts longer: 2 -> 3 -> 4 -> 5 -> 6 -> 7
        dot_damage_bonus=1,  # +1 burn damage per turn per rank: 3 -> 4 -> 5 -> 6 -> 7 -> 8
        cooldown_reduction_per_rank=0.4,  # Slight cooldown reduction
    ))
    
    # Lightning Bolt: AoE - more damage, larger radius
    register_rank_effects("lightning_bolt", SkillRankEffects(
        power_per_rank=0.12,  # +12% per rank
        aoe_radius_bonus=1,  # +1 radius
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Slow: Control - longer duration
    register_rank_effects("slow", SkillRankEffects(
        status_duration_bonus=1,  # +1 turn per rank: 3 -> 4 -> 5 -> 6 -> 7 -> 8
        cooldown_reduction_per_rank=0.5,
    ))
    
    # Magic Shield: Defensive - longer duration, more absorption
    register_rank_effects("magic_shield", SkillRankEffects(
        status_duration_bonus=1,  # +1 turn per rank
        # Note: Absorption amount would need special handling
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Arcane Missile: Quick attack - more damage, faster cooldown
    register_rank_effects("arcane_missile", SkillRankEffects(
        power_per_rank=0.10,
        cooldown_reduction_per_rank=0.5,  # Can become 0 cooldown at rank 2
        cost_reduction_per_rank=0.5,  # Reduce mana cost
    ))
    
    # Second Wind: Healing - restore more HP/stamina
    register_rank_effects("second_wind", SkillRankEffects(
        # Note: Healing percentage would need special handling
        cooldown_reduction_per_rank=0.5,  # Faster cooldown
    ))
    
    # Whirlwind: AoE - more damage, larger radius
    register_rank_effects("whirlwind", SkillRankEffects(
        power_per_rank=0.12,
        aoe_radius_bonus=1,
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.5,
    ))
    
    # Ground Slam: AoE - more damage, larger radius
    register_rank_effects("ground_slam", SkillRankEffects(
        power_per_rank=0.12,
        aoe_radius_bonus=1,
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Fan of Knives: AoE - more damage
    register_rank_effects("fan_of_knives", SkillRankEffects(
        power_per_rank=0.12,
        aoe_radius_bonus=1,
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.5,
    ))
    
    # Smoke Bomb: AoE control - longer duration, larger radius
    register_rank_effects("smoke_bomb", SkillRankEffects(
        status_duration_bonus=1,  # +1 turn per rank
        aoe_radius_bonus=1,
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Meteor Strike: Massive AoE - more damage, larger radius
    register_rank_effects("meteor_strike", SkillRankEffects(
        power_per_rank=0.18,  # +18% per rank (very high damage scaling)
        aoe_radius_bonus=1,
        aoe_radius_ranks=[2, 4],  # +1 at rank 2, +1 more at rank 4
        cooldown_reduction_per_rank=0.4,  # Better cooldown reduction
        cost_reduction_per_rank=0.5,  # Reduce mana cost (expensive skill)
    ))
    
    # Frost Nova: AoE + stun - more damage, longer stun, larger radius
    register_rank_effects("frost_nova", SkillRankEffects(
        power_per_rank=0.12,
        status_duration_bonus=1,  # Stun lasts longer
        aoe_radius_bonus=1,
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Blizzard: AoE + DoT - more damage, longer DoT, larger radius
    register_rank_effects("blizzard", SkillRankEffects(
        power_per_rank=0.12,
        status_duration_bonus=1,  # Chill lasts longer
        dot_damage_bonus=1,  # +1 damage per turn per rank
        aoe_radius_bonus=1,
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.4,
    ))
    
    # --- Ranged Weapon Skills Rank Effects ---
    
    # Quick Shot: Fast ranged - more damage, cost reduction
    register_rank_effects("quick_shot", SkillRankEffects(
        power_per_rank=0.10,
        cost_reduction_per_rank=0.3,  # Reduce stamina cost
    ))
    
    # Precise Shot: High damage ranged - more damage, range increase
    register_rank_effects("precise_shot", SkillRankEffects(
        power_per_rank=0.15,  # +15% per rank (high damage scaling)
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Multi-shot: AoE ranged - more damage, larger radius
    register_rank_effects("multi_shot", SkillRankEffects(
        power_per_rank=0.12,
        aoe_radius_bonus=1,
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Piercing Shot: Line attack - more damage
    register_rank_effects("piercing_shot", SkillRankEffects(
        power_per_rank=0.12,
        cooldown_reduction_per_rank=0.4,
    ))
    
    # --- Ranged Magic Skills Rank Effects ---
    
    # Arcane Missile: Quick magic - more damage, faster cooldown
    register_rank_effects("arcane_missile", SkillRankEffects(
        power_per_rank=0.10,
        cooldown_reduction_per_rank=0.5,  # Can become 0 cooldown at rank 2
        cost_reduction_per_rank=0.5,  # Reduce mana cost
    ))
    
    # Ice Bolt: Ranged ice - more damage, longer slow
    register_rank_effects("ice_bolt", SkillRankEffects(
        power_per_rank=0.12,
        status_duration_bonus=1,  # Slow lasts longer
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Chain Lightning: Ranged chain - more damage, larger radius
    register_rank_effects("chain_lightning", SkillRankEffects(
        power_per_rank=0.12,
        aoe_radius_bonus=1,
        aoe_radius_ranks=[3, 5],  # +1 at rank 3, +1 more at rank 5
        cooldown_reduction_per_rank=0.4,
    ))
    
    # Shadow Bolt: Ranged dark magic - more damage, longer weaken
    register_rank_effects("shadow_bolt", SkillRankEffects(
        power_per_rank=0.12,
        status_duration_bonus=1,  # Weaken lasts longer
        cooldown_reduction_per_rank=0.4,
    ))


_build_core_skills()
_register_skill_rank_effects()
