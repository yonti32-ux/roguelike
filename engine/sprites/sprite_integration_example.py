"""
Example integration code showing how to add sprite support to existing game objects.

This file demonstrates how to integrate the sprite system into:
- Entity drawing (Player, Enemy, etc.)
- Tile rendering
- Item display

You can use these as templates for integrating sprites into your actual game code.
"""

import pygame
from typing import Optional, Tuple

from .sprites import get_sprite_manager, SpriteCategory
from .sprite_registry import get_registry, EntitySpriteType, TileSpriteType
from .sprite_helpers import draw_sprite_with_camera, get_entity_sprite


# ============================================================================
# Example: Entity Integration
# ============================================================================

def draw_player_with_sprite_example(
    surface: pygame.Surface,
    player_x: float,
    player_y: float,
    player_width: int,
    player_height: int,
    camera_x: float = 0.0,
    camera_y: float = 0.0,
    zoom: float = 1.0,
    fallback_color: Tuple[int, int, int] = (220, 210, 90),
) -> None:
    """
    Example: Draw player entity with sprite support.
    
    This replaces the existing draw() method in Player class.
    """
    sprite_manager = get_sprite_manager()
    registry = get_registry()
    
    # Get sprite ID from registry
    sprite_id = registry.get_entity_sprite_id(EntitySpriteType.PLAYER)
    
    # Get the sprite (with fallback to color)
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        sprite_id,
        fallback_color=fallback_color,
        size=(player_width, player_height),
    )
    
    # Draw with camera transformation
    draw_sprite_with_camera(
        surface, sprite,
        player_x, player_y,
        camera_x, camera_y, zoom
    )


def draw_enemy_with_sprite_example(
    surface: pygame.Surface,
    enemy_x: float,
    enemy_y: float,
    enemy_width: int,
    enemy_height: int,
    enemy_type: str = "default",
    camera_x: float = 0.0,
    camera_y: float = 0.0,
    zoom: float = 1.0,
    fallback_color: Tuple[int, int, int] = (200, 80, 80),
    is_elite: bool = False,
) -> None:
    """
    Example: Draw enemy entity with sprite support.
    
    Supports different enemy types and elite variants.
    """
    sprite_manager = get_sprite_manager()
    registry = get_registry()
    
    # Get sprite ID for this enemy type
    sprite_id = registry.get_enemy_sprite_id(enemy_type)
    
    # Use variant for elite enemies
    variant = "elite" if is_elite else None
    
    # Get the sprite
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        sprite_id,
        variant=variant,
        fallback_color=fallback_color,
        size=(enemy_width, enemy_height),
    )
    
    # Draw with camera
    draw_sprite_with_camera(
        surface, sprite,
        enemy_x, enemy_y,
        camera_x, camera_y, zoom
    )
    
    # Draw elite glow overlay if needed
    if is_elite and sprite:
        # You can add overlay effects here if needed
        pass


def draw_chest_with_sprite_example(
    surface: pygame.Surface,
    chest_x: float,
    chest_y: float,
    chest_width: int,
    chest_height: int,
    opened: bool = False,
    camera_x: float = 0.0,
    camera_y: float = 0.0,
    zoom: float = 1.0,
) -> None:
    """
    Example: Draw chest with sprite support, different states.
    """
    sprite_manager = get_sprite_manager()
    registry = get_registry()
    
    sprite_id = registry.get_entity_sprite_id(EntitySpriteType.CHEST)
    
    # Use variant for opened state
    variant = "opened" if opened else "closed"
    
    # Fallback colors
    fallback_color = (120, 120, 120) if opened else (210, 180, 80)
    
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        sprite_id,
        variant=variant,
        fallback_color=fallback_color,
        size=(chest_width, chest_height),
    )
    
    draw_sprite_with_camera(
        surface, sprite,
        chest_x, chest_y,
        camera_x, camera_y, zoom
    )


# ============================================================================
# Example: Tile Integration
# ============================================================================

def draw_tile_with_sprite_example(
    surface: pygame.Surface,
    tile_type: TileSpriteType,
    tile_x: int,
    tile_y: int,
    tile_size: int,
    fallback_color: Optional[Tuple[int, int, int]] = None,
) -> None:
    """
    Example: Draw a tile with sprite support.
    
    Usage:
        draw_tile_with_sprite_example(surface, TileSpriteType.FLOOR, x, y, TILE_SIZE)
        draw_tile_with_sprite_example(surface, TileSpriteType.WALL, x, y, TILE_SIZE)
    """
    from .sprite_helpers import draw_tile_sprite
    
    draw_tile_sprite(
        surface,
        tile_type,
        tile_x, tile_y,
        tile_size,
        fallback_color=fallback_color,
    )


# ============================================================================
# Example: Item Integration (for Inventory UI)
# ============================================================================

def draw_item_icon_example(
    surface: pygame.Surface,
    item_id: str,
    x: int,
    y: int,
    icon_size: int = 32,
) -> None:
    """
    Example: Draw item icon in inventory/shop UI.
    """
    from .sprite_helpers import draw_item_sprite
    
    draw_item_sprite(
        surface,
        item_id,
        x, y,
        icon_size, icon_size,
    )


def get_item_icon_surface_example(
    item_id: str,
    icon_size: int = 32,
) -> Optional[pygame.Surface]:
    """
    Example: Get item icon surface for use in UI components.
    """
    from .sprite_helpers import get_item_sprite
    
    return get_item_sprite(
        item_id,
        icon_size, icon_size,
    )


# ============================================================================
# Example: Full Entity Class Integration
# ============================================================================

class SpriteEntityMixin:
    """
    Mixin class that adds sprite drawing capabilities to entities.
    
    Usage:
        class Player(Entity, SpriteEntityMixin):
            def __init__(self, ...):
                super().__init__(...)
                self.entity_sprite_type = EntitySpriteType.PLAYER
                self.fallback_color = (220, 210, 90)
            
            def draw(self, surface, camera_x=0.0, camera_y=0.0, zoom=1.0):
                self.draw_with_sprite(surface, camera_x, camera_y, zoom)
    """
    
    entity_sprite_type: EntitySpriteType
    fallback_color: Tuple[int, int, int] = (255, 0, 255)
    
    def draw_with_sprite(
        self,
        surface: pygame.Surface,
        camera_x: float = 0.0,
        camera_y: float = 0.0,
        zoom: float = 1.0,
        variant: Optional[str] = None,
    ) -> None:
        """Draw this entity using its sprite."""
        sprite_manager = get_sprite_manager()
        registry = get_registry()
        
        sprite_id = registry.get_entity_sprite_id(self.entity_sprite_type)
        
        sprite = sprite_manager.get_sprite(
            SpriteCategory.ENTITY,
            sprite_id,
            variant=variant,
            fallback_color=self.fallback_color,
            size=(self.width, self.height),
        )
        
        draw_sprite_with_camera(
            surface, sprite,
            self.x, self.y,
            camera_x, camera_y, zoom
        )


# ============================================================================
# Example: Initialization
# ============================================================================

def initialize_sprite_system_example() -> None:
    """
    Example: Initialize sprite system at game startup.
    
    Call this in your main() function or Game.__init__()
    """
    from .sprites import init_sprite_manager
    from .sprite_registry import init_registry
    
    # Initialize sprite manager (optional: specify custom sprite root)
    # sprite_manager = init_sprite_manager("path/to/sprites")
    sprite_manager = init_sprite_manager()  # Uses default: sprites/ in project root
    
    # Initialize registry (auto-loads item mappings)
    registry = init_registry()
    
    # Optionally preload commonly used sprites
    sprite_manager.preload_sprites([
        (SpriteCategory.ENTITY, "player", None),
        (SpriteCategory.TILE, "floor", None),
        (SpriteCategory.TILE, "wall", None),
    ])
    
    print("Sprite system initialized!")

