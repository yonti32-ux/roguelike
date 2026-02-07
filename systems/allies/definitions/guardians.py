"""
Guardian ally archetypes.

Guards, knights, and defensive allies that protect the player.
"""

from systems.allies import register_archetype
from systems.allies.types import AllyArchetype


def register_guardian_archetypes() -> None:
    """Register guardian-type ally archetypes."""
    
    # Town Guard - Basic defensive ally
    register_archetype(
        AllyArchetype(
            id="town_guard",
            name="Town Guard",
            role="Guardian",
            ai_profile="defender",
            base_hp=35,
            hp_per_level=6,
            base_attack=6,
            atk_per_level=1.2,
            base_defense=3,
            def_per_level=0.5,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["guard", "heavy_slam"],
            party_type_ids=["guard"],
            tags=["guardian", "military"],
            description="A town guard sworn to protect the innocent.",
        )
    )
    
    # Knight - Elite defensive ally
    register_archetype(
        AllyArchetype(
            id="knight",
            name="Knight",
            role="Elite Guardian",
            ai_profile="defender",
            base_hp=45,
            hp_per_level=7,
            base_attack=8,
            atk_per_level=1.5,
            base_defense=5,
            def_per_level=0.7,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=12,
            init_per_level=0.5,
            skill_ids=["guard", "heavy_slam", "war_cry"],
            party_type_ids=["knight"],
            tags=["guardian", "military", "elite"],
            description="An elite knight in shining armor.",
        )
    )
    
    # Noble Guard - Protective escort
    register_archetype(
        AllyArchetype(
            id="noble_guard",
            name="Noble Guard",
            role="Guardian",
            ai_profile="defender",
            base_hp=40,
            hp_per_level=6.5,
            base_attack=7,
            atk_per_level=1.3,
            base_defense=4,
            def_per_level=0.6,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["guard", "heavy_slam"],
            party_type_ids=["noble"],
            tags=["guardian", "military"],
            description="A guard protecting a noble's entourage.",
        )
    )
    
    # Shield Bearer - Heavy defensive specialist
    register_archetype(
        AllyArchetype(
            id="shield_bearer",
            name="Shield Bearer",
            role="Guardian",
            ai_profile="defender",
            base_hp=42,
            hp_per_level=7,
            base_attack=6,
            atk_per_level=1.1,
            base_defense=6,
            def_per_level=0.8,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=10,
            init_per_level=0.3,
            skill_ids=["guard", "heavy_slam"],
            party_type_ids=["guard", "knight"],
            tags=["guardian", "military", "tank"],
            description="A heavily armored warrior with a massive shield.",
        )
    )
    
    # Sentinel - Elite watchman
    register_archetype(
        AllyArchetype(
            id="sentinel",
            name="Sentinel",
            role="Elite Guardian",
            ai_profile="defender",
            base_hp=38,
            hp_per_level=6.5,
            base_attack=8,
            atk_per_level=1.4,
            base_defense=5,
            def_per_level=0.7,
            base_skill_power=1.0,
            skill_power_per_level=0.03,
            base_initiative=12,
            init_per_level=0.5,
            skill_ids=["guard", "heavy_slam", "mark_target"],
            party_type_ids=["guard", "knight"],
            tags=["guardian", "military", "elite"],
            description="An elite sentinel who stands watch over important locations.",
        )
    )
    
    # Watchman - Light guard
    register_archetype(
        AllyArchetype(
            id="watchman",
            name="Watchman",
            role="Guardian",
            ai_profile="defender",
            base_hp=30,
            hp_per_level=5.5,
            base_attack=6,
            atk_per_level=1.2,
            base_defense=2,
            def_per_level=0.4,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=11,
            init_per_level=0.4,
            skill_ids=["guard"],
            party_type_ids=["guard"],
            tags=["guardian", "military"],
            description="A watchman who patrols the streets.",
        )
    )
