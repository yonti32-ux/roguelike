# systems/skills.py

from dataclasses import dataclass
from typing import Optional, Literal, Callable, Dict

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

    # Blade perk: aggressive strike
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
        )
    )

    # Ward perk: control skill (stun)
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
            make_target_status=lambda: StatusEffect(
                name="stunned",
                duration=1,
                stunned=True,
            ),
        )
    )

    # Focus perk: big skill-power scaling hit
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
            make_self_status=lambda: StatusEffect(
                name="nimble",
                duration=1,
                incoming_mult=0.5,
            ),
        )
    )

    # guard / power_strike / crippling_blow / heavy_slam / poison_strike / dark_hex / feral_claws / war_cry
    # plus lunge / shield_bash / focus_blast / nimble_step variables are not used further,
    # but keeping them named makes it obvious what we're defining.
_build_core_skills()
