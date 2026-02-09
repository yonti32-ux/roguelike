"""
Party power rating for overworld parties.

Provides a dynamic power value (float) instead of the old 1-5 combat_strength.
Power is used for:
- Overworld display (threat level, tooltips)
- Simulated faction/party-vs-party combat
- Battle conversion: enemy count, archetype selection, and stat scaling

Power is computed from PartyType (base power) and RoamingParty (size, state)
so the same party type can have different effective power per instance.
"""

from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .roaming_party import RoamingParty
    from .party_types import PartyType


# Power scale: roughly 5 (weakest) to 150+ (boss-tier). Old 1-5 maps to ~10-50.
POWER_MIN = 5.0
POWER_MAX = 150.0

# Display tiers for UI
POWER_TIERS = [
    (15, "Trivial"),
    (35, "Weak"),
    (55, "Moderate"),
    (80, "Strong"),
    (110, "Elite"),
    (POWER_MAX + 1, "Boss"),
]


def get_base_power(party_type: "PartyType") -> float:
    """
    Get the base power rating for a party type (no size scaling).
    
    Uses power_rating if set, otherwise derives from combat_strength:
    combat_strength 1 -> 10, 5 -> 50 (linear).
    """
    if getattr(party_type, "power_rating", None) is not None:
        base = float(party_type.power_rating)
    else:
        # Backward compat: combat_strength 1-5 -> 10-50
        strength = getattr(party_type, "combat_strength", 1)
        strength = max(1, min(5, int(strength)))
        base = 10.0 + (strength - 1) * 10.0  # 10, 20, 30, 40, 50
    return max(POWER_MIN, min(POWER_MAX, base))


def get_party_power(
    party: "RoamingParty",
    party_type: "PartyType",
) -> float:
    """
    Get the effective power of a roaming party (type + size + state).
    
    - Base power from party type (power_rating or combat_strength).
    - Scaled by party size: size 1 = 1.0x, each extra member adds ~15% (capped).
    - Optional: wounded/defeated state could reduce power (future).
    
    Returns:
        Power value in [POWER_MIN, POWER_MAX] range (may exceed for bosses).
    """
    base = get_base_power(party_type)
    size = max(1, getattr(party, "party_size", 1))
    # Size factor: 1 -> 1.0, 2 -> 1.15, 3 -> 1.30, 4 -> 1.45, 5 -> 1.60, cap at ~2.0
    size_factor = 1.0 + (size - 1) * 0.15
    size_factor = min(2.0, size_factor)
    
    effective = base * size_factor

    # Hunt XP: natural creatures that have killed prey get slightly stronger (cap +25%)
    xp = getattr(party, "xp", 0)
    if xp > 0:
        xp_factor = 1.0 + min(0.25, xp / 200.0)  # 200 XP -> +25% power
        effective *= xp_factor
    
    # Health state (for future: wounded parties are weaker)
    health_state = getattr(party, "health_state", "healthy")
    if health_state == "wounded":
        effective *= 0.7
    elif health_state == "defeated":
        effective *= 0.3
    
    return max(POWER_MIN, min(POWER_MAX * 1.2, effective))


def power_to_display_tier(power: float) -> str:
    """Convert power value to a display tier label (e.g. 'Moderate', 'Elite')."""
    for threshold, label in POWER_TIERS:
        if power < threshold:
            return label
    return POWER_TIERS[-1][1]


def power_to_floor_index(power: float, player_level: int) -> int:
    """
    Map party power (+ player level) to a floor index for battle scaling.
    
    Used by battle_conversion to pick enemy archetypes and scale stats.
    Higher power -> higher floor -> stronger archetypes and stats.
    """
    # Power contributes: 0-50 power -> 0-5 floor, 50-100 -> 5-10, etc.
    power_floor = int(power / 15)  # e.g. 30 -> 2, 75 -> 5
    # Blend with player level so we don't spawn floor-1 enemies for a level-20 player
    floor = max(1, (power_floor + player_level + 1) // 2)
    return max(1, min(99, floor))


def power_to_enemy_count_factor(power: float) -> float:
    """
    Scale for number of enemies: higher power -> more enemies (or same count, stronger).
    Returns a factor typically in [0.7, 1.5] for use in count formulas.
    """
    # e.g. power 20 -> 0.8, power 50 -> 1.0, power 80 -> 1.2
    import math
    return 0.7 + 0.5 * math.log2(1 + power / 25.0)


def power_to_stat_factor(power: float) -> float:
    """
    Scale for enemy/ally stats (HP, attack, defense) in battle.
    Returns a factor typically in [0.6, 1.3] so battle parties feel right.
    """
    # power 20 -> ~0.75, power 50 -> ~0.95, power 90 -> ~1.15
    return 0.6 + (power / 120.0)


def get_power_display_string(power: float, include_tier: bool = True) -> str:
    """Format power for UI: e.g. '24 (Moderate)' or '24'."""
    if include_tier:
        tier = power_to_display_tier(power)
        return f"{int(round(power))} ({tier})"
    return str(int(round(power)))


# ---------------------------------------------------------------------------
# Overworld progression: no floors, so we scale by player level
# ---------------------------------------------------------------------------

def get_target_power_for_level(player_level: int) -> float:
    """
    "Ideal" challenge power for the given player level (for spawn weighting).
    Low level -> low target (weak parties common); high level -> high target (strong parties more likely).
    """
    level = max(1, int(player_level))
    # e.g. level 1 -> 12, level 10 -> 30, level 25 -> 55, level 50 -> 100
    return min(POWER_MAX, 10.0 + level * 1.8)


def get_spawn_weight_modifier_for_level(party_type: "PartyType", player_level: int) -> float:
    """
    Multiplier for spawn weight so overworld parties scale with progression.

    - At low player level: weak party types (low base power) get full or boosted weight.
    - As player level increases: stronger types get increasingly likely (higher modifier).
    - Weak types never disappear; they just become relatively less common.

    Returns a value typically in [0.4, 1.6]. Use: effective_weight = spawn_weight * modifier.
    """
    base_power = get_base_power(party_type)
    target = get_target_power_for_level(player_level)
    # Ratio: 1.0 when base_power matches target; <1 when party is weak for level; >1 when strong
    ratio = base_power / max(5.0, target)
    # Soft curve: 0.5 + 0.5*ratio, capped so we don't over-penalize or over-reward
    modifier = 0.5 + 0.5 * min(2.0, ratio)
    return max(0.4, min(1.6, modifier))


def get_level_size_bonus(player_level: int) -> int:
    """
    Max extra party size (0, 1, or 2) for spawns at higher player levels.
    Caller should add random.randint(0, get_level_size_bonus(level)) to base size.
    Same party type can appear slightly larger in a "higher-level" world.
    """
    if player_level < 8:
        return 0
    if player_level < 18:
        return 1
    return 2
