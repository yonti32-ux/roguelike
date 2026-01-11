# systems/stat_distribution.py

"""Stat distribution data structure for character creation."""

from dataclasses import dataclass, field


@dataclass
class StatDistribution:
    """
    Tracks how stat points were allocated during character creation.
    
    Players get 3-5 stat points to allocate to various stats.
    These are stored separately and applied to the base StatBlock.
    """
    hp_points: int = 0
    attack_points: int = 0
    defense_points: int = 0
    skill_power_points: float = 0.0
    crit_points: float = 0.0
    dodge_points: float = 0.0
    speed_points: float = 0.0
    
    def total_points_spent(self) -> float:
        """Calculate total points spent across all stats."""
        return (
            self.hp_points +
            self.attack_points +
            self.defense_points +
            self.skill_power_points +
            self.crit_points +
            self.dodge_points +
            self.speed_points
        )
    
    def apply_to_stat_block(self, stat_block) -> None:
        """
        Apply this distribution to a StatBlock.
        
        This adds the allocated points as flat values to the stats.
        """
        stat_block.max_hp += self.hp_points
        stat_block.attack += self.attack_points
        stat_block.defense += self.defense_points
        stat_block.skill_power += self.skill_power_points
        stat_block.crit_chance += self.crit_points
        stat_block.dodge_chance += self.dodge_points
        stat_block.speed += self.speed_points

