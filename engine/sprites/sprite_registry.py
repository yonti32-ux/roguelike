"""
Sprite registry system for mapping game entities/items to sprite IDs.

This module provides centralized mappings from game object IDs to sprite identifiers,
making it easy to manage sprite assignments and add new sprites incrementally.
"""

from typing import Dict, Optional
from enum import Enum

from .sprites import SpriteCategory


class EntitySpriteType(Enum):
    """Types of entity sprites."""
    PLAYER = "player"
    ENEMY = "enemy"
    CHEST = "chest"
    MERCHANT = "merchant"
    EVENT_NODE = "event_node"


class TileSpriteType(Enum):
    """Types of tile sprites."""
    FLOOR = "floor"
    WALL = "wall"
    UP_STAIRS = "up_stairs"
    DOWN_STAIRS = "down_stairs"


class SpriteRegistry:
    """
    Registry that maps game object IDs to sprite identifiers.
    
    This allows flexible sprite assignment:
    - Entity types to sprite IDs
    - Item IDs to sprite IDs
    - Tile types to sprite IDs
    - Easy addition of new mappings
    """
    
    def __init__(self):
        # Entity type mappings
        self.entity_sprites: Dict[EntitySpriteType, str] = {
            EntitySpriteType.PLAYER: "player",
            EntitySpriteType.ENEMY: "enemy_default",
            EntitySpriteType.CHEST: "chest",
            EntitySpriteType.MERCHANT: "merchant",
            EntitySpriteType.EVENT_NODE: "event_node",
        }
        
        # Tile type mappings
        self.tile_sprites: Dict[TileSpriteType, str] = {
            TileSpriteType.FLOOR: "floor",
            TileSpriteType.WALL: "wall",
            TileSpriteType.UP_STAIRS: "up_stairs",
            TileSpriteType.DOWN_STAIRS: "down_stairs",
        }
        
        # Item ID to sprite ID mappings (populated from item data)
        # Format: {item_id: sprite_id}
        self.item_sprites: Dict[str, str] = {}
        
        # Enemy type to sprite ID mappings
        # Format: {enemy_type: sprite_id}
        self.enemy_sprites: Dict[str, str] = {}
        
        # Event node type to sprite ID mappings
        # Format: {event_id: sprite_id}
        self.event_sprites: Dict[str, str] = {
            "shrine_of_power": "shrine_power",
            "cache": "cache",
            "lore_stone": "lore_stone",
        }
    
    def get_entity_sprite_id(self, entity_type: EntitySpriteType) -> str:
        """Get sprite ID for an entity type."""
        return self.entity_sprites.get(entity_type, "entity_default")
    
    def get_tile_sprite_id(self, tile_type: TileSpriteType) -> str:
        """Get sprite ID for a tile type."""
        return self.tile_sprites.get(tile_type, "tile_default")
    
    def get_item_sprite_id(self, item_id: str) -> str:
        """
        Get sprite ID for an item.
        
        If no specific mapping exists, tries to use the item_id itself.
        """
        return self.item_sprites.get(item_id, item_id)
    
    def get_enemy_sprite_id(self, enemy_type: str) -> str:
        """
        Get sprite ID for an enemy type.
        
        If no specific mapping exists, falls back to generic enemy sprite.
        """
        return self.enemy_sprites.get(enemy_type, "enemy_default")
    
    def get_event_sprite_id(self, event_id: str) -> str:
        """
        Get sprite ID for an event node.
        
        If no specific mapping exists, uses generic event sprite.
        """
        return self.event_sprites.get(event_id, "event_node")
    
    def register_item_sprite(self, item_id: str, sprite_id: str) -> None:
        """Register a custom sprite for an item."""
        self.item_sprites[item_id] = sprite_id
    
    def register_enemy_sprite(self, enemy_type: str, sprite_id: str) -> None:
        """Register a custom sprite for an enemy type."""
        self.enemy_sprites[enemy_type] = sprite_id
    
    def register_event_sprite(self, event_id: str, sprite_id: str) -> None:
        """Register a custom sprite for an event type."""
        self.event_sprites[event_id] = sprite_id
    
    def load_item_mappings_from_data(self, items_data: list) -> None:
        """
        Auto-populate item sprite mappings from item data.
        
        This automatically creates sprite mappings for all items based on their IDs.
        You can override specific items later with register_item_sprite().
        
        Args:
            items_data: List of item dictionaries from JSON files
        """
        for item in items_data:
            item_id = item.get("id")
            if item_id:
                # Use item_id as sprite_id by default
                # Can be overridden later if needed
                if item_id not in self.item_sprites:
                    self.item_sprites[item_id] = item_id


# Global registry instance
_registry: Optional[SpriteRegistry] = None


def get_registry() -> SpriteRegistry:
    """Get the global sprite registry instance."""
    global _registry
    if _registry is None:
        _registry = SpriteRegistry()
    return _registry


def init_registry() -> SpriteRegistry:
    """Initialize the global sprite registry and load default mappings."""
    global _registry
    _registry = SpriteRegistry()
    
    # Auto-load item mappings if items data is available
    try:
        from systems.inventory import all_items
        items = all_items()
        items_data = [{"id": item.id} for item in items]
        _registry.load_item_mappings_from_data(items_data)
    except Exception:
        pass  # Items not loaded yet, that's okay
    
    return _registry

