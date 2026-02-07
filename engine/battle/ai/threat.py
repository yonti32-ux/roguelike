"""
Threat assessment system.

Calculates threat values for units to help AI prioritize targets intelligently.
"""

from typing import List, Dict
from systems.statuses import has_status
from engine.battle.types import BattleUnit


class ThreatAssessment:
    """
    Calculates and tracks threat values for units.
    
    Threat value represents how dangerous a unit is, considering:
    - Current HP and max HP
    - Attack power
    - Skill power
    - Status effects (buffs/debuffs)
    - Position (isolated vs protected)
    - Role/type
    """
    
    def __init__(self):
        self.threat_cache: Dict[int, float] = {}  # Use id(unit) as key since BattleUnit is not hashable
    
    def calculate_threat(self, unit: BattleUnit) -> float:
        """
        Calculate threat value for a unit.
        
        Higher values = more dangerous/threatening.
        
        Returns:
            Threat value (0.0 to 100.0+)
        """
        unit_id = id(unit)
        if unit_id in self.threat_cache:
            return self.threat_cache[unit_id]
        
        threat = 0.0
        
        # Base threat from attack power (0-40 points)
        threat += min(40.0, unit.attack_power * 0.5)
        
        # HP-based threat (healthy units are more threatening) (0-30 points)
        if unit.max_hp > 0:
            hp_ratio = unit.hp / float(unit.max_hp)
            threat += hp_ratio * 30.0
        
        # Skill power threat (0-20 points)
        skill_power = getattr(unit.entity, "skill_power", 1.0)
        threat += min(20.0, skill_power * 5.0)
        
        # Status effect modifiers
        if has_status(unit.statuses, "empowered"):
            threat += 10.0
        if has_status(unit.statuses, "war_cry"):
            threat += 8.0
        if has_status(unit.statuses, "marked"):
            threat -= 5.0  # Marked targets are easier to kill
        if has_status(unit.statuses, "cursed"):
            threat -= 3.0
        if has_status(unit.statuses, "stunned"):
            threat -= 15.0  # Stunned units are much less threatening
        
        # Number of skills (more skills = more versatile = more threatening)
        threat += len(unit.skills) * 2.0
        
        self.threat_cache[unit_id] = threat
        return threat
    
    def clear_cache(self):
        """Clear the threat cache (call at start of each turn)."""
        self.threat_cache.clear()


def calculate_threat_value(unit: BattleUnit) -> float:
    """
    Convenience function to calculate threat for a single unit.
    
    Args:
        unit: The unit to assess
        
    Returns:
        Threat value
    """
    assessor = ThreatAssessment()
    return assessor.calculate_threat(unit)


def rank_targets_by_threat(targets: List[BattleUnit]) -> List[BattleUnit]:
    """
    Rank targets by threat value (highest threat first).
    
    Args:
        targets: List of target units
        
    Returns:
        List of targets sorted by threat (highest first)
    """
    assessor = ThreatAssessment()
    return sorted(targets, key=lambda t: assessor.calculate_threat(t), reverse=True)
