"""
Support ally archetypes.

Clerics, healers, and support allies that buff and heal the party.
"""

from systems.allies import register_archetype
from systems.allies.types import AllyArchetype


def register_support_archetypes() -> None:
    """Register support-type ally archetypes."""
    
    # Cleric - Support healer
    register_archetype(
        AllyArchetype(
            id="cleric",
            name="Cleric",
            role="Support",
            ai_profile="support",
            base_hp=30,
            hp_per_level=5,
            base_attack=5,
            atk_per_level=1.0,
            base_defense=2,
            def_per_level=0.3,
            base_skill_power=1.5,
            skill_power_per_level=0.05,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["heal_ally", "buff_ally"],
            party_type_ids=[],  # Not used by any party type yet (for future expansion)
            tags=["support", "healer"],
            description="A cleric who heals and supports allies.",
        )
    )
    
    # Paladin - Support fighter hybrid
    register_archetype(
        AllyArchetype(
            id="paladin",
            name="Paladin",
            role="Support Guardian",
            ai_profile="defender",
            base_hp=40,
            hp_per_level=6.5,
            base_attack=7,
            atk_per_level=1.3,
            base_defense=4,
            def_per_level=0.6,
            base_skill_power=1.2,
            skill_power_per_level=0.04,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["guard", "heal_ally", "war_cry"],
            party_type_ids=[],  # For future expansion
            tags=["support", "guardian", "military"],
            description="A holy warrior who protects and heals.",
        )
    )
    
    # Bard - Support buffer
    register_archetype(
        AllyArchetype(
            id="bard",
            name="Bard",
            role="Support",
            ai_profile="support",
            base_hp=25,
            hp_per_level=4.5,
            base_attack=5,
            atk_per_level=1.0,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.3,
            skill_power_per_level=0.05,
            base_initiative=12,
            init_per_level=0.5,
            skill_ids=["buff_ally", "war_cry"],
            party_type_ids=[],  # For future expansion
            tags=["support", "buffer"],
            description="A bard who inspires and buffs allies.",
        )
    )
    
    # Druid - Nature support
    register_archetype(
        AllyArchetype(
            id="druid",
            name="Druid",
            role="Support",
            ai_profile="support",
            base_hp=28,
            hp_per_level=5,
            base_attack=5,
            atk_per_level=1.0,
            base_defense=2,
            def_per_level=0.3,
            base_skill_power=1.4,
            skill_power_per_level=0.05,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["heal_ally", "buff_ally"],
            party_type_ids=[],  # For future expansion
            tags=["support", "healer", "nature"],
            description="A druid who draws power from nature to aid allies.",
        )
    )
    
    # Priest - Healer variant
    register_archetype(
        AllyArchetype(
            id="priest",
            name="Priest",
            role="Support",
            ai_profile="support",
            base_hp=29,
            hp_per_level=5.2,
            base_attack=5,
            atk_per_level=1.0,
            base_defense=2,
            def_per_level=0.3,
            base_skill_power=1.5,
            skill_power_per_level=0.05,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["heal_ally", "buff_ally"],
            party_type_ids=[],  # For future expansion
            tags=["support", "healer", "religious"],
            description="A priest who heals through divine power.",
        )
    )
    
    # Shaman - Tribal support
    register_archetype(
        AllyArchetype(
            id="shaman",
            name="Shaman",
            role="Support",
            ai_profile="support",
            base_hp=27,
            hp_per_level=4.8,
            base_attack=5,
            atk_per_level=1.0,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.4,
            skill_power_per_level=0.05,
            base_initiative=12,
            init_per_level=0.5,
            skill_ids=["heal_ally", "buff_ally"],
            party_type_ids=[],  # For future expansion
            tags=["support", "healer"],
            description="A shaman who channels spiritual energy to aid the party.",
        )
    )
