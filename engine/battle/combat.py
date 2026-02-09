"""
Battle combat calculations module.

Handles all combat-related calculations: damage, crits, flanking, cover, etc.
Extracted from battle_scene.py for better code organization.
"""

from typing import Optional, Tuple
import random

from settings import (
    BASE_CRIT_CHANCE,
    CRIT_DAMAGE_MULTIPLIER,
    COVER_DAMAGE_REDUCTION,
    FLANKING_DAMAGE_BONUS,
    DEFAULT_MIN_SKILL_POWER,
)
from systems.statuses import outgoing_multiplier, incoming_multiplier
from engine.battle.types import BattleUnit
from systems.enemies import get_archetype


def _get_distance(gx1: int, gy1: int, gx2: int, gy2: int, use_chebyshev: bool = False) -> int:
    """
    Calculate distance between two grid positions.
    
    Args:
        gx1, gy1: First position
        gx2, gy2: Second position
        use_chebyshev: If True, use Chebyshev distance (for melee/8-directional).
                      If False, use Manhattan distance (for ranged/4-directional).
    
    Returns:
        Distance in tiles
    """
    dx = abs(gx1 - gx2)
    dy = abs(gy1 - gy2)
    
    if use_chebyshev:
        # Chebyshev distance: max(dx, dy) - allows diagonal movement
        return max(dx, dy)
    else:
        # Manhattan distance: dx + dy - standard for ranged attacks
        return dx + dy


class BattleCombat:
    """
    Handles combat calculations for the battle scene.
    
    Takes a reference to the BattleScene to access terrain and unit information.
    """
    
    def __init__(self, scene):
        """
        Initialize the combat calculator with a reference to the battle scene.
        
        Args:
            scene: The BattleScene instance
        """
        self.scene = scene
    
    def is_flanking(self, attacker: BattleUnit, target: BattleUnit) -> bool:
        """
        Check if attacker is flanking the target.
        Flanking occurs when attacking from behind or the side.
        Updated for 8-directional: checks if attacker is adjacent (orthogonal or diagonal)
        and there's no ally directly opposite.
        """
        dx = attacker.gx - target.gx
        dy = attacker.gy - target.gy
        
        # Must be directly adjacent for flanking (orthogonal or diagonal, distance 1 using Chebyshev)
        distance = _get_distance(attacker.gx, attacker.gy, target.gx, target.gy, use_chebyshev=True)
        if distance != 1:
            return False
        
        # Check if there's an ally directly opposite the attacker (target would be "facing" that way)
        target_allies = self.scene.player_units if target.side == "player" else self.scene.enemy_units
        opposite_dx = -dx
        opposite_dy = -dy
        
        for ally in target_allies:
            if ally is target or not ally.is_alive:
                continue
            ally_dx = ally.gx - target.gx
            ally_dy = ally.gy - target.gy
            # If ally is directly opposite attacker, target is facing that direction (not a flank)
            # Check using Chebyshev distance to allow diagonal opposites
            if abs(ally_dx) <= 1 and abs(ally_dy) <= 1:
                # Normalize to direction
                if ally_dx != 0:
                    ally_dx_sign = 1 if ally_dx > 0 else -1
                else:
                    ally_dx_sign = 0
                if ally_dy != 0:
                    ally_dy_sign = 1 if ally_dy > 0 else -1
                else:
                    ally_dy_sign = 0
                
                # Check if opposite direction (or same direction, which also protects)
                if (ally_dx_sign == opposite_dx or (opposite_dx == 0 and ally_dx_sign == 0)) and \
                   (ally_dy_sign == opposite_dy or (opposite_dy == 0 and ally_dy_sign == 0)):
                    return False
        
        # No ally opposite attacker, so it's a flank
        return True
    
    def has_cover(self, attacker: BattleUnit, target: BattleUnit) -> bool:
        """
        Check if target has cover from attacker (for ranged attacks).
        Cover applies if target is on cover terrain or has cover between attacker and target.
        """
        # Check if target is on cover terrain
        target_terrain = self.scene.terrain_manager.get_terrain(target.gx, target.gy)
        if target_terrain.provides_cover:
            return True
        
        # Check for cover between attacker and target (simplified line-of-sight check)
        # For now, just check if target is on cover terrain
        # Future: could check Bresenham line for cover terrain
        
        return False
    
    def _get_damage_type(self, attacker: BattleUnit, skill_id: Optional[str] = None) -> str:
        """
        Determine damage type from skill or attack.
        Returns: "fire", "ice", "poison", "magic", or "physical" (default)
        """
        if skill_id:
            # Map skill IDs to damage types
            fire_skills = ["fireball", "flame_wall", "ignite"]
            ice_skills = ["ice_bolt", "frost_nova", "freeze"]
            poison_skills = ["poison_strike", "disease_strike", "venom_blast"]
            magic_skills = ["dark_hex", "lightning_bolt", "magic_missile", "void_bolt"]
            
            if skill_id in fire_skills:
                return "fire"
            elif skill_id in ice_skills:
                return "ice"
            elif skill_id in poison_skills:
                return "poison"
            elif skill_id in magic_skills:
                return "magic"
        
        # Default to physical for basic attacks
        return "physical"
    
    def _get_resistance_multiplier(self, target: BattleUnit, damage_type: str) -> float:
        """
        Get resistance multiplier for damage type.
        Returns: 0.0 = immune, 0.5 = 50% damage, 1.0 = normal, 1.5 = 150% (weakness)
        """
        # Check if target has resistances from archetype
        arch_id = getattr(target.entity, "archetype_id", None)
        if arch_id:
            try:
                arch = get_archetype(arch_id)
                if hasattr(arch, "resistances") and arch.resistances:
                    return arch.resistances.get(damage_type, 1.0)
            except (KeyError, AttributeError):
                pass
        
        # Default: no resistance
        return 1.0
    
    def calculate_damage(self, attacker: BattleUnit, target: BattleUnit, base_damage: int, is_crit: bool = False, skill_id: Optional[str] = None) -> int:
        """
        Calculate damage that would be dealt without actually applying it.
        Useful for previews.
        """
        damage = int(base_damage * self._outgoing_multiplier(attacker))
        damage = int(damage * self._incoming_multiplier(target))
        
        # Apply resistance/weakness based on damage type
        damage_type = self._get_damage_type(attacker, skill_id)
        resistance_mult = self._get_resistance_multiplier(target, damage_type)
        damage = int(damage * resistance_mult)
        
        # Log resistance messages (only for significant changes)
        if resistance_mult == 0.0:
            # Will be logged in apply_damage
            pass
        elif resistance_mult < 0.7:
            # Strong resistance
            pass
        elif resistance_mult > 1.3:
            # Weakness
            pass
        
        # Apply flanking bonus (melee attacks only)
        weapon_range = self._get_weapon_range(attacker)
        if weapon_range == 1 and self.is_flanking(attacker, target):
            damage = int(damage * FLANKING_DAMAGE_BONUS)
        
        # Apply cover reduction (ranged attacks only)
        if weapon_range > 1 and self.has_cover(attacker, target):
            damage = int(damage * COVER_DAMAGE_REDUCTION)
        
        # Apply critical hit multiplier
        if is_crit:
            damage = int(damage * CRIT_DAMAGE_MULTIPLIER)
        
        defense = int(getattr(target.entity, "defense", 0))
        damage = max(1, damage - max(0, defense))
        
        return damage
    
    def apply_damage(self, attacker: BattleUnit, target: BattleUnit, base_damage: int, skill_id: Optional[str] = None) -> int:
        """
        Apply damage from attacker to target, respecting statuses and defenses.
        Returns the actual damage dealt.
        
        Args:
            attacker: Unit dealing damage
            target: Unit receiving damage
            base_damage: Base damage amount
            skill_id: Optional skill ID for damage type determination
        """
        # Check for dodge first (before any damage calculations)
        dodge_chance = float(getattr(target.entity, "dodge_chance", 0.0))
        if dodge_chance > 0.0 and random.random() < dodge_chance:
            self.scene._log(f"{target.name} dodges the attack!")
            # Add miss effect at target position
            target_x = self.scene.grid_origin_x + target.gx * self.scene.cell_size + self.scene.cell_size // 2
            target_y = self.scene.grid_origin_y + target.gy * self.scene.cell_size + self.scene.cell_size // 2
            self.scene._hit_sparks.append({
                "x": target_x,
                "y": target_y,
                "timer": 0.3,
                "is_crit": False,
                "is_dodge": True,  # Flag for rendering dodge effect
            })
            return 0  # No damage dealt
        
        # Determine damage type and check resistances
        damage_type = self._get_damage_type(attacker, skill_id)
        resistance_mult = self._get_resistance_multiplier(target, damage_type)
        
        # Log resistance messages
        if resistance_mult == 0.0:
            self.scene._log(f"{target.name} is immune to {damage_type} damage!")
        elif resistance_mult < 0.7:
            self.scene._log(f"{target.name} resists {damage_type} damage!")
        elif resistance_mult > 1.3:
            self.scene._log(f"{target.name} is weak to {damage_type} damage!")
        
        # Roll for critical hit
        is_crit = self._roll_critical_hit()
        
        # Check for flanking and cover
        weapon_range = self._get_weapon_range(attacker)
        is_flanking = weapon_range == 1 and self.is_flanking(attacker, target)
        has_cover = weapon_range > 1 and self.has_cover(attacker, target)
        
        damage = self.calculate_damage(attacker, target, base_damage, is_crit=is_crit, skill_id=skill_id)
        
        # Log flanking/cover messages
        if is_flanking:
            self.scene._log(f"{attacker.name} flanks {target.name}!")
        if has_cover:
            self.scene._log(f"{target.name} takes cover!")
        
        # Handle counter attack (if target has counter_stance status)
        counter_status = next((s for s in target.statuses if s.name == "counter_stance"), None)
        if counter_status and attacker.side != target.side:
            # Counter attack deals 1.5x damage back
            counter_damage = max(1, int(damage * 1.5))
            current_hp = getattr(attacker.entity, "hp", 0)
            setattr(attacker.entity, "hp", max(0, current_hp - counter_damage))
            self.scene._log(f"{target.name} counters for {counter_damage} damage!")
            # Remove counter status after use
            target.statuses.remove(counter_status)
        
        # Add hit spark effect at target position
        target_x = self.scene.grid_origin_x + target.gx * self.scene.cell_size + self.scene.cell_size // 2
        target_y = self.scene.grid_origin_y + target.gy * self.scene.cell_size + self.scene.cell_size // 2
        self.scene._hit_sparks.append({
            "x": target_x,
            "y": target_y,
            "timer": 0.3,  # Short spark animation
            "is_crit": is_crit,
        })
        
        # Add visual effects
        self.scene.visual_effects.add_hit_particles(
            target_x, target_y,
            count=10 if is_crit else 6,
            is_crit=is_crit,
        )
        
        # Screen shake based on damage
        if damage >= 20:
            shake_intensity = min(8.0, damage / 5.0)
            self.scene.visual_effects.add_screen_shake(shake_intensity, 0.3)
        elif is_crit:
            self.scene.visual_effects.add_screen_shake(5.0, 0.25)
        
        # Screen flash for crits
        if is_crit:
            self.scene.visual_effects.add_screen_flash((255, 255, 150), 0.2, 80.0)
        
        current_hp = getattr(target.entity, "hp", 0)
        was_alive = current_hp > 0
        setattr(target.entity, "hp", max(0, current_hp - damage))
        is_kill = was_alive and getattr(target.entity, "hp", 0) <= 0
        
        # Quest progress: kill objectives
        if is_kill and target.side == "enemy":
            arch_id = getattr(target.entity, "archetype_id", None)
            if arch_id and hasattr(self.scene, "game") and self.scene.game is not None:
                try:
                    from systems.quests import update_quest_progress
                    update_quest_progress(self.scene.game, "kill", target_id=arch_id, amount=1)
                except Exception:
                    pass
        
        # Update health bar target for smooth animation
        new_hp_ratio = getattr(target.entity, "hp", 0) / target.max_hp if target.max_hp > 0 else 0.0
        self.scene.visual_effects.set_health_bar_target(target, new_hp_ratio)
        
        # Store damage for floating number display
        # Increased duration: crits 2.0s, normal 1.8s (was 1.2s and 1.0s)
        self.scene._floating_damage.append({
            "target": target,
            "damage": damage,
            "timer": 2.0 if is_crit else 1.8,  # Longer duration for better visibility
            "y_offset": 0,
            "is_crit": is_crit,
            "is_kill": is_kill,
        })
        
        return damage
    
    def get_damage_preview(self, unit: BattleUnit, target: BattleUnit) -> Tuple[Optional[int], Optional[int]]:
        """
        Calculate and return the damage range that would be dealt by the current action.
        Returns (normal_damage, crit_damage) tuple, or (None, None) if no valid preview.
        """
        if self.scene.targeting_mode is None:
            return None, None
        
        action_type = self.scene.targeting_mode.get("action_type")
        skill = self.scene.targeting_mode.get("skill")
        base_damage = None
        
        if action_type == "attack":
            weapon_range = self._get_weapon_range(unit)
            # Use Chebyshev distance for melee (range 1), Manhattan for ranged
            is_melee = weapon_range == 1
            distance = _get_distance(unit.gx, unit.gy, target.gx, target.gy, use_chebyshev=is_melee)
            
            if distance > weapon_range:
                return None, None
            
            base_damage = unit.attack_power
            
            # Apply damage falloff for ranged attacks (using Manhattan distance)
            if weapon_range > 1:
                manhattan_distance = _get_distance(unit.gx, unit.gy, target.gx, target.gy, use_chebyshev=False)
                if manhattan_distance > 1:
                    falloff_factor = 1.0 - (0.15 * (manhattan_distance - 1) / (weapon_range - 1))
                    base_damage = int(base_damage * falloff_factor)
                    base_damage = max(1, base_damage)
        
        elif action_type == "skill" and skill is not None:
            if skill.base_power <= 0:
                return None, None  # Non-damage skill
            
            max_range = int(getattr(skill, "range_tiles", 1) or 1)
            use_chebyshev = getattr(skill, "range_metric", "chebyshev") == "chebyshev"
            distance = _get_distance(unit.gx, unit.gy, target.gx, target.gy, use_chebyshev=use_chebyshev)
            
            if distance > max_range:
                return None, None
            
            base = unit.attack_power
            dmg = base * skill.base_power
            if skill.uses_skill_power:
                sp = float(getattr(unit.entity, "skill_power", 1.0))
                dmg *= max(DEFAULT_MIN_SKILL_POWER, sp)
            
            base_damage = int(dmg)
        
        if base_damage is None:
            return None, None
        
        normal_damage = self.calculate_damage(unit, target, base_damage, is_crit=False)
        crit_damage = self.calculate_damage(unit, target, base_damage, is_crit=True)
        
        return normal_damage, crit_damage
    
    def _outgoing_multiplier(self, unit: BattleUnit) -> float:
        """Get outgoing damage multiplier from statuses."""
        return outgoing_multiplier(unit.statuses)
    
    def _incoming_multiplier(self, unit: BattleUnit) -> float:
        """Get incoming damage multiplier from statuses."""
        return incoming_multiplier(unit.statuses)
    
    def _roll_critical_hit(self) -> bool:
        """Roll for a critical hit based on base crit chance."""
        return random.random() < BASE_CRIT_CHANCE
    
    def _get_weapon_range(self, unit: BattleUnit) -> int:
        """
        Get the weapon range for a unit. Returns 1 for melee weapons (default).
        
        For player: checks equipped weapon in game inventory.
        For companions: checks equipped weapon in companion state.
        For enemies: checks weapon_range attribute or archetype.
        """
        from systems.inventory import get_item_def
        from world.entities import Player, Enemy
        
        # Default melee range
        default_range = 1
        
        # Check if it's a player entity
        if isinstance(unit.entity, Player) and unit.entity is self.scene.player:
            # Hero: get weapon from game inventory
            if self.scene.game is not None:
                inventory = getattr(self.scene.game, "inventory", None)
                if inventory is not None:
                    weapon_id = inventory.equipped.get("weapon")
                    if weapon_id:
                        try:
                            weapon_def = get_item_def(weapon_id)
                            if weapon_def:
                                range_val = weapon_def.stats.get("range")
                                if range_val is not None:
                                    return int(range_val)
                        except (KeyError, AttributeError):
                            pass
        
        # Check if it's a companion (companions are also Player entities but different instances)
        # Since only one companion is used in battle, check the first companion in party
        if self.scene.game is not None and unit.side == "player" and unit.entity is not self.scene.player:
            party = getattr(self.scene.game, "party", None) or []
            if party:
                # Check first companion's equipment (only one companion is used in battle)
                comp_state = party[0]
                if hasattr(comp_state, "equipped"):
                    comp_weapon_id = comp_state.equipped.get("weapon")
                    if comp_weapon_id:
                        try:
                            weapon_def = get_item_def(comp_weapon_id)
                            if weapon_def:
                                range_val = weapon_def.stats.get("range")
                                if range_val is not None:
                                    return int(range_val)
                        except (KeyError, AttributeError):
                            pass
        
        # For enemies, check weapon_range attribute or archetype
        if isinstance(unit.entity, Enemy):
            # Check direct attribute first
            if hasattr(unit.entity, "weapon_range"):
                return int(getattr(unit.entity, "weapon_range", default_range))
            
            # Check archetype for weapon info
            arch_id = getattr(unit.entity, "archetype_id", None)
            if arch_id:
                from systems.enemies import get_archetype
                try:
                    arch = get_archetype(arch_id)
                    if hasattr(arch, "weapon_range"):
                        return int(getattr(arch, "weapon_range", default_range))
                except (KeyError, AttributeError):
                    pass
        
        return default_range

