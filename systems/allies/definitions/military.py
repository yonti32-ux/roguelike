"""
Military ally archetypes.

Soldiers, mercenaries, and professional fighters.
"""

from systems.allies import register_archetype
from systems.allies.types import AllyArchetype


def register_military_archetypes() -> None:
    """Register military-type ally archetypes."""
    
    # Mercenary - Professional fighter
    register_archetype(
        AllyArchetype(
            id="mercenary",
            name="Mercenary",
            role="Fighter",
            ai_profile="tactician",
            base_hp=38,
            hp_per_level=6,
            base_attack=8,
            atk_per_level=1.5,
            base_defense=3,
            def_per_level=0.5,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=12,
            init_per_level=0.5,
            skill_ids=["heavy_slam", "crippling_blow", "mark_target"],
            party_type_ids=["mercenary"],
            tags=["military", "mercenary"],
            description="A professional mercenary fighter.",
        )
    )
    
    # Adventurer - Skilled explorer
    register_archetype(
        AllyArchetype(
            id="adventurer",
            name="Adventurer",
            role="Fighter",
            ai_profile="tactician",
            base_hp=40,
            hp_per_level=6.5,
            base_attack=9,
            atk_per_level=1.6,
            base_defense=3,
            def_per_level=0.5,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=13,
            init_per_level=0.6,
            skill_ids=["heavy_slam", "crippling_blow", "mark_target"],
            party_type_ids=["adventurer"],
            tags=["military", "adventurer"],
            description="A fellow adventurer exploring the world.",
        )
    )
    
    # Veteran - Experienced fighter
    register_archetype(
        AllyArchetype(
            id="veteran",
            name="Veteran",
            role="Fighter",
            ai_profile="tactician",
            base_hp=42,
            hp_per_level=6.8,
            base_attack=8,
            atk_per_level=1.5,
            base_defense=4,
            def_per_level=0.6,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=12,
            init_per_level=0.5,
            skill_ids=["heavy_slam", "crippling_blow", "war_cry"],
            party_type_ids=["mercenary", "adventurer"],
            tags=["military", "veteran"],
            description="A battle-hardened veteran of many conflicts.",
        )
    )
    
    # Captain - Military leader
    register_archetype(
        AllyArchetype(
            id="captain",
            name="Captain",
            role="Elite Fighter",
            ai_profile="commander",
            base_hp=44,
            hp_per_level=7,
            base_attack=9,
            atk_per_level=1.6,
            base_defense=4,
            def_per_level=0.6,
            base_skill_power=1.1,
            skill_power_per_level=0.04,
            base_initiative=13,
            init_per_level=0.6,
            skill_ids=["heavy_slam", "war_cry", "mark_target"],
            party_type_ids=["knight", "mercenary"],
            tags=["military", "elite", "leader"],
            description="A military captain who leads by example.",
        )
    )
    
    # Soldier - Basic military unit
    register_archetype(
        AllyArchetype(
            id="soldier",
            name="Soldier",
            role="Fighter",
            ai_profile="brute",
            base_hp=36,
            hp_per_level=6,
            base_attack=7,
            atk_per_level=1.3,
            base_defense=3,
            def_per_level=0.5,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["heavy_slam", "guard"],
            party_type_ids=["guard", "mercenary"],
            tags=["military"],
            description="A disciplined soldier following orders.",
        )
    )
    
    # Champion - Elite fighter
    register_archetype(
        AllyArchetype(
            id="champion",
            name="Champion",
            role="Elite Fighter",
            ai_profile="tactician",
            base_hp=46,
            hp_per_level=7.5,
            base_attack=10,
            atk_per_level=1.7,
            base_defense=4,
            def_per_level=0.7,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=13,
            init_per_level=0.6,
            skill_ids=["heavy_slam", "crippling_blow", "war_cry", "mark_target"],
            party_type_ids=["knight", "adventurer"],
            tags=["military", "elite", "champion"],
            description="A legendary champion known for heroic deeds.",
        )
    )
