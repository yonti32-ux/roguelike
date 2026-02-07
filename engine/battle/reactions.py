"""
Battle reaction system module.

Handles reactions like Attacks of Opportunity (AoO) and can be extended for
overwatch, counter-attacks, and other reactive abilities.

Design philosophy:
- Reactions are triggered by specific events (movement, attacks, etc.)
- Units can have different reaction capabilities (granted by perks/skills)
- Reactions consume reaction points (typically 1 per turn)
- System is extensible for future reaction types (overwatch, intercept, etc.)
"""

from typing import List, Optional, Callable
from engine.battle.types import BattleUnit, Side
from engine.battle.combat import _get_distance


class ReactionType:
    """Types of reactions available."""
    ATTACK_OF_OPPORTUNITY = "attack_of_opportunity"
    COUNTER_ATTACK = "counter_attack"  # Future: automatic counter on being hit
    OVERWATCH = "overwatch"  # Future: react to movement in range
    INTERCEPT = "intercept"  # Future: protect ally from attack


class ReactionCapability:
    """
    Represents a reaction capability a unit has.
    
    This is a foundation class that can be extended for different reaction types.
    """
    def __init__(
        self,
        reaction_type: str,
        trigger_condition: Callable,  # Function that checks if reaction should trigger
        execute_reaction: Callable,  # Function that executes the reaction
        description: str = "",
    ):
        self.reaction_type = reaction_type
        self.trigger_condition = trigger_condition
        self.execute_reaction = execute_reaction
        self.description = description


class BattleReactions:
    """
    Handles reaction system for the battle scene.
    
    Manages reaction capabilities, triggers, and execution.
    """
    
    def __init__(self, scene):
        """
        Initialize the reaction system with a reference to the battle scene.
        
        Args:
            scene: The BattleScene instance
        """
        self.scene = scene
    
    def has_reaction_capability(self, unit: BattleUnit, reaction_type: str) -> bool:
        """
        Check if a unit has a specific reaction capability.
        
        Args:
            unit: The unit to check
            reaction_type: Type of reaction (ReactionType constant)
        
        Returns:
            True if unit can perform this reaction type
        """
        # Check if unit has reactions_available list
        if not hasattr(unit, "reaction_capabilities"):
            return False
        
        return reaction_type in unit.reaction_capabilities
    
    def can_use_reaction(self, unit: BattleUnit) -> bool:
        """
        Check if unit has reaction points available.
        
        Args:
            unit: The unit to check
        
        Returns:
            True if unit can use a reaction this turn
        """
        if not hasattr(unit, "reactions_remaining"):
            return False
        return unit.reactions_remaining > 0
    
    def grant_reaction_capability(self, unit: BattleUnit, reaction_type: str) -> None:
        """
        Grant a reaction capability to a unit (typically from a perk).
        
        Args:
            unit: The unit to grant capability to
            reaction_type: Type of reaction (ReactionType constant)
        """
        if not hasattr(unit, "reaction_capabilities"):
            unit.reaction_capabilities = []
        
        if reaction_type not in unit.reaction_capabilities:
            unit.reaction_capabilities.append(reaction_type)
    
    def reset_reactions(self, unit: BattleUnit) -> None:
        """
        Reset reaction points at the start of a unit's turn.
        
        Args:
            unit: The unit to reset reactions for
        """
        # Grant 1 reaction per turn if unit has any reaction capabilities
        if hasattr(unit, "reaction_capabilities") and unit.reaction_capabilities:
            unit.reactions_remaining = 1
        else:
            unit.reactions_remaining = 0
    
    def check_disengagement(self, moving_unit: BattleUnit, old_gx: int, old_gy: int, new_gx: int, new_gy: int) -> List[BattleUnit]:
        """
        Check if a unit's movement triggers disengagement (leaving melee range).
        
        Args:
            moving_unit: Unit that is moving
            old_gx, old_gy: Previous position
            new_gx, new_gy: New position
        
        Returns:
            List of units that can make attacks of opportunity against the moving unit
        """
        # Get enemies of the moving unit
        potential_reactors = []
        if moving_unit.side == "player":
            potential_reactors = self.scene.enemy_units
        else:
            potential_reactors = self.scene.player_units
        
        reactors = []
        
        for reactor in potential_reactors:
            if not reactor.is_alive:
                continue
            
            # Check if reactor has AoO capability
            if not self.has_reaction_capability(reactor, ReactionType.ATTACK_OF_OPPORTUNITY):
                continue
            
            # Check if reactor can use a reaction
            if not self.can_use_reaction(reactor):
                continue
            
            # Check if moving unit was adjacent to reactor before movement
            old_distance = _get_distance(old_gx, old_gy, reactor.gx, reactor.gy, use_chebyshev=True)
            if old_distance != 1:
                continue  # Wasn't adjacent before
            
            # Check if moving unit is no longer adjacent after movement
            new_distance = _get_distance(new_gx, new_gy, reactor.gx, reactor.gy, use_chebyshev=True)
            if new_distance > 1:
                # Disengagement! Reactor can make AoO
                reactors.append(reactor)
        
        return reactors
    
    def execute_attack_of_opportunity(self, reactor: BattleUnit, target: BattleUnit) -> bool:
        """
        Execute an Attack of Opportunity.
        
        Args:
            reactor: Unit performing the AoO
            target: Unit being attacked
        
        Returns:
            True if AoO was executed successfully
        """
        if not self.can_use_reaction(reactor):
            return False
        
        if not self.has_reaction_capability(reactor, ReactionType.ATTACK_OF_OPPORTUNITY):
            return False
        
        # Check if target is in melee range (should be, since we're checking disengagement)
        # But verify anyway
        weapon_range = self.scene.combat._get_weapon_range(reactor)
        if weapon_range < 1:
            return False
        
        # Use Chebyshev distance for melee
        distance = _get_distance(reactor.gx, reactor.gy, target.gx, target.gy, use_chebyshev=True)
        if distance > weapon_range:
            return False
        
        # Execute the attack with reduced damage (75% as discussed)
        base_damage = reactor.attack_power
        base_damage = int(base_damage * 0.75)  # AoO deals 75% damage
        
        # Apply damage
        damage = self.scene.combat.apply_damage(reactor, target, base_damage, skill_id=None)
        
        # Log the reaction
        self.scene._log(f"{reactor.name} makes an attack of opportunity against {target.name} for {damage} dmg!")
        
        # Consume reaction point
        reactor.reactions_remaining -= 1
        
        return True

