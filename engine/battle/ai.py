"""
Battle AI module.

Handles enemy AI decision-making and turn execution.
Extracted from battle_scene.py for better code organization.
"""

from typing import List, Optional
import random

from settings import (
    BATTLE_AI_DEFENSIVE_HP_THRESHOLD,
)
from systems.statuses import StatusEffect, has_status
from systems.enemies import get_archetype
from world.entities import Enemy
from engine.battle.types import BattleUnit, Side


class BattleAI:
    """
    Handles AI decision-making for enemy units.
    
    Takes a reference to the BattleScene to access game state and execute actions.
    """
    
    def __init__(self, scene):
        """
        Initialize the AI with a reference to the battle scene.
        
        Args:
            scene: The BattleScene instance
        """
        self.scene = scene
    
    def get_ai_profile(self, unit: BattleUnit) -> str:
        """Get the AI profile for an enemy unit."""
        if isinstance(unit.entity, Enemy):
            arch_id = getattr(unit.entity, "archetype_id", None)
            if arch_id:
                try:
                    arch = get_archetype(arch_id)
                    return arch.ai_profile
                except KeyError:
                    pass
        return "brute"  # Default
    
    def choose_target_by_priority(self, unit: BattleUnit, targets: List[BattleUnit]) -> Optional[BattleUnit]:
        """Choose target based on AI profile and tactical priorities."""
        if not targets:
            return None
        
        profile = self.get_ai_profile(unit)
        
        # Skirmishers prioritize low HP targets (finish them off)
        if profile == "skirmisher":
            # Prioritize marked targets, then low HP
            marked = [t for t in targets if has_status(t.statuses, "marked")]
            if marked:
                return min(marked, key=lambda t: t.hp)
            return min(targets, key=lambda t: t.hp)
        
        # Brutes prioritize highest threat (highest attack power or HP)
        elif profile == "brute":
            # Prioritize marked targets, then highest attack
            marked = [t for t in targets if has_status(t.statuses, "marked")]
            if marked:
                return max(marked, key=lambda t: t.attack_power)
            return max(targets, key=lambda t: t.attack_power)
        
        # Casters prioritize debuffed targets or low HP
        elif profile == "caster":
            # Prioritize marked/cursed targets, then low HP
            debuffed = [t for t in targets if has_status(t.statuses, "marked") or has_status(t.statuses, "cursed")]
            if debuffed:
                return min(debuffed, key=lambda t: t.hp)
            return min(targets, key=lambda t: t.hp)
        
        # Default: nearest target
        return min(targets, key=lambda t: abs(t.gx - unit.gx) + abs(t.gy - unit.gy))
    
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
        """
        Backwards-compatible helper: enemies at distance 1 (using Chebyshev for 8-directional).
        """
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
        
        damage = self.scene.combat.apply_damage(unit, target_unit, base_damage)
        
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
        This is the main AI decision-making logic.
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
        weapon_range = self.scene.combat._get_weapon_range(unit)
        is_ranged = weapon_range > 1
        is_melee = weapon_range == 1

        # --- Support AI: Heal/Buff Allies (for Support/Caster profiles) ---
        if profile in ("caster", "support") or "heal_ally" in unit.skills or "buff_ally" in unit.skills:
            # Check for heal_ally skill
            heal_skill = unit.skills.get("heal_ally")
            if heal_skill:
                cd = unit.cooldowns.get(heal_skill.id, 0)
                if cd == 0:
                    injured_ally = self.find_injured_ally(unit, max_range=1)
                    if injured_ally and random.random() < 0.6:  # 60% chance to heal if ally injured
                        # Heal for 30% of ally's max HP
                        heal_amount = max(1, int(injured_ally.max_hp * 0.3))
                        current_hp = getattr(injured_ally.entity, "hp", 0)
                        max_hp = getattr(injured_ally.entity, "max_hp", 1)
                        new_hp = min(max_hp, current_hp + heal_amount)
                        setattr(injured_ally.entity, "hp", new_hp)
                        unit.cooldowns[heal_skill.id] = heal_skill.cooldown
                        self.scene._log(f"{unit.name} heals {injured_ally.name} for {heal_amount} HP.")
                        self.scene._next_turn()
                        return
            
            # Check for buff_ally skill
            buff_skill = unit.skills.get("buff_ally")
            if buff_skill:
                cd = unit.cooldowns.get(buff_skill.id, 0)
                if cd == 0:
                    ally_to_buff = self.find_ally_to_buff(unit, max_range=1)
                    if ally_to_buff and random.random() < 0.5:  # 50% chance to buff
                        self.scene._use_skill_targeted(unit, buff_skill, ally_to_buff, for_ai=True)
                        return

        # --- Defensive Skills (when low HP or berserker rage) ---
        # Only use defensive skills when actually needed (low HP), not every turn
        if hp_ratio < BATTLE_AI_DEFENSIVE_HP_THRESHOLD or (hp_ratio < 0.3 and "berserker_rage" in unit.skills):
            # Prioritize berserker_rage when very low HP (80% chance)
            if hp_ratio < 0.3:
                rage_skill = unit.skills.get("berserker_rage")
                if rage_skill:
                    cd = unit.cooldowns.get(rage_skill.id, 0)
                    can_use, _ = unit.has_resources_for_skill(rage_skill)
                    if cd == 0 and can_use and random.random() < 0.8:
                        if self.scene._use_skill(unit, rage_skill, for_ai=True):
                            return
            
            # Other defensive self-buffs (exclude guard - it's too basic, only use when very low HP)
            defensive_skills = [
                s for s in unit.skills.values()
                if s.target_mode == "self" 
                and s.id not in ("berserker_rage", "regeneration", "guard")
            ]
            for skill in defensive_skills:
                cd = unit.cooldowns.get(skill.id, 0)
                can_use, _ = unit.has_resources_for_skill(skill)
                if cd == 0 and can_use and random.random() < 0.7:
                    if self.scene._use_skill(unit, skill, for_ai=True):
                        return
            
            # Guard only when very low HP (<30%) and no other defensive options
            if hp_ratio < 0.3:
                guard_skill = unit.skills.get("guard")
                if guard_skill:
                    cd = unit.cooldowns.get(guard_skill.id, 0)
                    can_use, _ = unit.has_resources_for_skill(guard_skill)
                    if cd == 0 and can_use and random.random() < 0.5:
                        if self.scene._use_skill(unit, guard_skill, for_ai=True):
                            return

        # --- Regeneration skill (use when below 50% HP, 70% chance) ---
        regen_skill = unit.skills.get("regeneration")
        if regen_skill and hp_ratio < 0.5:
            cd = unit.cooldowns.get(regen_skill.id, 0)
            if cd == 0 and not has_status(unit.statuses, "regenerating"):
                if random.random() < 0.7:
                    if self.scene._use_skill(unit, regen_skill, for_ai=True):
                        return

        # --- Fear Scream (AoE stun) ---
        fear_skill = unit.skills.get("fear_scream")
        if fear_skill:
            cd = unit.cooldowns.get(fear_skill.id, 0)
            if cd == 0:
                nearby_enemies = self.enemies_in_range(unit, 1)
                if nearby_enemies and random.random() < 0.4:  # 40% chance to use fear
                    # Apply stun to all adjacent enemies
                    for enemy in nearby_enemies:
                        self.scene._add_status(enemy, StatusEffect(
                            name="stunned",
                            duration=1,
                            stunned=True,
                        ))
                    unit.cooldowns[fear_skill.id] = fear_skill.cooldown
                    self.scene._log(f"{unit.name} screams in terror, stunning nearby enemies!")
                    self.scene._next_turn()
                    return

        # --- Offensive Skills (with tactical targeting) ---
        offensive_skills = [
            s for s in unit.skills.values()
            if s.target_mode == "adjacent_enemy" and s.base_power > 0.0
        ]
        # Prioritize mark_target and debuff skills
        priority_skills = [s for s in offensive_skills if s.id in ("mark_target", "dark_hex", "crippling_blow")]
        other_skills = [s for s in offensive_skills if s.id not in ("mark_target", "dark_hex", "crippling_blow")]
        
        # Try priority skills first (higher chance to use)
        for skill in priority_skills:
            max_range = int(getattr(skill, "range_tiles", 1) or 1)
            use_chebyshev = getattr(skill, "range_metric", "chebyshev") == "chebyshev"
            targets_for_skill = self.enemies_in_range(unit, max_range, use_chebyshev=use_chebyshev)
            if not targets_for_skill:
                continue
            
            cd = unit.cooldowns.get(skill.id, 0)
            can_use, _ = unit.has_resources_for_skill(skill)
            if cd == 0 and can_use:
                # Higher chance to use debuff/mark skills (70% for mark, 60% for debuffs)
                chance = 0.7 if skill.id == "mark_target" else 0.6
                if random.random() < chance:
                    target = self.choose_target_by_priority(unit, targets_for_skill)
                    if target:
                        if self.scene._use_skill_targeted(unit, skill, target, for_ai=True):
                            return
        
        # Then try other offensive skills (increased chance: 60% instead of 40%)
        random.shuffle(other_skills)
        for skill in other_skills:
            max_range = int(getattr(skill, "range_tiles", 1) or 1)
            use_chebyshev = getattr(skill, "range_metric", "chebyshev") == "chebyshev"
            targets_for_skill = self.enemies_in_range(unit, max_range, use_chebyshev=use_chebyshev)
            if not targets_for_skill:
                continue

            cd = unit.cooldowns.get(skill.id, 0)
            can_use, _ = unit.has_resources_for_skill(skill)
            if cd == 0 and can_use:
                # Special handling for life_drain (higher priority when low HP)
                if skill.id == "life_drain":
                    chance = 0.7 if hp_ratio < 0.5 else 0.5
                    if random.random() < chance:
                        target = self.choose_target_by_priority(unit, targets_for_skill)
                        if target:
                            if self.scene._use_skill_targeted(unit, skill, target, for_ai=True):
                                return
                # Poison strike and disease strike: use more often (60%)
                elif skill.id in ("poison_strike", "disease_strike"):
                    if random.random() < 0.6:
                        target = self.choose_target_by_priority(unit, targets_for_skill)
                        if target:
                            if self.scene._use_skill_targeted(unit, skill, target, for_ai=True):
                                return
                # Other offensive skills: 55% chance (increased from 40%)
                else:
                    if random.random() < 0.55:
                        target = self.choose_target_by_priority(unit, targets_for_skill)
                        if target:
                            if self.scene._use_skill_targeted(unit, skill, target, for_ai=True):
                                return

        # --- Basic Attack (with tactical targeting) ---
        # Use basic attack if we're in range and no skills were used above
        enemies_in_weapon_range = self.enemies_in_range(unit, weapon_range, use_chebyshev=is_melee)
        if enemies_in_weapon_range:
            target = self.choose_target_by_priority(unit, enemies_in_weapon_range)
            if target:
                self.perform_basic_attack(unit, target=target)
                return

        # --- Movement (tactical positioning based on role) ---
        target = self.nearest_target(unit, "player")
        if target is None:
            self.scene.status = "victory"
            self.scene._log("The foes scatter.")
            return

        profile = self.get_ai_profile(unit)
        # Use Chebyshev distance for movement calculations (allows diagonal)
        dx = abs(target.gx - unit.gx)
        dy = abs(target.gy - unit.gy)
        distance = max(dx, dy)

        # For ranged units, try to maintain optimal distance
        if is_ranged:
            if distance <= 1:
                # Back away from melee range
                dx = unit.gx - target.gx
                dy = unit.gy - target.gy
                if dx != 0 or dy != 0:
                    step_x = 0
                    step_y = 0
                    if abs(dx) >= abs(dy) and dx != 0:
                        step_x = 1 if dx > 0 else -1
                    elif dy != 0:
                        step_y = 1 if dy > 0 else -1
                    
                    if step_x != 0 or step_y != 0:
                        if self.scene._try_move_unit(unit, step_x, step_y):
                            self.scene._log(f"{unit.name} backs away.")
            elif distance > weapon_range:
                # Move closer if out of range
                moved = self.step_towards(unit, target)
                if moved:
                    self.scene._log(f"{unit.name} advances.")
                else:
                    self.scene._log(f"{unit.name} hesitates.")
            else:
                # In optimal range, reposition slightly
                moved = self.step_towards(unit, target)
                if moved:
                    self.scene._log(f"{unit.name} repositions.")
                else:
                    self.scene._log(f"{unit.name} hesitates.")
        else:
            # Melee units: tactical movement based on role
            if profile == "caster" or profile == "support":
                # Casters/support: try to maintain distance, only close if necessary
                if distance > 2:
                    # Too far, move closer
                    moved = self.step_towards(unit, target)
                    if moved:
                        self.scene._log(f"{unit.name} advances cautiously.")
                    else:
                        self.scene._log(f"{unit.name} hesitates.")
                elif distance == 2:
                    # Good distance for casting, maybe reposition laterally
                    # Try to move sideways if possible
                    dx = target.gx - unit.gx
                    dy = target.gy - unit.gy
                    # Try moving perpendicular to target
                    if abs(dx) >= abs(dy):
                        # Move vertically
                        if self.scene._try_move_unit(unit, 0, 1) or self.scene._try_move_unit(unit, 0, -1):
                            self.scene._log(f"{unit.name} repositions.")
                    else:
                        # Move horizontally
                        if self.scene._try_move_unit(unit, 1, 0) or self.scene._try_move_unit(unit, -1, 0):
                            self.scene._log(f"{unit.name} repositions.")
                    # If can't reposition, just advance
                    moved = self.step_towards(unit, target)
                    if moved:
                        self.scene._log(f"{unit.name} advances.")
                    else:
                        self.scene._log(f"{unit.name} hesitates.")
                else:
                    # Already close, just advance
                    moved = self.step_towards(unit, target)
                    if moved:
                        self.scene._log(f"{unit.name} advances.")
                    else:
                        self.scene._log(f"{unit.name} hesitates.")
            elif profile == "skirmisher":
                # Skirmishers: cautious approach, try to flank
                if distance > 1:
                    # Try to find a flanking position
                    dx = target.gx - unit.gx
                    dy = target.gy - unit.gy
                    
                    # Check if we can move to a flanking position
                    # Try positions adjacent to target that would be flanks
                    flank_positions = [
                        (target.gx + 1, target.gy),  # Right
                        (target.gx - 1, target.gy),  # Left
                        (target.gx, target.gy + 1),  # Down
                        (target.gx, target.gy - 1),  # Up
                    ]
                    
                    # Shuffle to randomize which flank we try
                    random.shuffle(flank_positions)
                    
                    for fx, fy in flank_positions:
                        # Check if this would be a flanking position
                        test_unit = BattleUnit(entity=unit.entity, side=unit.side, gx=fx, gy=fy, name=unit.name)
                        if self.scene.combat.is_flanking(test_unit, target):
                            # Try to move towards this flanking position
                            move_dx = fx - unit.gx
                            move_dy = fy - unit.gy
                            # Normalize to single step
                            if abs(move_dx) > 0:
                                move_dx = 1 if move_dx > 0 else -1
                            if abs(move_dy) > 0:
                                move_dy = 1 if move_dy > 0 else -1
                            
                            if self.scene._try_move_unit(unit, move_dx, move_dy):
                                self.scene._log(f"{unit.name} maneuvers for a flank.")
                    
                    # If no flanking position available, normal approach
                    moved = self.step_towards(unit, target)
                    if moved:
                        self.scene._log(f"{unit.name} advances.")
                    else:
                        self.scene._log(f"{unit.name} hesitates.")
                else:
                    # Already adjacent - check if we're flanking, if not try to reposition
                    if not self.scene.combat.is_flanking(unit, target):
                        # Try to move to a flanking position
                        flank_positions = [
                            (target.gx + 1, target.gy),
                            (target.gx - 1, target.gy),
                            (target.gx, target.gy + 1),
                            (target.gx, target.gy - 1),
                        ]
                        random.shuffle(flank_positions)
                        for fx, fy in flank_positions:
                            test_unit = BattleUnit(entity=unit.entity, side=unit.side, gx=fx, gy=fy, name=unit.name)
                            if self.scene.combat.is_flanking(test_unit, target) and not self.scene._cell_blocked(fx, fy):
                                move_dx = fx - unit.gx
                                move_dy = fy - unit.gy
                                if abs(move_dx) > 0:
                                    move_dx = 1 if move_dx > 0 else -1
                                if abs(move_dy) > 0:
                                    move_dy = 1 if move_dy > 0 else -1
                                if self.scene._try_move_unit(unit, move_dx, move_dy):
                                    self.scene._log(f"{unit.name} repositions for a flank.")
                    
                    # Already in good position or can't flank
                    moved = self.step_towards(unit, target)
                    if moved:
                        self.scene._log(f"{unit.name} repositions.")
                    else:
                        self.scene._log(f"{unit.name} holds position.")
            else:
                # Brutes: direct charge forward
                moved = self.step_towards(unit, target)

                # If we couldn't advance directly (often because an ally is blocking),
                # try a simple sidestep to work around the obstruction.
                if not moved:
                    dx = target.gx - unit.gx
                    dy = target.gy - unit.gy

                    # Decide whether we're mostly approaching horizontally or vertically
                    if abs(dx) >= abs(dy):
                        # Target is mostly to the left/right – try stepping up or down
                        if self.scene._try_move_unit(unit, 0, -1) or self.scene._try_move_unit(unit, 0, 1):
                            moved = True
                    else:
                        # Target is mostly above/below – try stepping left or right
                        if self.scene._try_move_unit(unit, -1, 0) or self.scene._try_move_unit(unit, 1, 0):
                            moved = True

                if moved:
                    self.scene._log(f"{unit.name} charges forward.")
                else:
                    self.scene._log(f"{unit.name} hesitates.")
        
        # AI can use remaining movement points for additional movement
        # Try to move closer if we have movement points remaining
        if unit.current_movement_points > 0:
            dx = abs(target.gx - unit.gx)
            dy = abs(target.gy - unit.gy)
            distance = max(dx, dy)
            if distance > 1:
                # Continue moving towards target until movement points are exhausted
                while unit.current_movement_points > 0:
                    moved = self.step_towards(unit, target)
                    if not moved:
                        # Can't move further (blocked, no path, etc.)
                        break
                    dx = abs(target.gx - unit.gx)
                    dy = abs(target.gy - unit.gy)
                    distance = max(dx, dy)
                    if distance <= 1:
                        # Reached target, no need to continue moving
                        break
                # Continue moving towards target until movement points are exhausted
                while unit.current_movement_points > 0:
                    moved = self.step_towards(unit, target)
                    if not moved:
                        # Can't move further (blocked, no path, etc.)
                        break

        self.scene._next_turn()

