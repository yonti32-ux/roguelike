"""
Late game enemy archetypes (Tier 3, Difficulty 70-90+).

These are the powerful enemies that appear in the late floors of the dungeon.
"""

from ..types import EnemyArchetype
from ..registry import register_archetype


def register_late_game_archetypes() -> None:
    """Register all late game enemy archetypes."""
    
    # --- Tier 3: late floors / scary stuff --------------------------------

    register_archetype(
        EnemyArchetype(
            id="dread_knight",
            name="Dread Knight",
            role="Elite Brute",
            tier=3,  # Kept for backward compatibility
            ai_profile="tactician",  # Uses tactician AI for smart positioning and combos
            base_hp=40,
            hp_per_floor=3.0,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=26,
            xp_per_floor=3.0,
            skill_ids=[
                "heavy_slam",
                "war_cry",
            ],
            # New difficulty system
            difficulty_level=85,  # Late game elite enemy
            spawn_min_floor=5,
            spawn_max_floor=None,  # Can appear from floor 5 onwards
            spawn_weight=1.0,
            tags=["late_game", "elite", "brute", "undead"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="voidspawn_mauler",
            name="Voidspawn Mauler",
            role="Brute",
            tier=3,
            ai_profile="brute",
            base_hp=36,
            hp_per_floor=2.8,
            base_attack=10,
            atk_per_floor=1.4,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=24,
            xp_per_floor=2.8,
            skill_ids=[
                "feral_claws",
                "poison_strike",
            ],
            # New difficulty system
            difficulty_level=82,  # Late game enemy
            spawn_min_floor=5,
            spawn_max_floor=None,
            spawn_weight=1.0,
            tags=["late_game", "void", "brute", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="cultist_harbinger",
            name="Cultist Harbinger",
            role="Support",
            tier=3,
            ai_profile="caster",
            base_hp=30,
            hp_per_floor=2.4,
            base_attack=9,
            atk_per_floor=1.3,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=25,
            xp_per_floor=3.0,
            skill_ids=[
                "dark_hex",
                "crippling_blow",
            ],
            # New difficulty system
            difficulty_level=83,  # Late game support
            spawn_min_floor=5,
            spawn_max_floor=None,
            spawn_weight=0.9,  # Less common, support role
            tags=["late_game", "cultist", "support", "caster", "common"],
        )
    )

    # --- New Tier 3 Enemies ----------------------------------------------------

    register_archetype(
        EnemyArchetype(
            id="lich",
            name="Lich",
            role="Elite Support",
            tier=3,
            ai_profile="caster",
            base_hp=35,
            hp_per_floor=2.8,
            base_attack=10,
            atk_per_floor=1.4,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=28,
            xp_per_floor=3.2,
            skill_ids=[
                "life_drain",
                "dark_hex",
                "heal_ally",
                "regeneration",
            ],
            # New difficulty system
            difficulty_level=88,  # Very strong late game elite
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.7,  # Rare, elite enemy
            tags=["late_game", "elite", "undead", "support", "caster", "rare"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="dragonkin",
            name="Dragonkin",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=45,
            hp_per_floor=3.2,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=30,
            xp_per_floor=3.5,
            skill_ids=[
                "heavy_slam",
                "berserker_rage",
                "war_cry",
            ],
            # New difficulty system
            difficulty_level=87,  # Very strong late game elite
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.8,  # Rare, elite enemy
            tags=["late_game", "elite", "brute", "dragon", "rare"],
        )
    )

    # Lair unique: brutal champion
    register_archetype(
        EnemyArchetype(
            id="pit_champion",
            name="Pit Champion",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=50,
            hp_per_floor=3.2,
            base_attack=13,
            atk_per_floor=1.7,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=34,
            xp_per_floor=3.4,
            skill_ids=[
                "heavy_slam",
                "berserker_rage",
                "war_cry",
            ],
            # New difficulty system - unique room enemy
            difficulty_level=90,  # Very strong late game unique
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.3,  # Rare spawn (unique enemy)
            tags=["late_game", "elite", "brute", "unique", "lair"],
        )
    )

    # --- Late Game Additions (Difficulty 70-90) ---
    
    register_archetype(
        EnemyArchetype(
            id="death_knight",
            name="Death Knight",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=42,
            hp_per_floor=3.2,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=27,
            xp_per_floor=3.2,
            skill_ids=[
                "heavy_slam",
                "war_cry",
            ],
            difficulty_level=84,  # Late game elite
            spawn_min_floor=5,
            spawn_max_floor=None,
            spawn_weight=1.0,
            tags=["late_game", "elite", "undead", "brute", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="void_mage",
            name="Void Mage",
            role="Invoker",
            tier=3,
            ai_profile="controller",  # Uses controller AI for debuffs and control
            base_hp=32,
            hp_per_floor=2.6,
            base_attack=10,
            atk_per_floor=1.4,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=29,
            xp_per_floor=3.3,
            skill_ids=[
                "dark_hex",
                "crippling_blow",
            ],
            difficulty_level=86,  # Late game caster
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.9,
            tags=["late_game", "void", "invoker", "caster", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="behemoth",
            name="Behemoth",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=55,
            hp_per_floor=3.5,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=5,
            def_per_floor=0.9,
            base_xp=32,
            xp_per_floor=3.6,
            skill_ids=[
                "heavy_slam",
                "war_cry",
                "counter_attack",
            ],
            difficulty_level=89,  # Very tanky late game
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.7,
            tags=["late_game", "elite", "beast", "brute", "tank", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="shadow_lord",
            name="Shadow Lord",
            role="Elite Support",
            tier=3,
            ai_profile="support",  # Uses support AI for healing and buffing
            base_hp=38,
            hp_per_floor=3.0,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=31,
            xp_per_floor=3.4,
            skill_ids=[
                "dark_hex",
                "life_drain",
                "heal_ally",
                "regeneration",
            ],
            difficulty_level=88,  # Very strong late game support
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.6,
            tags=["late_game", "elite", "shadow", "support", "caster", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="frost_giant",
            name="Frost Giant",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=48,
            hp_per_floor=3.3,
            base_attack=13,
            atk_per_floor=1.7,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=33,
            xp_per_floor=3.7,
            skill_ids=[
                "heavy_slam",
                "war_cry",
                "berserker_rage",
            ],
            difficulty_level=91,  # Very strong late game
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.5,
            tags=["late_game", "elite", "giant", "brute", "ice", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="chaos_spawn",
            name="Chaos Spawn",
            role="Brute",
            tier=3,
            ai_profile="brute",
            base_hp=40,
            hp_per_floor=3.0,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=28,
            xp_per_floor=3.1,
            skill_ids=[
                "feral_claws",
                "poison_strike",
                "berserker_rage",
            ],
            difficulty_level=81,  # Late game chaos enemy
            spawn_min_floor=5,
            spawn_max_floor=None,
            spawn_weight=1.0,
            tags=["late_game", "void", "brute", "chaos", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="archmage",
            name="Archmage",
            role="Elite Invoker",
            tier=3,
            ai_profile="caster",
            base_hp=34,
            hp_per_floor=2.7,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=30,
            xp_per_floor=3.5,
            skill_ids=[
                "fireball",
                "dark_hex",
                "crippling_blow",
            ],
            difficulty_level=85,  # Late game elite caster
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.8,
            tags=["late_game", "elite", "invoker", "caster", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="bone_dragon",
            name="Bone Dragon",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=50,
            hp_per_floor=3.4,
            base_attack=14,
            atk_per_floor=1.8,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=35,
            xp_per_floor=4.0,
            skill_ids=[
                "heavy_slam",
                "feral_claws",
                "war_cry",
            ],
            difficulty_level=92,  # Very strong late game elite
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.4,
            tags=["late_game", "elite", "undead", "dragon", "brute", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="blood_fiend",
            name="Blood Fiend",
            role="Skirmisher",
            tier=3,
            ai_profile="skirmisher",
            base_hp=28,
            hp_per_floor=2.4,
            base_attack=10,
            atk_per_floor=1.4,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=26,
            xp_per_floor=3.0,
            skill_ids=[
                "life_drain",
                "poison_strike",
                "nimble_step",
            ],
            difficulty_level=83,  # Late game skirmisher
            spawn_min_floor=5,
            spawn_max_floor=None,
            spawn_weight=0.9,
            tags=["late_game", "demon", "skirmisher", "common"],
        )
    )
    
    # --- Additional Unique/Special Enemies ---
    
    register_archetype(
        EnemyArchetype(
            id="ancient_guardian",
            name="Ancient Guardian",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=46,
            hp_per_floor=3.3,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=5,
            def_per_floor=0.9,
            base_xp=31,
            xp_per_floor=3.5,
            skill_ids=[
                "heavy_slam",
                "counter_attack",
                "war_cry",
            ],
            difficulty_level=86,  # Late game elite
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.6,
            tags=["late_game", "elite", "construct", "brute", "tank", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="vampire_noble",
            name="Vampire Noble",
            role="Elite Support",
            tier=3,
            ai_profile="caster",
            base_hp=36,
            hp_per_floor=2.9,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=29,
            xp_per_floor=3.3,
            skill_ids=[
                "life_drain",
                "regeneration",
                "heal_ally",
            ],
            difficulty_level=84,  # Late game elite
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.7,
            tags=["late_game", "elite", "undead", "support", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="soul_reaper",
            name="Soul Reaper",
            role="Elite Invoker",
            tier=3,
            ai_profile="caster",
            base_hp=33,
            hp_per_floor=2.7,
            base_attack=10,
            atk_per_floor=1.4,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=30,
            xp_per_floor=3.4,
            skill_ids=[
                "life_drain",
                "dark_hex",
                "crippling_blow",
            ],
            difficulty_level=87,  # Late game elite caster
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.7,
            tags=["late_game", "elite", "undead", "invoker", "caster", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="iron_golem",
            name="Iron Golem",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=52,
            hp_per_floor=3.4,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=6,
            def_per_floor=1.0,
            base_xp=33,
            xp_per_floor=3.6,
            skill_ids=[
                "heavy_slam",
                "counter_attack",
                "war_cry",
            ],
            difficulty_level=90,  # Very tanky late game
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.5,
            tags=["late_game", "elite", "construct", "brute", "tank", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="abyssal_horror",
            name="Abyssal Horror",
            role="Elite Invoker",
            tier=3,
            ai_profile="caster",
            base_hp=39,
            hp_per_floor=3.1,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=32,
            xp_per_floor=3.7,
            skill_ids=[
                "dark_hex",
                "crippling_blow",
                "fear_scream",
            ],
            difficulty_level=93,  # Very strong late game
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.4,
            tags=["late_game", "elite", "void", "invoker", "caster", "rare"],
        )
    )
    
    # --- New Late-Game Enemies with Advanced AI Profiles -------------------
    
    register_archetype(
        EnemyArchetype(
            id="death_knight",
            name="Death Knight",
            role="Elite Brute",
            tier=3,
            ai_profile="tactician",  # Smart positioning and combos
            base_hp=44,
            hp_per_floor=3.3,
            base_attack=13,
            atk_per_floor=1.7,
            base_defense=5,
            def_per_floor=0.9,
            base_xp=30,
            xp_per_floor=3.5,
            skill_ids=[
                "mark_target",
                "heavy_slam",
                "war_cry",
            ],
            difficulty_level=87,  # Strong late-game tactician
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.8,
            tags=["late_game", "elite", "undead", "brute", "tactician", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="void_assassin",
            name="Void Assassin",
            role="Skirmisher",
            tier=3,
            ai_profile="assassin",  # Targets isolated enemies
            base_hp=24,
            hp_per_floor=2.2,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=1,
            def_per_floor=0.4,
            base_xp=28,
            xp_per_floor=3.2,
            skill_ids=[
                "crippling_blow",
                "poison_strike",
                "life_drain",
            ],
            difficulty_level=85,  # Late-game assassin
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.7,
            tags=["late_game", "void", "skirmisher", "assassin", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="dread_guardian",
            name="Dread Guardian",
            role="Brute",
            tier=3,
            ai_profile="defender",  # Protects allies
            base_hp=48,
            hp_per_floor=3.4,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=6,
            def_per_floor=1.0,
            base_xp=29,
            xp_per_floor=3.3,
            skill_ids=[
                "guard",
                "war_cry",
                "heavy_slam",
            ],
            difficulty_level=88,  # Very tanky late-game defender
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.6,
            tags=["late_game", "elite", "undead", "brute", "tank", "defender", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="archlich",
            name="Archlich",
            role="Elite Support",
            tier=3,
            ai_profile="commander",  # Coordinates undead hordes
            base_hp=40,
            hp_per_floor=3.2,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=33,
            xp_per_floor=3.8,
            skill_ids=[
                "dark_hex",
                "mark_target",
                "war_cry",
                "heal_ally",
            ],
            difficulty_level=91,  # Very strong late-game commander
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.4,
            tags=["late_game", "elite", "undead", "support", "commander", "unique"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="chaos_lord",
            name="Chaos Lord",
            role="Elite Brute",
            tier=3,
            ai_profile="berserker",  # Aggressive and reckless
            base_hp=46,
            hp_per_floor=3.3,
            base_attack=14,
            atk_per_floor=1.8,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=31,
            xp_per_floor=3.6,
            skill_ids=[
                "berserker_rage",
                "heavy_slam",
                "feral_claws",
            ],
            difficulty_level=90,  # Very aggressive late-game
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.5,
            tags=["late_game", "elite", "demon", "brute", "berserker", "rare"],
        )
    )
    
    # --- Additional Late-Game Enemies ---------------------------------------
    
    register_archetype(
        EnemyArchetype(
            id="dragon_knight",
            name="Dragon Knight",
            role="Elite Brute",
            tier=3,
            ai_profile="tactician",  # Smart positioning and combos
            base_hp=50,
            hp_per_floor=3.6,
            base_attack=15,
            atk_per_floor=1.9,
            base_defense=6,
            def_per_floor=1.0,
            base_xp=34,
            xp_per_floor=3.9,
            skill_ids=[
                "mark_target",
                "heavy_slam",
                "war_cry",
                "feral_claws",
            ],
            difficulty_level=92,
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.6,
            tags=["late_game", "elite", "dragon", "brute", "tactician", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="shadow_weaver",
            name="Shadow Weaver",
            role="Elite Invoker",
            tier=3,
            ai_profile="controller",  # Debuffs and crowd control
            base_hp=35,
            hp_per_floor=2.8,
            base_attack=13,
            atk_per_floor=1.7,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=32,
            xp_per_floor=3.7,
            skill_ids=[
                "dark_hex",
                "mark_target",
                "fear_scream",
                "life_drain",
            ],
            difficulty_level=89,
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.7,
            tags=["late_game", "elite", "shadow", "invoker", "controller", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="frost_giant_berserker",
            name="Frost Giant Berserker",
            role="Elite Brute",
            tier=3,
            ai_profile="berserker",  # Aggressive when low HP
            base_hp=52,
            hp_per_floor=3.7,
            base_attack=14,
            atk_per_floor=1.8,
            base_defense=5,
            def_per_floor=0.9,
            base_xp=33,
            xp_per_floor=3.8,
            skill_ids=[
                "berserker_rage",
                "heavy_slam",
                "war_cry",
            ],
            difficulty_level=91,
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.6,
            tags=["late_game", "elite", "giant", "brute", "berserker", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="void_guardian",
            name="Void Guardian",
            role="Elite Brute",
            tier=3,
            ai_profile="defender",  # Protects allies
            base_hp=54,
            hp_per_floor=3.8,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=7,
            def_per_floor=1.1,
            base_xp=31,
            xp_per_floor=3.6,
            skill_ids=[
                "guard",
                "war_cry",
                "heavy_slam",
                "counter_attack",
            ],
            difficulty_level=90,
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.5,
            tags=["late_game", "elite", "void", "brute", "tank", "defender", "rare"],
            resistances={"magic": 0.3},  # 70% magic resistance
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="demon_lord",
            name="Demon Lord",
            role="Elite Brute",
            tier=3,
            ai_profile="commander",  # Coordinates demon hordes
            base_hp=48,
            hp_per_floor=3.5,
            base_attack=16,
            atk_per_floor=2.0,
            base_defense=5,
            def_per_floor=0.9,
            base_xp=35,
            xp_per_floor=4.0,
            skill_ids=[
                "war_cry",
                "mark_target",
                "heavy_slam",
                "berserker_rage",
            ],
            difficulty_level=93,
            spawn_min_floor=8,
            spawn_max_floor=None,
            spawn_weight=0.3,
            tags=["late_game", "elite", "demon", "brute", "commander", "unique"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="lich_king",
            name="Lich King",
            role="Elite Support",
            tier=3,
            ai_profile="commander",  # Coordinates undead armies
            base_hp=42,
            hp_per_floor=3.3,
            base_attack=14,
            atk_per_floor=1.8,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=36,
            xp_per_floor=4.1,
            skill_ids=[
                "dark_hex",
                "mark_target",
                "war_cry",
                "heal_ally",
                "fear_scream",
            ],
            difficulty_level=94,
            spawn_min_floor=8,
            spawn_max_floor=None,
            spawn_weight=0.2,
            tags=["late_game", "elite", "undead", "support", "commander", "unique"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="blood_fiend",
            name="Blood Fiend",
            role="Skirmisher",
            tier=3,
            ai_profile="assassin",  # Targets isolated enemies
            base_hp=28,
            hp_per_floor=2.4,
            base_attack=13,
            atk_per_floor=1.7,
            base_defense=2,
            def_per_floor=0.5,
            base_xp=30,
            xp_per_floor=3.5,
            skill_ids=[
                "crippling_blow",
                "life_drain",
                "poison_strike",
            ],
            difficulty_level=86,
            spawn_min_floor=6,
            spawn_max_floor=None,
            spawn_weight=0.8,
            tags=["late_game", "demon", "skirmisher", "assassin", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="ancient_dragon",
            name="Ancient Dragon",
            role="Elite Brute",
            tier=3,
            ai_profile="tactician",  # Smart positioning and combos
            base_hp=60,
            hp_per_floor=4.0,
            base_attack=17,
            atk_per_floor=2.1,
            base_defense=7,
            def_per_floor=1.2,
            base_xp=38,
            xp_per_floor=4.3,
            skill_ids=[
                "mark_target",
                "heavy_slam",
                "war_cry",
                "feral_claws",
                "fireball",
            ],
            difficulty_level=95,
            spawn_min_floor=9,
            spawn_max_floor=None,
            spawn_weight=0.2,
            tags=["late_game", "elite", "dragon", "brute", "tactician", "unique"],
            resistances={"fire": 0.0, "physical": 0.5},  # Fire immune, 50% physical resistance
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="soul_reaper",
            name="Soul Reaper",
            role="Elite Invoker",
            tier=3,
            ai_profile="controller",  # Debuffs and crowd control
            base_hp=36,
            hp_per_floor=2.9,
            base_attack=13,
            atk_per_floor=1.7,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=34,
            xp_per_floor=3.9,
            skill_ids=[
                "dark_hex",
                "mark_target",
                "fear_scream",
                "life_drain",
            ],
            difficulty_level=92,
            spawn_min_floor=7,
            spawn_max_floor=None,
            spawn_weight=0.6,
            tags=["late_game", "elite", "undead", "invoker", "controller", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="void_titan",
            name="Void Titan",
            role="Elite Brute",
            tier=3,
            ai_profile="defender",  # Protects allies
            base_hp=58,
            hp_per_floor=4.1,
            base_attack=15,
            atk_per_floor=1.9,
            base_defense=8,
            def_per_floor=1.3,
            base_xp=37,
            xp_per_floor=4.2,
            skill_ids=[
                "guard",
                "war_cry",
                "heavy_slam",
                "counter_attack",
            ],
            difficulty_level=94,
            spawn_min_floor=8,
            spawn_max_floor=None,
            spawn_weight=0.3,
            tags=["late_game", "elite", "void", "brute", "tank", "defender", "unique"],
            resistances={"magic": 0.2, "physical": 0.4},  # Very resistant
        )
    )