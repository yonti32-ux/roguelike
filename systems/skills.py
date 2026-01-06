# systems/skills.py

from dataclasses import dataclass, field
from typing import Optional, Literal, Callable, Dict, List

import pygame

from .statuses import StatusEffect


TargetMode = Literal["self", "adjacent_enemy"]


@dataclass
class Skill:
    """
    Generic combat skill definition.

    - id:          internal id used for cooldown tracking
    - name:        display name
    - description: UI / tooltip text
    - key:         pygame key constant to trigger it (None = AI only)
    - target_mode: "self" or "adjacent_enemy" for now
    - base_power:  multiplier on the user's attack stat
    - uses_skill_power: if True, multiplies damage by entity.skill_power
    - cooldown:    number of that unit's turns before reuse
    - max_rank:    maximum rank this skill can be upgraded to (default 5)
    - class_restrictions: List of class IDs that can use this skill.
                          Empty list means all classes can use it.
    - make_self_status / make_target_status: factories returning
      StatusEffect instances to apply when the skill fires.
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


def calculate_skill_power_at_rank(base_power: float, rank: int) -> float:
    """
    Calculate the effective power of a skill at a given rank.
    
    Each rank increases power by 10%:
    Rank 0 (unranked): base_power
    Rank 1: base_power * 1.1
    Rank 2: base_power * 1.2
    Rank 3: base_power * 1.3
    Rank 4: base_power * 1.4
    Rank 5: base_power * 1.5
    """
    if rank <= 0:
        return base_power
    return base_power * (1.0 + 0.1 * rank)


def calculate_skill_cooldown_at_rank(base_cooldown: int, rank: int) -> int:
    """
    Calculate the effective cooldown of a skill at a given rank.
    
    Cooldown reduces by 1 turn every 2 ranks:
    Rank 0-1: base_cooldown
    Rank 2-3: base_cooldown - 1 (minimum 0)
    Rank 4-5: base_cooldown - 2 (minimum 0)
    """
    if rank <= 1:
        return max(0, base_cooldown)
    reduction = rank // 2
    return max(0, base_cooldown - reduction)


def calculate_skill_cost_at_rank(base_cost: int, rank: int, cost_type: str = "stamina") -> int:
    """
    Calculate the effective cost (stamina/mana) of a skill at a given rank.
    
    Cost reduces by 1 per rank (minimum 0):
    Rank 0: base_cost
    Rank 1: base_cost - 1
    Rank 2: base_cost - 2
    etc.
    """
    if rank <= 0:
        return max(0, base_cost)
    return max(0, base_cost - rank)


# --- Core skill definitions -------------------------------------------------


def _build_core_skills() -> None:
    # Always-available defensive skill
    guard = register(
        Skill(
            id="guard",
            name="Guard",
            description="Brace to halve incoming damage until your next turn.",
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
            description="Heavy blow that weakens the target for 2 turns.",
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
            description="Driving strike (1.25x damage).",
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
            description="Smash the target, dealing 1.1x damage and stunning for 1 turn.",
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
            description="Focused blow that scales heavily with skill power (1.4x).",
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
            description="Evasive footwork: halve damage taken until your next turn.",
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
            description="Sweeping strike hitting all adjacent enemies (1.2x damage each).",
            key=None,  # Will be assigned via perk or starting skill
            target_mode="adjacent_enemy",
            base_power=1.2,
            uses_skill_power=False,
            cooldown=4,
            stamina_cost=5,  # Increased: AoE is powerful
            class_restrictions=["warrior"],
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
            description="Precise strike from an advantageous position (2.0x damage).",
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

    # Fireball: AoE damage with burn
    fireball = register(
        Skill(
            id="fireball",
            name="Fireball",
            description="Hurl a ball of fire, dealing 1.8x damage and burning the target.",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.8,
            uses_skill_power=True,
            cooldown=3,
            mana_cost=6,  # Increased: high damage + DoT
            class_restrictions=["mage"],
            make_target_status=lambda: StatusEffect(
                name="burning",
                duration=2,
                flat_damage_each_turn=3,
            ),
        )
    )

    # Lightning Bolt: Chain damage
    lightning_bolt = register(
        Skill(
            id="lightning_bolt",
            name="Lightning Bolt",
            description="Strike with lightning that chains to nearby enemies (1.6x damage).",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.6,
            uses_skill_power=True,
            cooldown=4,
            mana_cost=7,  # Increased: chain damage is powerful
            class_restrictions=["mage"],
        )
    )

    # Slow: Reduce enemy speed
    slow = register(
        Skill(
            id="slow",
            name="Slow",
            description="Encase the target in temporal magic, slowing them for 3 turns.",
            key=None,
            target_mode="adjacent_enemy",
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

    # Magic Shield: Absorb damage
    magic_shield = register(
        Skill(
            id="magic_shield",
            name="Magic Shield",
            description="Create a barrier that absorbs the next 20 damage.",
            key=None,
            target_mode="self",
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

    # Arcane Missile: Quick magic attack
    arcane_missile = register(
        Skill(
            id="arcane_missile",
            name="Arcane Missile",
            description="Quick magical projectile (1.3x damage, low cooldown).",
            key=None,
            target_mode="adjacent_enemy",
            base_power=1.3,
            uses_skill_power=True,
            cooldown=2,
            mana_cost=4,  # Increased: still cheap but balanced
            class_restrictions=["mage"],
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

    # guard / power_strike / crippling_blow / heavy_slam / poison_strike / dark_hex / feral_claws / war_cry
    # plus lunge / shield_bash / focus_blast / nimble_step variables are not used further,
    # but keeping them named makes it obvious what we're defining.
_build_core_skills()
