"""
Merchant ally archetypes.

Merchants, traders, and their guards.
"""

from systems.allies import register_archetype
from systems.allies.types import AllyArchetype


def register_merchant_archetypes() -> None:
    """Register merchant-type ally archetypes."""
    
    # Merchant Guard - Protects caravans
    register_archetype(
        AllyArchetype(
            id="merchant_guard",
            name="Merchant Guard",
            role="Guardian",
            ai_profile="defender",
            base_hp=32,
            hp_per_level=5.5,
            base_attack=6,
            atk_per_level=1.2,
            base_defense=3,
            def_per_level=0.4,
            base_skill_power=1.0,
            skill_power_per_level=0.02,
            base_initiative=10,
            init_per_level=0.3,
            skill_ids=["guard", "heavy_slam"],
            party_type_ids=["merchant", "trader"],
            tags=["guardian", "merchant"],
            description="A guard protecting a merchant caravan.",
        )
    )
    
    # Villager - Basic civilian ally
    register_archetype(
        AllyArchetype(
            id="villager",
            name="Villager",
            role="Civilian",
            ai_profile="brute",
            base_hp=20,
            hp_per_level=4,
            base_attack=4,
            atk_per_level=0.8,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.0,
            skill_power_per_level=0.01,
            base_initiative=9,
            init_per_level=0.2,
            skill_ids=["guard"],
            party_type_ids=["villager", "pilgrim"],
            tags=["civilian"],
            description="A brave villager fighting alongside you.",
        )
    )
    
    # Trader - Merchant variant
    register_archetype(
        AllyArchetype(
            id="trader",
            name="Trader",
            role="Civilian",
            ai_profile="brute",
            base_hp=22,
            hp_per_level=4.2,
            base_attack=5,
            atk_per_level=1.0,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.0,
            skill_power_per_level=0.01,
            base_initiative=10,
            init_per_level=0.3,
            skill_ids=["guard"],
            party_type_ids=["merchant", "trader"],
            tags=["civilian", "merchant"],
            description="A trader who knows how to defend their goods.",
        )
    )
    
    # Pilgrim - Religious traveler
    register_archetype(
        AllyArchetype(
            id="pilgrim",
            name="Pilgrim",
            role="Civilian",
            ai_profile="brute",
            base_hp=21,
            hp_per_level=4.1,
            base_attack=4,
            atk_per_level=0.9,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.0,
            skill_power_per_level=0.01,
            base_initiative=9,
            init_per_level=0.2,
            skill_ids=["guard"],
            party_type_ids=["pilgrim"],
            tags=["civilian", "religious"],
            description="A pilgrim on a holy journey.",
        )
    )
    
    # Farmer - Civilian fighter
    register_archetype(
        AllyArchetype(
            id="farmer",
            name="Farmer",
            role="Civilian",
            ai_profile="brute",
            base_hp=23,
            hp_per_level=4.3,
            base_attack=5,
            atk_per_level=0.9,
            base_defense=1,
            def_per_level=0.2,
            base_skill_power=1.0,
            skill_power_per_level=0.01,
            base_initiative=9,
            init_per_level=0.2,
            skill_ids=["guard", "heavy_slam"],
            party_type_ids=["villager"],
            tags=["civilian"],
            description="A farmer who fights to protect their home.",
        )
    )
