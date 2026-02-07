"""
Overworld party archetypes.

These are humanoid/civilian archetypes used for overworld parties like guards, rangers, merchants, etc.
They can change alignment based on faction relations.
"""

from ..types import EnemyArchetype
from ..registry import register_archetype


def register_overworld_party_archetypes() -> None:
    """Register all overworld party archetypes."""
    
    # Humanoid/Civilian Archetypes for Overworld Parties
    register_archetype(
        EnemyArchetype(
            id="town_guard",
            name="Town Guard",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=20,
            hp_per_floor=1.8,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=2,
            def_per_floor=0.4,
            base_xp=15,
            xp_per_floor=2.0,
            skill_ids=[
                "heavy_slam",
                "guard",  # Defensive stance
                "counter_attack",  # Retaliate when attacked
            ],
            difficulty_level=42,  # Mid game guard
            spawn_min_floor=2,
            spawn_max_floor=6,
            spawn_weight=1.0,
            tags=["mid_game", "human", "guard", "brute", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="ranger",
            name="Ranger",
            role="Skirmisher",
            tier=2,
            ai_profile="skirmisher",
            base_hp=18,
            hp_per_floor=1.7,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=16,
            xp_per_floor=2.0,
            skill_ids=[
                "poison_strike",  # Poisoned arrows
                "nimble_step",  # Quick movement
            ],
            difficulty_level=44,  # Mid game ranger
            spawn_min_floor=2,
            spawn_max_floor=6,
            spawn_weight=1.0,
            tags=["mid_game", "human", "ranger", "skirmisher", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="merchant_guard",
            name="Merchant Guard",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=15,
            hp_per_floor=1.5,
            base_attack=6,
            atk_per_floor=0.9,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=10,
            xp_per_floor=1.5,
            skill_ids=[
                "poison_strike",  # Dirty fighting
                "guard",  # Protect the caravan
            ],
            difficulty_level=25,  # Early-mid game merchant guard
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=1.0,
            tags=["early_game", "human", "merchant", "skirmisher", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="villager",
            name="Villager",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=10,
            hp_per_floor=1.0,
            base_attack=4,
            atk_per_floor=0.7,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=5,
            xp_per_floor=0.8,
            skill_ids=[],  # No special skills - just basic attacks
            difficulty_level=12,  # Very weak early game
            spawn_min_floor=1,
            spawn_max_floor=3,
            spawn_weight=1.0,
            tags=["early_game", "human", "villager", "weak", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="noble_guard",
            name="Noble Guard",
            role="Elite Brute",
            tier=2,
            ai_profile="brute",
            base_hp=25,
            hp_per_floor=2.2,
            base_attack=9,
            atk_per_floor=1.2,
            base_defense=3,
            def_per_floor=0.5,
            base_xp=20,
            xp_per_floor=2.5,
            skill_ids=[
                "heavy_slam",
                "guard",  # Elite defensive training
                "counter_attack",  # Well-trained retaliation
                "war_cry",  # Rallying cry
            ],
            difficulty_level=52,  # Mid-late game noble guard
            spawn_min_floor=3,
            spawn_max_floor=7,
            spawn_weight=0.8,
            tags=["mid_game", "human", "noble", "elite", "brute", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="scout",
            name="Scout",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=13,
            hp_per_floor=1.2,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=8,
            xp_per_floor=1.2,
            skill_ids=[
                "nimble_step",  # Quick and agile
                "poison_strike",  # Traps and tricks
            ],
            difficulty_level=20,  # Early game scout
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=1.0,
            tags=["early_game", "human", "scout", "skirmisher", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="pilgrim",
            name="Pilgrim",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=9,
            hp_per_floor=0.9,
            base_attack=3,
            atk_per_floor=0.6,
            base_defense=0,
            def_per_floor=0.1,
            base_xp=4,
            xp_per_floor=0.7,
            skill_ids=[],  # No combat skills - peaceful travelers
            difficulty_level=10,  # Very weak early game
            spawn_min_floor=1,
            spawn_max_floor=2,
            spawn_weight=1.0,
            tags=["early_game", "human", "pilgrim", "weak", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="corrupted_priest",
            name="Corrupted Priest",
            role="Support",
            tier=2,
            ai_profile="caster",
            base_hp=21,
            hp_per_floor=2.0,
            base_attack=6,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=19,
            xp_per_floor=2.3,
            skill_ids=[
                "dark_hex",
                "heal_ally",
                "life_drain",
            ],
            difficulty_level=55,  # Mid game support
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "cultist", "support", "caster", "common"],
        )
    )
