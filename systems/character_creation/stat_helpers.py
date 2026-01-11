# systems/character_creation/stat_helpers.py

"""Helper functions for applying stat modifiers from backgrounds and traits."""

from ..stats import StatBlock


def apply_percentage_stat_modifiers(stat_block: StatBlock, modifiers: StatBlock) -> None:
    """
    Apply percentage-based stat modifiers to a StatBlock.
    
    Modifiers are applied as multipliers (e.g., 0.05 = +5%, -0.10 = -10%).
    For percentage stats (crit_chance, dodge_chance, status_resist, skill_power, speed),
    the modifier is added directly (they're already percentages).
    
    For flat stats (max_hp, attack, defense, max_mana, max_stamina, etc.),
    the modifier is applied as a multiplier and then rounded.
    
    IMPORTANT: Only applies modifiers that are non-default values.
    Since StatBlock has defaults, we compare against default StatBlock to avoid
    applying default values as multipliers.
    
    Args:
        stat_block: The StatBlock to modify (modified in-place)
        modifiers: The StatBlock containing percentage modifiers to apply
    """
    # Create a default StatBlock to compare against
    default = StatBlock()
    
    # Flat stats (multiply, then round) - only if modifier differs from default
    if modifiers.max_hp != default.max_hp:
        stat_block.max_hp = int(stat_block.max_hp * (1.0 + modifiers.max_hp))
    if modifiers.attack != default.attack:
        stat_block.attack = int(stat_block.attack * (1.0 + modifiers.attack))
    if modifiers.defense != default.defense:
        stat_block.defense = int(stat_block.defense * (1.0 + modifiers.defense))
    if modifiers.max_mana != default.max_mana:
        stat_block.max_mana = int(stat_block.max_mana * (1.0 + modifiers.max_mana))
    if modifiers.max_stamina != default.max_stamina:
        stat_block.max_stamina = int(stat_block.max_stamina * (1.0 + modifiers.max_stamina))
    if modifiers.movement_points_bonus != default.movement_points_bonus:
        # Movement points bonus is already flat, so add directly
        stat_block.movement_points_bonus += modifiers.movement_points_bonus
    
    # Percentage stats (add directly, they're already percentages) - only if modifier differs from default
    if modifiers.skill_power != default.skill_power:
        stat_block.skill_power += modifiers.skill_power
    if modifiers.crit_chance != default.crit_chance:
        stat_block.crit_chance += modifiers.crit_chance
    if modifiers.dodge_chance != default.dodge_chance:
        stat_block.dodge_chance += modifiers.dodge_chance
    if modifiers.status_resist != default.status_resist:
        stat_block.status_resist += modifiers.status_resist
    if modifiers.speed != default.speed:
        stat_block.speed += modifiers.speed
    
    # Regen bonuses (add directly, they're flat values) - only if modifier differs from default
    if modifiers.stamina_regen_bonus != default.stamina_regen_bonus:
        stat_block.stamina_regen_bonus += modifiers.stamina_regen_bonus
    if modifiers.mana_regen_bonus != default.mana_regen_bonus:
        stat_block.mana_regen_bonus += modifiers.mana_regen_bonus
    
    # Initiative (flat value, add directly) - only if modifier differs from default
    if modifiers.initiative != default.initiative:
        stat_block.initiative += modifiers.initiative

