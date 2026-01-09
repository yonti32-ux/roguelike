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
from systems.loot import roll_battle_loot

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
    ) -> List[str]:
        """
        Calculate and award rewards after a battle victory.
        
        Args:
            floor: Current floor number (affects reward amounts)
            hero_stats: Hero stats object for adding gold
            inventory: Inventory object for adding items (optional)
        
        Returns:
            List of message strings describing rewards
        """
        messages: List[str] = []
        
        # --- Gold pouch ---
        # Enemies on deeper floors give more gold
        base_min_gold = 3 + floor
        base_max_gold = 6 + floor * 2
        
        gold_amount = random.randint(base_min_gold, base_max_gold)
        if hasattr(hero_stats, "add_gold"):
            gained_gold = hero_stats.add_gold(gold_amount)
        else:
            gained_gold = gold_amount
        
        if gained_gold > 0:
            messages.append(f"You pick up a pouch of {gained_gold} gold.")
        
        # --- Item drop ---
        # Roll for item loot (25-50% chance based on floor)
        if inventory is not None:
            item_id = roll_battle_loot(floor)
            if item_id is not None:
                # Add item to inventory (with randomization enabled)
                inventory.add_item(item_id, randomized=True)
                # Store floor index for randomization context
                if not hasattr(inventory, "_current_floor"):
                    inventory._current_floor = floor
                else:
                    inventory._current_floor = floor
                
                # Get item name for message
                from systems.inventory import get_item_def
                item_def = get_item_def(item_id)
                item_name = item_def.name if item_def is not None else item_id
                messages.append(f"You find {item_name} among the remains.")
        
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

