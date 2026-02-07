"""
Early game enemy archetypes (Tier 1, Difficulty 10-30).

These are the basic enemies that appear in the early floors of the dungeon.
"""

from ..types import EnemyArchetype
from ..registry import register_archetype


def register_early_game_archetypes() -> None:
    """Register all early game enemy archetypes."""
    
    # --- Tier 1: early-game fodder ----------------------------------------

    register_archetype(
        EnemyArchetype(
            id="goblin_skirmisher",
            name="Goblin Skirmisher",
            role="Skirmisher",
            tier=1,  # Kept for backward compatibility
            ai_profile="skirmisher",
            base_hp=10,
            hp_per_floor=1.0,
            base_attack=4,
            atk_per_floor=0.7,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=6,
            xp_per_floor=1.0,
            skill_ids=[
                "poison_strike",  # new enemy-only skill
                "nimble_step",    # reuses existing defensive skill
            ],
            # New difficulty system (explicit values override auto-calculation)
            difficulty_level=15,  # Early game enemy
            spawn_min_floor=1,
            spawn_max_floor=4,  # Can appear floors 1-4
            spawn_weight=1.5,  # Common enemy
            tags=["early_game", "goblin", "skirmisher", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="goblin_brute",
            name="Goblin Brute",
            role="Brute",
            tier=1,
            ai_profile="brute",
            base_hp=16,
            hp_per_floor=1.5,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=8,
            xp_per_floor=1.1,
            skill_ids=[
                "heavy_slam",      # big single-hit
            ],
            # New difficulty system
            difficulty_level=18,  # Slightly harder than skirmisher
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=1.2,  # Common but slightly less than skirmisher
            tags=["early_game", "goblin", "brute", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="bandit_cutthroat",
            name="Bandit Cutthroat",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=12,
            hp_per_floor=1.2,
            base_attack=5,
            atk_per_floor=0.9,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=7,
            xp_per_floor=1.1,
            skill_ids=[
                "lunge",           # uses existing hero-style skill
            ],
            # New difficulty system
            difficulty_level=17,  # Similar to goblin skirmisher
            spawn_min_floor=1,
            spawn_max_floor=5,  # Can appear slightly later
            spawn_weight=1.0,  # Normal spawn rate
            tags=["early_game", "bandit", "skirmisher", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="cultist_adept",
            name="Cultist Adept",
            role="Invoker",
            tier=1,
            ai_profile="caster",
            base_hp=11,
            hp_per_floor=1.1,
            base_attack=4,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=9,
            xp_per_floor=1.3,
            skill_ids=[
                "dark_hex",        # curse / debuff
            ],
            # New difficulty system
            difficulty_level=20,  # Slightly higher XP reward = slightly harder
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=0.8,  # Less common, prefers event rooms
            tags=["early_game", "cultist", "invoker", "caster", "common"],
        )
    )

    # --- New Tier 1 Enemies ----------------------------------------------------

    register_archetype(
        EnemyArchetype(
            id="goblin_shaman",
            name="Goblin Shaman",
            role="Support",
            tier=1,
            ai_profile="caster",
            base_hp=9,
            hp_per_floor=1.0,
            base_attack=3,
            atk_per_floor=0.6,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=8,
            xp_per_floor=1.2,
            skill_ids=[
                "heal_ally",
                "buff_ally",
                "dark_hex",
            ],
            # New difficulty system
            difficulty_level=19,  # Support enemy, slightly higher
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=0.9,  # Less common, support role
            tags=["early_game", "goblin", "support", "caster", "common"],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="skeleton_archer",
            name="Skeleton Archer",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=10,
            hp_per_floor=1.0,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=7,
            xp_per_floor=1.1,
            skill_ids=[
                "mark_target",
            ],
            # New difficulty system
            difficulty_level=16,  # Similar to goblin skirmisher
            spawn_min_floor=1,
            spawn_max_floor=5,  # Can appear slightly later
            spawn_weight=1.0,
            tags=["early_game", "undead", "skirmisher", "common"],
            # Unique mechanics & resistances
            unique_mechanics=[],
            resistances={"poison": 0.5},  # Undead resist poison (50% damage)
        )
    )

    register_archetype(
        EnemyArchetype(
            id="dire_rat",
            name="Dire Rat",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=8,
            hp_per_floor=0.8,
            base_attack=4,
            atk_per_floor=0.7,
            base_defense=0,
            def_per_floor=0.1,
            base_xp=5,
            xp_per_floor=0.9,
            skill_ids=[
                "disease_strike",
                "nimble_step",
            ],
            # New difficulty system
            difficulty_level=12,  # Weakest Tier 1 enemy
            spawn_min_floor=1,
            spawn_max_floor=3,  # Early floors only
            spawn_weight=1.3,  # Common weak enemy
            tags=["early_game", "beast", "skirmisher", "common", "weak"],
        )
    )

    # --- Early Game Additions (Difficulty 10-30) ---
    
    register_archetype(
        EnemyArchetype(
            id="goblin_trapper",
            name="Goblin Trapper",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=9,
            hp_per_floor=0.9,
            base_attack=4,
            atk_per_floor=0.6,
            base_defense=0,
            def_per_floor=0.1,
            base_xp=6,
            xp_per_floor=0.9,
            skill_ids=[
                "poison_strike",
                "nimble_step",
            ],
            difficulty_level=14,  # Very early game
            spawn_min_floor=1,
            spawn_max_floor=3,
            spawn_weight=1.2,
            tags=["early_game", "goblin", "skirmisher", "common", "weak"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="skeleton_warrior",
            name="Skeleton Warrior",
            role="Brute",
            tier=1,
            ai_profile="brute",
            base_hp=14,
            hp_per_floor=1.3,
            base_attack=5,
            atk_per_floor=0.7,
            base_defense=1,
            def_per_floor=0.2,
            base_xp=7,
            xp_per_floor=1.0,
            skill_ids=[
                "heavy_slam",
            ],
            difficulty_level=16,  # Early game brute
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=1.0,
            tags=["early_game", "undead", "brute", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="cultist_zealot",
            name="Cultist Zealot",
            role="Invoker",
            tier=1,
            ai_profile="caster",
            base_hp=10,
            hp_per_floor=1.0,
            base_attack=4,
            atk_per_floor=0.7,
            base_defense=0,
            def_per_floor=0.1,
            base_xp=8,
            xp_per_floor=1.1,
            skill_ids=[
                "dark_hex",
            ],
            difficulty_level=18,  # Early game caster
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=0.9,
            tags=["early_game", "cultist", "invoker", "caster", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="wild_boar",
            name="Wild Boar",
            role="Brute",
            tier=1,
            ai_profile="brute",
            base_hp=13,
            hp_per_floor=1.2,
            base_attack=5,
            atk_per_floor=0.7,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=6,
            xp_per_floor=0.9,
            skill_ids=[
                "heavy_slam",
            ],
            difficulty_level=13,  # Weak early game beast
            spawn_min_floor=1,
            spawn_max_floor=3,
            spawn_weight=1.3,
            tags=["early_game", "beast", "brute", "common", "weak"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="spider_scout",
            name="Spider Scout",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=8,
            hp_per_floor=0.9,
            base_attack=4,
            atk_per_floor=0.6,
            base_defense=0,
            def_per_floor=0.1,
            base_xp=5,
            xp_per_floor=0.8,
            skill_ids=[
                "poison_strike",
                "nimble_step",
            ],
            difficulty_level=11,  # Very weak early game
            spawn_min_floor=1,
            spawn_max_floor=2,
            spawn_weight=1.4,
            tags=["early_game", "beast", "skirmisher", "common", "weak"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="wolf",
            name="Wolf",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=12,
            hp_per_floor=1.1,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=7,
            xp_per_floor=1.0,
            skill_ids=[
                "feral_claws",
                "nimble_step",
            ],
            difficulty_level=18,  # Early-mid game beast
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=1.2,
            tags=["early_game", "beast", "skirmisher", "common"],
        )
    )
    
    # --- Additional Early-Game Enemies --------------------------------------
    
    register_archetype(
        EnemyArchetype(
            id="goblin_shaman",
            name="Goblin Shaman",
            role="Invoker",
            tier=1,
            ai_profile="caster",
            base_hp=11,
            hp_per_floor=1.0,
            base_attack=4,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=7,
            xp_per_floor=1.1,
            skill_ids=[
                "dark_hex",
                "poison_strike",
            ],
            difficulty_level=16,
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=0.8,
            tags=["early_game", "goblin", "invoker", "caster", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="dire_rat",
            name="Dire Rat",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=9,
            hp_per_floor=0.9,
            base_attack=4,
            atk_per_floor=0.7,
            base_defense=0,
            def_per_floor=0.1,
            base_xp=5,
            xp_per_floor=0.9,
            skill_ids=[
                "poison_strike",
            ],
            difficulty_level=12,
            spawn_min_floor=1,
            spawn_max_floor=3,
            spawn_weight=1.5,
            tags=["early_game", "beast", "skirmisher", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="skeleton_warrior",
            name="Skeleton Warrior",
            role="Brute",
            tier=1,
            ai_profile="brute",
            base_hp=14,
            hp_per_floor=1.3,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=7,
            xp_per_floor=1.0,
            skill_ids=[
                "heavy_slam",
            ],
            difficulty_level=17,
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=1.0,
            tags=["early_game", "undead", "brute", "common"],
            resistances={"poison": 0.5},  # 50% poison resistance (undead)
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="bandit_archer",
            name="Bandit Archer",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=10,
            hp_per_floor=1.0,
            base_attack=5,
            atk_per_floor=0.9,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=6,
            xp_per_floor=1.0,
            skill_ids=[
                "lunge",
            ],
            difficulty_level=16,
            spawn_min_floor=1,
            spawn_max_floor=5,
            spawn_weight=1.0,
            tags=["early_game", "bandit", "skirmisher", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="wild_boar",
            name="Wild Boar",
            role="Brute",
            tier=1,
            ai_profile="berserker",  # Aggressive beast
            base_hp=15,
            hp_per_floor=1.4,
            base_attack=6,
            atk_per_floor=0.9,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=8,
            xp_per_floor=1.1,
            skill_ids=[
                "feral_claws",
            ],
            difficulty_level=19,
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=1.1,
            tags=["early_game", "beast", "brute", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="goblin_trapper",
            name="Goblin Trapper",
            role="Skirmisher",
            tier=1,
            ai_profile="assassin",  # Targets isolated enemies
            base_hp=9,
            hp_per_floor=0.9,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.1,
            base_xp=6,
            xp_per_floor=1.0,
            skill_ids=[
                "poison_strike",
                "crippling_blow",
            ],
            difficulty_level=16,
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=0.9,
            tags=["early_game", "goblin", "skirmisher", "assassin", "common"],
        )
    )
    
    register_archetype(
        EnemyArchetype(
            id="corrupted_sprite",
            name="Corrupted Sprite",
            role="Invoker",
            tier=1,
            ai_profile="controller",  # Debuffs and control
            base_hp=8,
            hp_per_floor=0.8,
            base_attack=4,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=6,
            xp_per_floor=1.0,
            skill_ids=[
                "dark_hex",
                "mark_target",
            ],
            difficulty_level=15,
            spawn_min_floor=1,
            spawn_max_floor=4,
            spawn_weight=0.7,
            tags=["early_game", "fey", "invoker", "controller", "rare"],
        )
    )
