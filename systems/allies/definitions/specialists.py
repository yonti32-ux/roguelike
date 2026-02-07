"""
Specialist ally archetypes.

Unique and specialized allies with distinct roles.
"""

from systems.allies import register_archetype
from systems.allies.types import AllyArchetype


def register_specialist_archetypes() -> None:
    """Register specialist-type ally archetypes."""
    
    # Assassin - Stealth ally
    register_archetype(
        AllyArchetype(
            id="assassin",
            name="Assassin",
            role="Assassin",
            ai_profile="assassin",
            base_hp=24,
            hp_per_level=4.5,
            base_attack=9,
            atk_per_level=1.6,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=15,
            init_per_level=0.8,
            skill_ids=["crippling_blow", "poison_strike", "nimble_step"],
            party_type_ids=[],  # For future expansion
            tags=["assassin", "skirmisher"],
            description="A deadly assassin who strikes from the shadows.",
        )
    )
    
    # Mage - Caster ally
    register_archetype(
        AllyArchetype(
            id="mage",
            name="Mage",
            role="Invoker",
            ai_profile="caster",
            base_hp=22,
            hp_per_level=4,
            base_attack=4,
            atk_per_level=0.8,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.8,
            skill_power_per_level=0.06,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["dark_hex", "mark_target"],
            party_type_ids=[],  # For future expansion
            tags=["caster", "mage"],
            description="A mage who wields powerful magic.",
        )
    )
    
    # Archer - Ranged specialist
    register_archetype(
        AllyArchetype(
            id="archer",
            name="Archer",
            role="Skirmisher",
            ai_profile="skirmisher",
            base_hp=26,
            hp_per_level=4.8,
            base_attack=8,
            atk_per_level=1.5,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=13,
            init_per_level=0.6,
            skill_ids=["crippling_blow", "mark_target"],
            party_type_ids=["ranger", "scout"],
            tags=["ranger", "archer"],
            description="A skilled archer with deadly aim.",
        )
    )
    
    # Berserker - Aggressive fighter
    register_archetype(
        AllyArchetype(
            id="berserker",
            name="Berserker",
            role="Berserker",
            ai_profile="berserker",
            base_hp=38,
            hp_per_level=6.5,
            base_attack=9,
            atk_per_level=1.7,
            base_defense=2,
            def_per_level=0.3,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=12,
            init_per_level=0.5,
            skill_ids=["heavy_slam", "berserker_rage"],
            party_type_ids=[],  # For future expansion
            tags=["military", "berserker"],
            description="A berserker who fights with reckless fury.",
        )
    )
    
    # Duelist - Skilled fighter
    register_archetype(
        AllyArchetype(
            id="duelist",
            name="Duelist",
            role="Fighter",
            ai_profile="tactician",
            base_hp=32,
            hp_per_level=5.5,
            base_attack=9,
            atk_per_level=1.6,
            base_defense=2,
            def_per_level=0.4,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=14,
            init_per_level=0.7,
            skill_ids=["crippling_blow", "nimble_step", "mark_target"],
            party_type_ids=["mercenary", "adventurer"],
            tags=["military", "duelist"],
            description="A skilled duelist who excels in one-on-one combat.",
        )
    )
    
    # Warden - Protective specialist
    register_archetype(
        AllyArchetype(
            id="warden",
            name="Warden",
            role="Guardian",
            ai_profile="defender",
            base_hp=41,
            hp_per_level=6.8,
            base_attack=7,
            atk_per_level=1.3,
            base_defense=5,
            def_per_level=0.7,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["guard", "heavy_slam", "war_cry"],
            party_type_ids=["guard", "knight"],
            tags=["guardian", "military"],
            description="A warden who protects and enforces order.",
        )
    )
