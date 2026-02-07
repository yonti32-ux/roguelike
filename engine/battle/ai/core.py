"""
Core battle AI module.

Contains the main BattleAI class that orchestrates all AI decision-making.
"""

from typing import List, Optional
import random

from settings import BATTLE_AI_DEFENSIVE_HP_THRESHOLD
from systems.statuses import StatusEffect, has_status
from systems.enemies import get_archetype
from world.entities import Enemy
from engine.battle.types import BattleUnit, Side

from .profiles import get_ai_profile_handler
from .threat import calculate_threat_value
from .skill_priority import SkillPrioritizer
from .coordination import CoordinationManager
from .positioning import PositioningHelper


class BattleAI:
    """
    Main AI orchestrator for enemy units.
    
    Delegates to specialized modules for different aspects of AI decision-making:
    - Profiles: Role-based behavior patterns
    - Threat: Target prioritization
    - Skills: Skill selection and prioritization
    - Coordination: Team tactics and focus fire
    - Positioning: Movement and positioning
    """
    
    def __init__(self, scene):
        """
        Initialize the AI with a reference to the battle scene.
        
        Args:
            scene: The BattleScene instance
        """
        self.scene = scene
        self.skill_prioritizer = SkillPrioritizer(scene)
        self.coordination = CoordinationManager(scene)
        self.positioning = PositioningHelper(scene)
    
    def get_ai_profile(self, unit: BattleUnit) -> str:
        """Get the AI profile for an enemy unit or AI-controlled ally."""
        # Check if it's an enemy with an archetype
        if isinstance(unit.entity, Enemy):
            arch_id = getattr(unit.entity, "archetype_id", None)
            if arch_id:
                try:
                    arch = get_archetype(arch_id)
                    return arch.ai_profile
                except KeyError:
                    pass
        
        # Check if it's an AI-controlled ally with an archetype
        if getattr(unit, "is_ai_controlled", False):
            ally_arch_id = getattr(unit.entity, "ally_archetype_id", None)
            if ally_arch_id:
                try:
                    from systems.allies import get_archetype as get_ally_archetype
                    ally_arch = get_ally_archetype(ally_arch_id)
                    return ally_arch.ai_profile
                except (KeyError, ImportError):
                    pass
            # Default for allies without archetype
            return "brute"
        
        return "brute"  # Default
    
    def choose_target_by_priority(self, unit: BattleUnit, targets: List[BattleUnit]) -> Optional[BattleUnit]:
        """
        Choose target based on AI profile, threat assessment, and coordination.
        
        Uses threat assessment and coordination to make smarter targeting decisions.
        """
        if not targets:
            return None
        
        profile = self.get_ai_profile(unit)
        profile_handler = get_ai_profile_handler(profile)
        
        # Use profile-specific targeting with threat assessment
        return profile_handler.choose_target(unit, targets, self)
    
    def enemies_in_range(self, unit: BattleUnit, max_range: int, use_chebyshev: bool = False) -> List[BattleUnit]:
        """
        Return all enemy units within a given range.
        
        Args:
            unit: The unit checking range
            max_range: Maximum range
            use_chebyshev: If True, use Chebyshev distance (for melee/8-directional).
                          If False, use Manhattan distance (for ranged/4-directional).
        """
        enemies = self.scene.enemy_units if unit.side == "player" else self.scene.player_units
        res: List[BattleUnit] = []
        for u in enemies:
            if not u.is_alive:
                continue
            
            # Calculate distance using appropriate metric
            if use_chebyshev:
                dx = abs(u.gx - unit.gx)
                dy = abs(u.gy - unit.gy)
                dist = max(dx, dy)
            else:
                dist = abs(u.gx - unit.gx) + abs(u.gy - unit.gy)
            
            if dist <= max_range:
                res.append(u)
        return res
    
    def adjacent_enemies(self, unit: BattleUnit) -> List[BattleUnit]:
        """Backwards-compatible helper: enemies at distance 1 (using Chebyshev for 8-directional)."""
        return self.enemies_in_range(unit, 1, use_chebyshev=True)
    
    def allies_in_range(self, unit: BattleUnit, max_range: int, use_chebyshev: bool = False) -> List[BattleUnit]:
        """Return all ally units within range (for support skills)."""
        allies = self.scene.enemy_units if unit.side == "enemy" else self.scene.player_units
        res: List[BattleUnit] = []
        for u in allies:
            if u is unit or not u.is_alive:
                continue
            
            # Calculate distance using appropriate metric
            if use_chebyshev:
                dx = abs(u.gx - unit.gx)
                dy = abs(u.gy - unit.gy)
                dist = max(dx, dy)
            else:
                dist = abs(u.gx - unit.gx) + abs(u.gy - unit.gy)
            
            if dist <= max_range:
                res.append(u)
        return res
    
    def nearest_target(self, unit: BattleUnit, target_side: Side, use_chebyshev: bool = False) -> Optional[BattleUnit]:
        """Find the nearest target on the specified side."""
        candidates = self.scene.player_units if target_side == "player" else self.scene.enemy_units
        candidates = [u for u in candidates if u.is_alive]
        if not candidates:
            return None
        
        def distance_func(u: BattleUnit) -> int:
            if use_chebyshev:
                dx = abs(u.gx - unit.gx)
                dy = abs(u.gy - unit.gy)
                return max(dx, dy)
            else:
                return abs(u.gx - unit.gx) + abs(u.gy - unit.gy)
        
        return min(candidates, key=distance_func)
    
    def find_injured_ally(self, unit: BattleUnit, max_range: int = 1) -> Optional[BattleUnit]:
        """Find an injured ally within range (for healing)."""
        allies = self.allies_in_range(unit, max_range, use_chebyshev=True)
        injured = [a for a in allies if a.hp < a.max_hp * 0.7]  # Below 70% HP
        if injured:
            return min(injured, key=lambda a: a.hp / float(a.max_hp))  # Most injured
        return None
    
    def find_ally_to_buff(self, unit: BattleUnit, max_range: int = 1) -> Optional[BattleUnit]:
        """Find an ally that could benefit from buffs (not already buffed)."""
        allies = self.allies_in_range(unit, max_range, use_chebyshev=True)
        # Prefer allies that aren't already empowered
        unbuffed = [a for a in allies if not has_status(a.statuses, "empowered") and not has_status(a.statuses, "war_cry")]
        if unbuffed:
            # Prefer brutes/skirmishers (damage dealers)
            brutes = [a for a in unbuffed if self.get_ai_profile(a) in ("brute", "skirmisher")]
            if brutes:
                return brutes[0]
            return unbuffed[0]
        return allies[0] if allies else None
    
    def step_towards(self, unit: BattleUnit, target: BattleUnit) -> bool:
        """
        Move unit one step towards target, preferably along a proper path.

        Returns True if movement succeeded.
        """
        # If we're already on the target, nothing to do
        if unit.gx == target.gx and unit.gy == target.gy:
            return False

        # --- Pathfinding-based step (smarter around obstacles/terrain) ---
        path = None
        try:
            # Temporarily give the unit a large movement budget so A* can
            # find a full path to the goal, then restore it.
            original_mp = unit.current_movement_points
            # Upper bound: crossing the whole grid horizontally + vertically
            max_cost = self.scene.grid_width + self.scene.grid_height
            unit.current_movement_points = max_cost
            path = self.scene.pathfinding.find_path(unit, target.gx, target.gy)
            unit.current_movement_points = original_mp
        except Exception:
            # Fail-safe: never let a pathfinding error break the AI turn
            path = None
            unit.current_movement_points = getattr(unit, "current_movement_points", 0)

        # If we have a path, take the next step along it
        if path and len(path) >= 2:
            next_gx, next_gy = path[1]
            dx = next_gx - unit.gx
            dy = next_gy - unit.gy
            # Normalise to a single-tile step (path is 4‑way so this should already be 1 tile)
            if dx > 1:
                dx = 1
            elif dx < -1:
                dx = -1
            if dy > 1:
                dy = 1
            elif dy < -1:
                dy = -1
            if dx != 0 or dy != 0:
                if self.scene._try_move_unit(unit, dx, dy):
                    return True

        # --- Fallback: simple greedy step (old behaviour) ---
        dx = target.gx - unit.gx
        dy = target.gy - unit.gy

        if dx == 0 and dy == 0:
            return False

        step_x = 0
        step_y = 0
        if abs(dx) >= abs(dy) and dx != 0:
            step_x = 1 if dx > 0 else -1
        elif dy != 0:
            step_y = 1 if dy > 0 else -1

        if step_x != 0 or step_y != 0:
            if self.scene._try_move_unit(unit, step_x, step_y):
                return True

        alt_x = 0
        alt_y = 0
        if step_x != 0 and dy != 0:
            alt_y = 1 if dy > 0 else -1
        elif step_y != 0 and dx != 0:
            alt_x = 1 if dx > 0 else -1

        if alt_x != 0 or alt_y != 0:
            return self.scene._try_move_unit(unit, alt_x, alt_y)

        return False
    
    def move_towards_target(self, unit: BattleUnit, target: BattleUnit) -> bool:
        """
        Move unit towards target using all available movement points.
        Keeps calling step_towards until out of MP or blocked (e.g. adjacent to target).
        Returns True if any movement was made.
        """
        any_moved = False
        while unit.current_movement_points > 0:
            if unit.gx == target.gx and unit.gy == target.gy:
                break
            if self.step_towards(unit, target):
                any_moved = True
            else:
                break
        return any_moved
    
    def perform_basic_attack(self, unit: BattleUnit, target: Optional[BattleUnit] = None) -> None:
        """Perform basic attack with auto-targeting (for AI and backwards compatibility)."""
        if self.scene._is_stunned(unit):
            self.scene._log(f"{unit.name} is stunned and cannot act!")
            self.scene._next_turn()
            return

        # Get weapon range (defaults to 1 for melee)
        weapon_range = self.scene.combat._get_weapon_range(unit)
        
        # Find enemies in weapon range (use Chebyshev for melee)
        is_melee = weapon_range == 1
        enemies_in_range = self.enemies_in_range(unit, weapon_range, use_chebyshev=is_melee)
        if not enemies_in_range:
            if weapon_range > 1:
                self.scene._log(f"No enemy in range! (weapon range: {weapon_range})")
            else:
                self.scene._log("No enemy in range!")
            return

        # Use provided target if valid, otherwise choose nearest
        if target and target in enemies_in_range:
            target_unit = target
        else:
            # Calculate distance for melee using Chebyshev
            is_melee = weapon_range == 1
            def distance_func(u: BattleUnit) -> int:
                if is_melee:
                    dx = abs(u.gx - unit.gx)
                    dy = abs(u.gy - unit.gy)
                    return max(dx, dy)
                else:
                    return abs(u.gx - unit.gx) + abs(u.gy - unit.gy)
            target_unit = min(enemies_in_range, key=distance_func)
        
        self.perform_basic_attack_targeted(unit, target_unit)

    def perform_basic_attack_targeted(self, unit: BattleUnit, target_unit: BattleUnit) -> None:
        """Perform basic attack on a specific target."""
        if self.scene._is_stunned(unit):
            self.scene._log(f"{unit.name} is stunned and cannot act!")
            self.scene._next_turn()
            return

        # Verify target is in range
        weapon_range = self.scene.combat._get_weapon_range(unit)
        is_melee = weapon_range == 1
        if is_melee:
            dx = abs(target_unit.gx - unit.gx)
            dy = abs(target_unit.gy - unit.gy)
            distance = max(dx, dy)
        else:
            distance = abs(target_unit.gx - unit.gx) + abs(target_unit.gy - unit.gy)
        if distance > weapon_range:
            self.scene._log(f"{target_unit.name} is out of range!")
            return
        
        # Calculate damage with falloff for ranged weapons
        base_damage = unit.attack_power
        
        # Apply damage falloff for ranged attacks at longer distances
        # At max range, deal 85% damage (slight penalty for accuracy)
        # Use Manhattan distance for falloff calculation
        if weapon_range > 1:
            manhattan_distance = abs(target_unit.gx - unit.gx) + abs(target_unit.gy - unit.gy)
            if manhattan_distance > 1:
                # Linear falloff: 100% at range 1, 85% at max range
                falloff_factor = 1.0 - (0.15 * (manhattan_distance - 1) / (weapon_range - 1))
                base_damage = int(base_damage * falloff_factor)
                base_damage = max(1, base_damage)  # Always deal at least 1 damage
        
        damage = self.scene.combat.apply_damage(unit, target_unit, base_damage, skill_id=None)
        
        # Different attack messages for ranged vs melee
        is_ranged = weapon_range > 1
        attack_verb = "shoots" if is_ranged else "hits"

        if not target_unit.is_alive:
            if not any(
                u.is_alive
                for u in (self.scene.enemy_units if unit.side == "player" else self.scene.player_units)
            ):
                if unit.side == "player":
                    self.scene.status = "victory"
                    self.scene._log(f"{unit.name} defeats the enemy party!")
                else:
                    self.scene.status = "defeat"
                    self.scene._log(f"{unit.name} destroys the last of your party!")
                return
            else:
                self.scene._log(f"{unit.name} {attack_verb} and slays {target_unit.name} ({damage} dmg).")
        else:
            self.scene._log(f"{unit.name} {attack_verb} {target_unit.name} for {damage} dmg.")

        self.scene._next_turn()
    
    def execute_ai_turn(self, unit: BattleUnit) -> None:
        """
        Execute AI turn for an enemy unit.
        
        This is the main AI decision-making logic that orchestrates all modules.
        """
        # Handle regeneration status (heal each turn)
        regen_status = next((s for s in unit.statuses if s.name == "regenerating"), None)
        if regen_status:
            heal_amount = 2
            current_hp = getattr(unit.entity, "hp", 0)
            max_hp = getattr(unit.entity, "max_hp", 1)
            new_hp = min(max_hp, current_hp + heal_amount)
            setattr(unit.entity, "hp", new_hp)
            if new_hp > current_hp:
                self.scene._log(f"{unit.name} regenerates {heal_amount} HP.")

        if self.scene._is_stunned(unit):
            self.scene._log(f"{unit.name} is stunned!")
            self.scene._next_turn()
            return

        # Calculate HP ratio for tactical decisions
        if unit.max_hp > 0:
            hp_ratio = unit.hp / float(unit.max_hp)
        else:
            hp_ratio = 1.0

        profile = self.get_ai_profile(unit)
        profile_handler = get_ai_profile_handler(profile)
        
        # Delegate to profile-specific AI handler
        profile_handler.execute_turn(unit, self, hp_ratio)
