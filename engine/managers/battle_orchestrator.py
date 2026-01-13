"""
Battle orchestration system.

Handles battle initiation, encounter group building, and reward calculation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
import random

from settings import TILE_SIZE
from world.entities import Enemy, Player
from world.game_map import GameMap
from ..battle import BattleScene
from systems.loot import roll_battle_loot, roll_battle_consumable, roll_battle_loot_multiple, roll_boss_loot

if TYPE_CHECKING:
    from ..core.game import Game


class BattleOrchestrator:
    """
    Orchestrates battles: building encounter groups and calculating rewards.
    
    Responsibilities:
    - Build encounter groups from nearby enemies
    - Start battles with encounter groups
    - Calculate battle rewards (gold, items)
    """
    
    @staticmethod
    def build_encounter_group(
        trigger_enemy: Enemy,
        game_map: GameMap,
        player: Player,
        max_group_size: int = 6,
        radius: int = TILE_SIZE * 5,
    ) -> List[Enemy]:
        """
        Build an encounter group around the trigger enemy.
        
        Args:
            trigger_enemy: The enemy that triggered the battle
            game_map: The current game map
            player: The player entity
            max_group_size: Maximum number of enemies in the encounter
            radius: Radius to search for nearby enemies (in pixels)
        
        Returns:
            List of Enemy entities for the encounter
        """
        group: List[Enemy] = []
        
        # Always include the enemy that triggered the battle
        if trigger_enemy in game_map.entities:
            group.append(trigger_enemy)
        
        # Add other nearby enemies within a radius
        px, py = player.rect.center
        
        for entity in list(game_map.entities):
            if not isinstance(entity, Enemy):
                continue
            if entity is trigger_enemy:
                continue
            ex, ey = entity.rect.center
            dx = ex - px
            dy = ey - py
            if dx * dx + dy * dy <= radius * radius:
                group.append(entity)
        
        # Limit how many can join a single battle (for sanity)
        return group[:max_group_size]
    
    @staticmethod
    def calculate_battle_rewards(
        floor: int,
        hero_stats: "HeroStats",
        inventory: Optional["Inventory"] = None,
        encounter_enemies: Optional[List[Enemy]] = None,
    ) -> List[str]:
        """
        Calculate and award rewards after a battle victory.
        
        Args:
            floor: Current floor number (affects reward amounts)
            hero_stats: Hero stats object for adding gold
            inventory: Inventory object for adding items (optional)
            encounter_enemies: List of enemies in the encounter (for boss detection and size)
        
        Returns:
            List of message strings describing rewards
        """
        messages: List[str] = []
        
        try:
            # Check if this was a boss battle
            is_boss = False
            is_final_boss = False
            encounter_size = 1
            
            if encounter_enemies:
                encounter_size = len(encounter_enemies)
                # Check for bosses
                for enemy in encounter_enemies:
                    if getattr(enemy, "is_boss", False):
                        is_boss = True
                        if getattr(enemy, "is_final_boss", False):
                            is_final_boss = True
                        break
            
            # --- Gold pouch ---
            # Enemies on deeper floors give more gold
            # Bosses give more gold
            gold_multiplier = 2.0 if is_final_boss else (1.5 if is_boss else 1.0)
            base_min_gold = int((3 + floor) * gold_multiplier)
            base_max_gold = int((6 + floor * 2) * gold_multiplier)
            
            gold_amount = random.randint(base_min_gold, base_max_gold)
            if hasattr(hero_stats, "add_gold"):
                gained_gold = hero_stats.add_gold(gold_amount)
            else:
                gained_gold = gold_amount
            
            if gained_gold > 0:
                messages.append(f"You pick up a pouch of {gained_gold} gold.")
            
            # --- Loot drops ---
            if inventory is not None:
                loot_items: List[str] = []
                
                if is_boss:
                    # Bosses use special loot function (guaranteed drops)
                    loot_items = roll_boss_loot(floor, is_final_boss=is_final_boss)
                else:
                    # Regular battles: multiple drops for larger encounters
                    # Base 1 drop, +1 for every 3 enemies
                    num_drops = 1 + (encounter_size - 1) // 3
                    num_drops = min(num_drops, 3)  # Cap at 3 drops
                    
                    loot_items = roll_battle_loot_multiple(floor, num_drops=num_drops, encounter_size=encounter_size)
                    
                    # Consumable drop (separate from equipment)
                    consumable_id = roll_battle_consumable(floor)
                    if consumable_id is not None:
                        loot_items.append(consumable_id)
                
                # Add all loot to inventory
                if loot_items:
                    item_names = []
                    for item_id in loot_items:
                        try:
                            # Determine if it's a consumable or equipment
                            from systems.inventory import get_item_def
                            item_def = get_item_def(item_id)
                            
                            if item_def is None:
                                continue  # Skip invalid items
                            
                            # Add to inventory with appropriate randomization
                            is_consumable = item_def.slot == "consumable"
                            inventory.add_item(item_id, randomized=not is_consumable)
                            
                            # Store floor index for randomization context
                            if not hasattr(inventory, "_current_floor"):
                                inventory._current_floor = floor
                            else:
                                inventory._current_floor = floor
                            
                            item_names.append(item_def.name)
                        except Exception:
                            # Skip items that fail to add
                            continue
                    
                    # Format loot message
                    if item_names:
                        if len(item_names) == 1:
                            messages.append(f"You find {item_names[0]} among the remains.")
                        elif len(item_names) == 2:
                            messages.append(f"You find {item_names[0]} and {item_names[1]} among the remains.")
                        else:
                            # Multiple items: list all but last, then "and X"
                            items_str = ", ".join(item_names[:-1]) + f", and {item_names[-1]}"
                            messages.append(f"You find {items_str} among the remains.")
        
        except Exception as e:
            # Error handling: at least give gold message
            if not messages:
                messages.append("You search the remains but find nothing of value.")
        
        return messages
    
    @staticmethod
    def calculate_encounter_xp(encounter_enemies: List[Enemy]) -> int:
        """
        Calculate total XP reward for an encounter group.
        
        Args:
            encounter_enemies: List of enemies in the encounter
        
        Returns:
            Total XP amount
        """
        xp_total = 0
        for enemy in encounter_enemies:
            xp_total += int(getattr(enemy, "xp_reward", 5))
        return xp_total

