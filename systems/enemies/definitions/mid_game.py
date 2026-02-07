"""
Mid game enemy archetypes (Tier 2, Difficulty 40-69).

These are the enemies that appear in the middle floors of the dungeon.
"""

from ..types import EnemyArchetype
from ..registry import register_archetype


def register_mid_game_archetypes() -> None:
    """Register all mid game enemy archetypes."""
    
    # --- Tier 2: midgame threats ------------------------------------------

    register_archetype(
        EnemyArchetype(
            id="ghoul_ripper",
            name="Ghoul Ripper",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=22,
            hp_per_floor=2.0,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.4,
            base_xp=14,
            xp_per_floor=1.8,
            skill_ids=[
                "feral_claws",     # bleeding DOT
            ],
            # New difficulty system
            difficulty_level=48,  # Mid-game enemy
            spawn_min_floor=3,
            spawn_max_floor=7,
            spawn_weight=1.2,
            tags=["mid_game", "undead", "brute", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="orc_raider",
            name="Orc Raider",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=26,
            hp_per_floor=2.2,
            base_attack=8,
            atk_per_floor=1.2,
            base_defense=2,
            def_per_floor=0.5,
            base_xp=16,
            xp_per_floor=2.0,
            skill_ids=[
                "heavy_slam",
            ],
            # New difficulty system
            difficulty_level=52,  # Stronger mid-game enemy
            spawn_min_floor=3,
            spawn_max_floor=8,
            spawn_weight=1.0,
            tags=["mid_game", "orc", "brute", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="dark_adept",
            name="Dark Adept",
            role="Invoker",
            tier=2,
            ai_profile="caster",
            base_hp=18,
            hp_per_floor=1.8,
            base_attack=6,
            atk_per_floor=1.1,
            base_defense=1,
            def_per_floor=0.4,
            base_xp=18,
            xp_per_floor=2.2,
            skill_ids=[
                "dark_hex",
                "crippling_blow",
            ],
            # New difficulty system
            difficulty_level=55,  # Higher XP = harder
            spawn_min_floor=3,
            spawn_max_floor=7,
            spawn_weight=0.9,  # Less common, prefers event rooms
            tags=["mid_game", "cultist", "invoker", "caster", "common"],
        )
    )

    # --- New Tier 2 Enemies ----------------------------------------------------

    register_archetype(
        EnemyArchetype(
            id="necromancer",
            name="Necromancer",
            role="Support",
            tier=2,
            ai_profile="caster",
            base_hp=20,
            hp_per_floor=1.9,
            base_attack=6,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=17,
            xp_per_floor=2.1,
            skill_ids=[
                "dark_hex",
                "heal_ally",
                "life_drain",
            ],
            # New difficulty system
            difficulty_level=50,  # Mid-game support
            spawn_min_floor=3,
            spawn_max_floor=8,
            spawn_weight=0.8,  # Less common, support role
            tags=["mid_game", "undead", "support", "caster", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="shadow_stalker",
            name="Shadow Stalker",
            role="Skirmisher",
            tier=2,
            ai_profile="skirmisher",
            base_hp=16,
            hp_per_floor=1.6,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=0,
            def_per_floor=0.3,
            base_xp=16,
            xp_per_floor=2.0,
            skill_ids=[
                "mark_target",
                "poison_strike",
                "nimble_step",
            ],
            # New difficulty system
            difficulty_level=53,  # High damage skirmisher
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=1.0,
            tags=["mid_game", "shadow", "skirmisher", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="stone_golem",
            name="Stone Golem",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=32,
            hp_per_floor=2.5,
            base_attack=6,
            atk_per_floor=0.9,
            base_defense=4,
            def_per_floor=0.6,
            base_xp=18,
            xp_per_floor=2.2,
            skill_ids=[
                "heavy_slam",
                "counter_attack",
            ],
            # New difficulty system
            difficulty_level=58,  # Tanky mid-game enemy
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.9,  # Less common, tanky
            tags=["mid_game", "construct", "brute", "tank", "common"],
            # Unique mechanics & resistances
            unique_mechanics=[],
            resistances={"physical": 0.3},  # 70% physical resistance (stone body)
        )
    )

    register_archetype(
        EnemyArchetype(
            id="banshee",
            name="Banshee",
            role="Invoker",
            tier=2,
            ai_profile="caster",
            base_hp=19,
            hp_per_floor=1.8,
            base_attack=7,
            atk_per_floor=1.2,
            base_defense=0,
            def_per_floor=0.3,
            base_xp=19,
            xp_per_floor=2.3,
            skill_ids=[
                "fear_scream",
                "dark_hex",
                "berserker_rage",  # Enrages when low HP
            ],
            # New difficulty system
            difficulty_level=57,  # Strong mid-game caster
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,  # Less common, prefers event rooms
            tags=["mid_game", "undead", "invoker", "caster", "common"],
        )
    )

    # --- Room-themed unique enemies (rare spawns) ------------------------------

    # Graveyard unique: tougher undead guardian
    register_archetype(
        EnemyArchetype(
            id="grave_warden",
            name="Grave Warden",
            role="Elite Support",
            tier=2,  # Kept for backward compatibility
            ai_profile="caster",
            base_hp=32,
            hp_per_floor=2.2,
            base_attack=8,
            atk_per_floor=1.2,
            base_defense=3,
            def_per_floor=0.6,
            base_xp=26,
            xp_per_floor=2.6,
            skill_ids=[
                "dark_hex",
                "fear_scream",
                "regeneration",
            ],
            # New difficulty system - unique room enemy
            difficulty_level=60,  # Mid-late game unique
            spawn_min_floor=3,
            spawn_max_floor=8,  # Spawns in mid-game range
            spawn_weight=0.3,  # Rare spawn (unique enemy)
            tags=["mid_game", "late_game", "elite", "undead", "unique", "graveyard"],
        )
    )

    # Sanctum unique: defensive guardian
    register_archetype(
        EnemyArchetype(
            id="sanctum_guardian",
            name="Sanctum Guardian",
            role="Elite Brute",
            tier=2,
            ai_profile="brute",
            base_hp=38,
            hp_per_floor=2.5,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=4,
            def_per_floor=0.7,
            base_xp=24,
            xp_per_floor=2.4,
            skill_ids=[
                "heavy_slam",
                "counter_attack",
                "war_cry",
            ],
            # New difficulty system - unique room enemy
            difficulty_level=62,  # Mid-late game unique
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.3,  # Rare spawn (unique enemy)
            tags=["mid_game", "late_game", "elite", "holy", "unique", "sanctum"],
        )
    )

    # Treasure unique: mimic-style boss
    register_archetype(
        EnemyArchetype(
            id="hoard_mimic",
            name="Hoard Mimic",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=36,
            hp_per_floor=2.3,
            base_attack=9,
            atk_per_floor=1.2,
            base_defense=3,
            def_per_floor=0.5,
            base_xp=28,
            xp_per_floor=2.8,
            skill_ids=[
                "heavy_slam",
                "feral_claws",
            ],
            # New difficulty system - unique room enemy
            difficulty_level=65,  # Mid-late game unique
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.3,  # Rare spawn (unique enemy)
            tags=["mid_game", "late_game", "brute", "unique", "treasure"],
        )
    )

    # Library unique: arcane golem
    register_archetype(
        EnemyArchetype(
            id="arcane_golem",
            name="Arcane Golem",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=28,
            hp_per_floor=2.2,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=5,
            def_per_floor=0.7,
            base_xp=22,
            xp_per_floor=2.5,
            skill_ids=[
                "heavy_slam",
                "magic_shield",
            ],
            difficulty_level=60,  # Mid-late game unique
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.3,  # Rare spawn (unique enemy)
            tags=["mid_game", "late_game", "construct", "brute", "tank", "unique", "library"],
            # Unique mechanics & resistances
            unique_mechanics=[],
            resistances={"magic": 0.3},  # High magic resistance (arcane construct)
        )
    )

    # Armory unique: animated armor
    register_archetype(
        EnemyArchetype(
            id="animated_armor",
            name="Animated Armor",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=26,
            hp_per_floor=2.0,
            base_attack=6,
            atk_per_floor=0.9,
            base_defense=6,
            def_per_floor=0.8,
            base_xp=20,
            xp_per_floor=2.3,
            skill_ids=[
                "heavy_slam",
                "counter_attack",
            ],
            difficulty_level=59,  # Mid-late game unique
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.3,  # Rare spawn (unique enemy)
            tags=["mid_game", "late_game", "construct", "brute", "tank", "unique", "armory"],
            # Unique mechanics & resistances
            unique_mechanics=[],
            resistances={"physical": 0.4},  # High physical resistance (armor)
        )
    )

    # --- Mid Game Additions (Difficulty 40-60) ---
    
    register_archetype(
        EnemyArchetype(
            id="wraith",
            name="Wraith",
            role="Skirmisher",
            tier=2,
            ai_profile="skirmisher",
            base_hp=15,
            hp_per_floor=1.5,
            base_attack=8,
            atk_per_floor=1.0,
            base_defense=0,
            def_per_floor=0.3,
            base_xp=17,
            xp_per_floor=2.0,
            skill_ids=[
                "life_drain",
                "nimble_step",
            ],
            difficulty_level=49,  # Mid game skirmisher
            spawn_min_floor=3,
            spawn_max_floor=7,
            spawn_weight=1.0,
            tags=["mid_game", "undead", "skirmisher", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="troll_berserker",
            name="Troll Berserker",
            role="Brute",
            tier=2,
            ai_profile="berserker",  # Uses berserker AI for aggressive low-HP behavior
            base_hp=30,
            hp_per_floor=2.8,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.4,
            base_xp=19,
            xp_per_floor=2.3,
            skill_ids=[
                "regeneration",
                "berserker_rage",
                "heavy_slam",
            ],
            difficulty_level=56,  # Tanky mid game
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.9,
            tags=["mid_game", "beast", "brute", "tank", "common"],
            # Unique mechanics & resistances
            unique_mechanics=["regeneration"],  # Heals each turn
            resistances={},
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="fire_elemental",
            name="Fire Elemental",
            role="Invoker",
            tier=2,
            ai_profile="caster",
            base_hp=20,
            hp_per_floor=1.9,
            base_attack=7,
            atk_per_floor=1.2,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=20,
            xp_per_floor=2.4,
            skill_ids=[
                "fireball",
            ],
            difficulty_level=54,  # Mid game caster
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "elemental", "invoker", "caster", "fire", "common"],
            # Unique mechanics & resistances
            unique_mechanics=[],
            resistances={"fire": 0.0},  # Immune to fire
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="mind_flayer",
            name="Mind Flayer",
            role="Support",
            tier=2,
            ai_profile="controller",  # Uses controller AI for debuffs and crowd control
            base_hp=19,
            hp_per_floor=1.8,
            base_attack=6,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=21,
            xp_per_floor=2.5,
            skill_ids=[
                "dark_hex",
                "crippling_blow",
            ],
            difficulty_level=58,  # Strong mid game support
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.7,
            tags=["mid_game", "aberration", "support", "caster", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="ice_wraith",
            name="Ice Wraith",
            role="Invoker",
            tier=2,
            ai_profile="caster",
            base_hp=18,
            hp_per_floor=1.7,
            base_attack=6,
            atk_per_floor=1.1,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=18,
            xp_per_floor=2.2,
            skill_ids=[
                "dark_hex",
            ],
            difficulty_level=51,  # Mid game elemental
            spawn_min_floor=3,
            spawn_max_floor=7,
            spawn_weight=0.9,
            tags=["mid_game", "undead", "invoker", "caster", "ice", "common"],
            # Unique mechanics & resistances
            unique_mechanics=[],
            resistances={"ice": 0.0, "fire": 1.5},  # Immune to ice, weak to fire
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="dire_wolf",
            name="Dire Wolf",
            role="Skirmisher",
            tier=2,
            ai_profile="skirmisher",
            base_hp=17,
            hp_per_floor=1.6,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=0,
            def_per_floor=0.3,
            base_xp=16,
            xp_per_floor=2.0,
            skill_ids=[
                "feral_claws",
                "nimble_step",
            ],
            difficulty_level=47,  # Mid game beast
            spawn_min_floor=3,
            spawn_max_floor=7,
            spawn_weight=1.1,
            tags=["mid_game", "beast", "skirmisher", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="bear",
            name="Bear",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=22,
            hp_per_floor=2.0,
            base_attack=9,
            atk_per_floor=1.2,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=18,
            xp_per_floor=2.2,
            skill_ids=[
                "heavy_slam",
                "feral_claws",
            ],
            difficulty_level=45,  # Mid game beast, strong brute
            spawn_min_floor=2,
            spawn_max_floor=6,
            spawn_weight=1.0,
            tags=["mid_game", "beast", "brute", "common"],
        )
    )

    # Additional mid-game enemies
    register_archetype(
        EnemyArchetype(
            id="plague_bearer",
            name="Plague Bearer",
            role="Support",
            tier=2,
            ai_profile="caster",
            base_hp=22,
            hp_per_floor=2.1,
            base_attack=7,
            atk_per_floor=1.1,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=20,
            xp_per_floor=2.4,
            skill_ids=[
                "disease_strike",
                "dark_hex",
            ],
            difficulty_level=59,  # Strong mid-late game support
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "late_game", "undead", "support", "caster", "disease", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="storm_elemental",
            name="Storm Elemental",
            role="Invoker",
            tier=2,
            ai_profile="caster",
            base_hp=19,
            hp_per_floor=1.8,
            base_attack=7,
            atk_per_floor=1.2,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=19,
            xp_per_floor=2.3,
            skill_ids=[
                "dark_hex",
            ],
            difficulty_level=53,  # Mid game elemental
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "elemental", "invoker", "caster", "lightning", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="cave_troll",
            name="Cave Troll",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=28,
            hp_per_floor=2.6,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=2,
            def_per_floor=0.5,
            base_xp=18,
            xp_per_floor=2.2,
            skill_ids=[
                "heavy_slam",
                "regeneration",
            ],
            difficulty_level=50,  # Mid game tank
            spawn_min_floor=3,
            spawn_max_floor=7,
            spawn_weight=1.0,
            tags=["mid_game", "beast", "brute", "tank", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="dark_ritualist",
            name="Dark Ritualist",
            role="Support",
            tier=2,
            ai_profile="caster",
            base_hp=20,
            hp_per_floor=1.9,
            base_attack=6,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=20,
            xp_per_floor=2.4,
            skill_ids=[
                "dark_hex",
                "heal_ally",
                "buff_ally",
            ],
            difficulty_level=56,  # Mid game support
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "cultist", "support", "caster", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="hellhound",
            name="Hellhound",
            role="Skirmisher",
            tier=2,
            ai_profile="skirmisher",
            base_hp=18,
            hp_per_floor=1.7,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=17,
            xp_per_floor=2.1,
            skill_ids=[
                "feral_claws",
                "poison_strike",
            ],
            difficulty_level=52,  # Mid game beast
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=1.0,
            tags=["mid_game", "demon", "beast", "skirmisher", "fire", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="cursed_chest_mimic",
            name="Cursed Chest Mimic",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=30,
            hp_per_floor=2.2,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=2,
            def_per_floor=0.4,
            base_xp=22,
            xp_per_floor=2.6,
            skill_ids=[
                "heavy_slam",
                "feral_claws",
            ],
            difficulty_level=61,  # Mid-late game unique
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.2,  # Very rare
            tags=["mid_game", "late_game", "brute", "unique", "treasure", "mimic"],
        )
    )
    
    # --- New Mid-Game Enemies with Advanced AI Profiles --------------------
    
    register_archetype(
        EnemyArchetype(
            id="orc_warlord",
            name="Orc Warlord",
            role="Elite Brute",
            tier=2,
            ai_profile="commander",  # Coordinates orc packs
            base_hp=28,
            hp_per_floor=2.5,
            base_attack=9,
            atk_per_floor=1.3,
            base_defense=3,
            def_per_floor=0.6,
            base_xp=20,
            xp_per_floor=2.4,
            skill_ids=[
                "war_cry",
                "mark_target",
                "heavy_slam",
            ],
            difficulty_level=60,  # Strong mid-game leader
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.6,  # Less common, leader role
            tags=["mid_game", "orc", "elite", "brute", "commander", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="shadow_assassin",
            name="Shadow Assassin",
            role="Skirmisher",
            tier=2,
            ai_profile="assassin",  # Targets isolated/low HP enemies
            base_hp=16,
            hp_per_floor=1.6,
            base_attack=8,
            atk_per_floor=1.3,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=18,
            xp_per_floor=2.3,
            skill_ids=[
                "crippling_blow",
                "poison_strike",
                "nimble_step",
            ],
            difficulty_level=57,  # Mid-game assassin
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "assassin", "skirmisher", "shadow", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="stone_guardian",
            name="Stone Guardian",
            role="Brute",
            tier=2,
            ai_profile="defender",  # Protects allies
            base_hp=32,
            hp_per_floor=2.6,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=4,
            def_per_floor=0.7,
            base_xp=19,
            xp_per_floor=2.2,
            skill_ids=[
                "guard",
                "heavy_slam",
            ],
            difficulty_level=58,  # Tanky mid-game defender
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.7,
            tags=["mid_game", "construct", "brute", "tank", "defender", "common"],
            resistances={"physical": 0.4},  # 60% physical resistance
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="necromancer",
            name="Necromancer",
            role="Support",
            tier=2,
            ai_profile="controller",  # Debuffs and crowd control
            base_hp=20,
            hp_per_floor=1.9,
            base_attack=7,
            atk_per_floor=1.2,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=22,
            xp_per_floor=2.6,
            skill_ids=[
                "dark_hex",
                "mark_target",
                "fear_scream",
            ],
            difficulty_level=59,  # Strong mid-game controller
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.7,
            tags=["mid_game", "undead", "support", "caster", "controller", "rare"],
        )
    )
    
    # --- Additional Mid-Game Enemies -----------------------------------------
    
    register_archetype(
        EnemyArchetype(
            id="orc_shaman",
            name="Orc Shaman",
            role="Support",
            tier=2,
            ai_profile="support",  # Heals and buffs orcs
            base_hp=20,
            hp_per_floor=1.9,
            base_attack=6,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=17,
            xp_per_floor=2.1,
            skill_ids=[
                "heal_ally",
                "war_cry",
                "dark_hex",
            ],
            difficulty_level=53,
            spawn_min_floor=3,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "orc", "support", "caster", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="wraith",
            name="Wraith",
            role="Skirmisher",
            tier=2,
            ai_profile="assassin",  # Targets isolated enemies
            base_hp=15,
            hp_per_floor=1.5,
            base_attack=7,
            atk_per_floor=1.2,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=18,
            xp_per_floor=2.2,
            skill_ids=[
                "life_drain",
                "phase_shift",
            ],
            difficulty_level=55,
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.9,
            tags=["mid_game", "undead", "skirmisher", "assassin", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="ogre_warrior",
            name="Ogre Warrior",
            role="Brute",
            tier=2,
            ai_profile="berserker",  # Aggressive when low HP
            base_hp=34,
            hp_per_floor=2.9,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=2,
            def_per_floor=0.5,
            base_xp=20,
            xp_per_floor=2.4,
            skill_ids=[
                "berserker_rage",
                "heavy_slam",
            ],
            difficulty_level=59,
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.9,
            tags=["mid_game", "giant", "brute", "berserker", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="earth_elemental",
            name="Earth Elemental",
            role="Brute",
            tier=2,
            ai_profile="defender",  # Protects allies
            base_hp=30,
            hp_per_floor=2.6,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=5,
            def_per_floor=0.8,
            base_xp=19,
            xp_per_floor=2.3,
            skill_ids=[
                "guard",
                "heavy_slam",
            ],
            difficulty_level=57,
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "elemental", "brute", "tank", "defender", "common"],
            resistances={"physical": 0.3},  # 70% physical resistance
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="dark_ranger",
            name="Dark Ranger",
            role="Skirmisher",
            tier=2,
            ai_profile="tactician",  # Smart positioning and combos
            base_hp=18,
            hp_per_floor=1.7,
            base_attack=8,
            atk_per_floor=1.3,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=19,
            xp_per_floor=2.3,
            skill_ids=[
                "mark_target",
                "crippling_blow",
                "poison_strike",
            ],
            difficulty_level=56,
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "human", "skirmisher", "tactician", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="bone_mage",
            name="Bone Mage",
            role="Invoker",
            tier=2,
            ai_profile="controller",  # Debuffs and crowd control
            base_hp=17,
            hp_per_floor=1.6,
            base_attack=7,
            atk_per_floor=1.2,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=20,
            xp_per_floor=2.4,
            skill_ids=[
                "dark_hex",
                "mark_target",
                "fear_scream",
            ],
            difficulty_level=58,
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.7,
            tags=["mid_game", "undead", "invoker", "caster", "controller", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="cave_troll",
            name="Cave Troll",
            role="Brute",
            tier=2,
            ai_profile="berserker",  # Aggressive regeneration
            base_hp=32,
            hp_per_floor=2.8,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=2,
            def_per_floor=0.5,
            base_xp=21,
            xp_per_floor=2.5,
            skill_ids=[
                "regeneration",
                "berserker_rage",
                "heavy_slam",
            ],
            difficulty_level=60,
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.8,
            tags=["mid_game", "beast", "brute", "berserker", "common"],
            unique_mechanics=["regeneration"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="shadow_stalker",
            name="Shadow Stalker",
            role="Skirmisher",
            tier=2,
            ai_profile="assassin",  # Targets isolated enemies
            base_hp=16,
            hp_per_floor=1.6,
            base_attack=9,
            atk_per_floor=1.4,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=20,
            xp_per_floor=2.4,
            skill_ids=[
                "crippling_blow",
                "poison_strike",
                "life_drain",
            ],
            difficulty_level=58,
            spawn_min_floor=4,
            spawn_max_floor=8,
            spawn_weight=0.7,
            tags=["mid_game", "shadow", "skirmisher", "assassin", "rare"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="iron_golem",
            name="Iron Golem",
            role="Brute",
            tier=2,
            ai_profile="defender",  # Protects allies
            base_hp=36,
            hp_per_floor=3.0,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=6,
            def_per_floor=0.9,
            base_xp=22,
            xp_per_floor=2.6,
            skill_ids=[
                "guard",
                "heavy_slam",
                "counter_attack",
            ],
            difficulty_level=62,
            spawn_min_floor=5,
            spawn_max_floor=8,
            spawn_weight=0.6,
            tags=["mid_game", "construct", "brute", "tank", "defender", "rare"],
            resistances={"physical": 0.2, "magic": 0.5},  # Very resistant
        )
    )