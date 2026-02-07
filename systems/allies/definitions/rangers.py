"""
Ranger ally archetypes.

Rangers, scouts, and mobile skirmishing allies.
"""

from systems.allies import register_archetype
from systems.allies.types import AllyArchetype


def register_ranger_archetypes() -> None:
    """Register ranger-type ally archetypes."""
    
    # Ranger - Mobile skirmisher
    register_archetype(
        AllyArchetype(
            id="ranger",
            name="Ranger",
            role="Skirmisher",
            ai_profile="skirmisher",
            base_hp=28,
            hp_per_level=5,
            base_attack=7,
            atk_per_level=1.4,
            base_defense=2,
            def_per_level=0.3,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=13,
            init_per_level=0.6,
            skill_ids=["crippling_blow", "nimble_step"],
            party_type_ids=["ranger"],
            tags=["ranger", "skirmisher"],
            description="A skilled ranger who patrols the wilderness.",
        )
    )
    
    # Scout - Fast reconnaissance
    register_archetype(
        AllyArchetype(
            id="scout",
            name="Scout",
            role="Skirmisher",
            ai_profile="skirmisher",
            base_hp=25,
            hp_per_level=4.5,
            base_attack=6,
            atk_per_level=1.3,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=14,
            init_per_level=0.7,
            skill_ids=["crippling_blow", "nimble_step"],
            party_type_ids=["scout"],
            tags=["ranger", "skirmisher"],
            description="A swift scout who excels at hit-and-run tactics.",
        )
    )
    
    # Tracker - Specialized hunter
    register_archetype(
        AllyArchetype(
            id="tracker",
            name="Tracker",
            role="Skirmisher",
            ai_profile="skirmisher",
            base_hp=27,
            hp_per_level=5,
            base_attack=7,
            atk_per_level=1.4,
            base_defense=2,
            def_per_level=0.3,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=13,
            init_per_level=0.6,
            skill_ids=["crippling_blow", "mark_target", "nimble_step"],
            party_type_ids=["ranger", "scout"],
            tags=["ranger", "skirmisher"],
            description="A skilled tracker who hunts down enemies.",
        )
    )
    
    # Hunter - Ranged specialist
    register_archetype(
        AllyArchetype(
            id="hunter",
            name="Hunter",
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
            party_type_ids=["ranger"],
            tags=["ranger", "skirmisher"],
            description="A hunter skilled with ranged weapons.",
        )
    )
    
    # Pathfinder - Explorer guide
    register_archetype(
        AllyArchetype(
            id="pathfinder",
            name="Pathfinder",
            role="Skirmisher",
            ai_profile="skirmisher",
            base_hp=29,
            hp_per_level=5.2,
            base_attack=7,
            atk_per_level=1.4,
            base_defense=2,
            def_per_level=0.3,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=13,
            init_per_level=0.6,
            skill_ids=["crippling_blow", "nimble_step"],
            party_type_ids=["ranger", "scout"],
            tags=["ranger", "skirmisher"],
            description="A pathfinder who knows the wilderness well.",
        )
    )
