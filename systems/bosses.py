"""
Boss and Mini-Boss system.

Defines boss archetypes, stat scaling, and registry for bosses and mini-bosses.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import random

from .namegen import generate_boss_name


@dataclass
class BossArchetype:
    """
    Defines a *type* of boss that can appear in the dungeon.
    
    Similar to EnemyArchetype but with higher base stats and special abilities.
    """
    id: str
    name_template: str = ""  # Optional: if empty, uses name generation
    role: str  # "Brute", "Invoker", "Hybrid", etc.
    tier: int  # 1-3 for mini-bosses, 3+ for final bosses
    boss_type: str  # "mini_boss" or "final_boss"
    
    # Stat scaling (higher than regular enemies)
    base_hp: int
    hp_per_floor: float
    base_attack: int
    atk_per_floor: float
    base_defense: int
    def_per_floor: float
    base_xp: int  # Much higher than regular enemies
    xp_per_floor: float
    
    skill_ids: List[str]  # Special boss abilities
    ai_profile: str
    
    # Initiative (higher for bosses)
    base_initiative: int = 12
    init_per_floor: float = 0.3
    
    # Name generation style (if name_template is empty)
    name_style: str = "auto"  # "brutal", "mystical", "beast", "fantasy", "auto"


BOSS_ARCHETYPES: Dict[str, BossArchetype] = {}


def register_boss(boss: BossArchetype) -> BossArchetype:
    """Register a boss archetype."""
    BOSS_ARCHETYPES[boss.id] = boss
    return boss


def get_boss_archetype(boss_id: str) -> BossArchetype:
    """Get a boss archetype by ID."""
    return BOSS_ARCHETYPES[boss_id]


def compute_scaled_boss_stats(arch: BossArchetype, floor_index: int) -> Tuple[int, int, int, int, int]:
    """
    Scale a boss archetype's stats for the given floor.
    
    Returns (max_hp, attack_power, defense, xp_reward, initiative).
    """
    level = max(1, floor_index)
    max_hp = int(arch.base_hp + arch.hp_per_floor * (level - 1))
    attack = int(arch.base_attack + arch.atk_per_floor * (level - 1))
    defense = int(arch.base_defense + arch.def_per_floor * (level - 1))
    xp = int(arch.base_xp + arch.xp_per_floor * (level - 1))
    
    # Initiative scaling (slightly higher cap than regular enemies)
    raw_initiative = arch.base_initiative + arch.init_per_floor * (level - 1)
    max_initiative = arch.base_initiative + (level - 1) * 0.7
    initiative = int(min(raw_initiative, max_initiative))
    
    return max_hp, attack, defense, xp, initiative


def _tier_for_floor(floor_index: int) -> int:
    """Get tier for a given floor (same as enemy system)."""
    if floor_index <= 2:
        return 1
    elif floor_index <= 4:
        return 2
    else:
        return 3


def choose_miniboss_archetype_for_floor(floor_index: int) -> BossArchetype:
    """
    Pick a mini-boss archetype for the given floor.
    
    Args:
        floor_index: Current floor number
    
    Returns:
        BossArchetype suitable for this floor
    """
    tier = _tier_for_floor(floor_index)
    
    # Find mini-bosses of the appropriate tier
    candidates = [
        b for b in BOSS_ARCHETYPES.values()
        if b.boss_type == "mini_boss" and b.tier == tier
    ]
    
    if not candidates:
        # Fallback: use any mini-boss
        candidates = [b for b in BOSS_ARCHETYPES.values() if b.boss_type == "mini_boss"]
    
    if not candidates:
        raise RuntimeError("No mini-boss archetypes registered.")
    
    return random.choice(candidates)


def choose_final_boss_archetype(floor_count: int) -> BossArchetype:
    """
    Pick a final boss archetype.
    
    Args:
        floor_count: Total number of floors in the dungeon
    
    Returns:
        BossArchetype for the final boss
    """
    # Final bosses are tier 3+
    candidates = [
        b for b in BOSS_ARCHETYPES.values()
        if b.boss_type == "final_boss" and b.tier >= 3
    ]
    
    if not candidates:
        # Fallback: use any final boss
        candidates = [b for b in BOSS_ARCHETYPES.values() if b.boss_type == "final_boss"]
    
    if not candidates:
        raise RuntimeError("No final boss archetypes registered.")
    
    return random.choice(candidates)


def generate_boss_name_for_archetype(
    arch: BossArchetype,
    floor_index: int,
    is_final_boss: bool = False,
) -> str:
    """
    Generate a name for a boss based on its archetype.
    
    Args:
        arch: Boss archetype
        floor_index: Current floor
        is_final_boss: If True, uses final boss naming
    
    Returns:
        Generated boss name
    """
    if arch.name_template:
        # Use provided template
        return arch.name_template
    
    # Generate name using name generator
    tier = arch.tier
    return generate_boss_name(
        tier=tier,
        is_final_boss=is_final_boss,
        use_title=True,
        name_style=arch.name_style,
    )


# ---------------------------------------------------------------------------
# Boss Archetype Definitions
# ---------------------------------------------------------------------------


def _build_boss_archetypes() -> None:
    """Build and register all boss archetypes."""
    
    # --- Tier 1 Mini-Bosses (Early floors: 1-2) ---
    
    register_boss(
        BossArchetype(
            id="goblin_warboss",
            role="Brute",
            tier=1,
            boss_type="mini_boss",
            base_hp=40,
            hp_per_floor=2.5,
            base_attack=8,
            atk_per_floor=1.2,
            base_defense=2,
            def_per_floor=0.4,
            base_xp=40,
            xp_per_floor=5.0,
            skill_ids=["heavy_slam", "war_cry"],
            ai_profile="brute",
            name_style="brutal",
        )
    )
    
    register_boss(
        BossArchetype(
            id="bandit_chieftain",
            role="Skirmisher",
            tier=1,
            boss_type="mini_boss",
            base_hp=35,
            hp_per_floor=2.2,
            base_attack=9,
            atk_per_floor=1.3,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=45,
            xp_per_floor=5.5,
            skill_ids=["lunge", "poison_strike"],
            ai_profile="skirmisher",
            name_style="brutal",
        )
    )
    
    # --- Tier 2 Mini-Bosses (Mid floors: 3-4) ---
    
    register_boss(
        BossArchetype(
            id="orc_warlord",
            role="Brute",
            tier=2,
            boss_type="mini_boss",
            base_hp=70,
            hp_per_floor=3.5,
            base_attack=14,
            atk_per_floor=1.8,
            base_defense=4,
            def_per_floor=0.6,
            base_xp=80,
            xp_per_floor=8.0,
            skill_ids=["heavy_slam", "berserker_rage", "war_cry"],
            ai_profile="brute",
            name_style="brutal",
        )
    )
    
    register_boss(
        BossArchetype(
            id="necromancer_lord",
            role="Support",
            tier=2,
            boss_type="mini_boss",
            base_hp=60,
            hp_per_floor=3.0,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=2,
            def_per_floor=0.5,
            base_xp=85,
            xp_per_floor=8.5,
            skill_ids=["life_drain", "dark_hex", "heal_ally", "regeneration"],
            ai_profile="caster",
            name_style="mystical",
        )
    )
    
    # --- Tier 3 Mini-Bosses (Late floors: 5+) ---
    
    register_boss(
        BossArchetype(
            id="dread_champion",
            role="Elite Brute",
            tier=3,
            boss_type="mini_boss",
            base_hp=100,
            hp_per_floor=4.5,
            base_attack=20,
            atk_per_floor=2.2,
            base_defense=6,
            def_per_floor=0.9,
            base_xp=120,
            xp_per_floor=12.0,
            skill_ids=["heavy_slam", "berserker_rage", "war_cry", "feral_claws"],
            ai_profile="brute",
            name_style="brutal",
        )
    )
    
    register_boss(
        BossArchetype(
            id="shadow_archon",
            role="Hybrid",
            tier=3,
            boss_type="mini_boss",
            base_hp=90,
            hp_per_floor=4.0,
            base_attack=18,
            atk_per_floor=2.0,
            base_defense=5,
            def_per_floor=0.8,
            base_xp=130,
            xp_per_floor=13.0,
            skill_ids=["poison_strike", "dark_hex", "nimble_step", "mark_target"],
            ai_profile="skirmisher",
            name_style="mystical",
        )
    )
    
    # --- Final Bosses (Last floor only) ---
    
    register_boss(
        BossArchetype(
            id="lich_king",
            role="Elite Support",
            tier=3,
            boss_type="final_boss",
            base_hp=180,
            hp_per_floor=6.0,
            base_attack=28,
            atk_per_floor=3.0,
            base_defense=8,
            def_per_floor=1.2,
            base_xp=300,
            xp_per_floor=30.0,
            skill_ids=["life_drain", "dark_hex", "heal_ally", "regeneration", "war_cry"],
            ai_profile="caster",
            name_style="mystical",
        )
    )
    
    register_boss(
        BossArchetype(
            id="dragon_lord",
            role="Elite Brute",
            tier=3,
            boss_type="final_boss",
            base_hp=200,
            hp_per_floor=6.5,
            base_attack=30,
            atk_per_floor=3.2,
            base_defense=7,
            def_per_floor=1.1,
            base_xp=320,
            xp_per_floor=32.0,
            skill_ids=["heavy_slam", "berserker_rage", "war_cry", "feral_claws", "counter_attack"],
            ai_profile="brute",
            name_style="beast",
        )
    )
    
    register_boss(
        BossArchetype(
            id="void_titan",
            role="Hybrid",
            tier=3,
            boss_type="final_boss",
            base_hp=190,
            hp_per_floor=6.2,
            base_attack=29,
            atk_per_floor=3.1,
            base_defense=8,
            def_per_floor=1.2,
            base_xp=310,
            xp_per_floor=31.0,
            skill_ids=["feral_claws", "poison_strike", "dark_hex", "berserker_rage", "regeneration"],
            ai_profile="brute",
            name_style="mystical",
        )
    )


# Build boss archetypes on import
_build_boss_archetypes()

