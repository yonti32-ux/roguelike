"""
Helper functions for easily integrating sprites into existing game code.

These functions provide drop-in replacements for drawing entities, tiles, and items
with sprite support, maintaining backward compatibility with color-based rendering.
"""

from typing import Optional, Tuple
import pygame

from .sprites import SpriteManager, SpriteCategory, get_sprite_manager
from .sprite_registry import (
    SpriteRegistry,
    EntitySpriteType,
    TileSpriteType,
    get_registry,
)


def draw_entity_sprite(
    surface: pygame.Surface,
    entity_type: EntitySpriteType,
    x: int,
    y: int,
    width: int,
    height: int,
    sprite_manager: Optional[SpriteManager] = None,
    registry: Optional[SpriteRegistry] = None,
    fallback_color: Optional[Tuple[int, int, int]] = None,
    variant: Optional[str] = None,
) -> None:
    """
    Draw an entity using its sprite.
    
    Args:
        surface: Surface to draw on
        entity_type: Type of entity to draw
        x, y: Screen coordinates
        width, height: Desired sprite size
        sprite_manager: Optional sprite manager (uses global if None)
        registry: Optional registry (uses global if None)
        fallback_color: Color if sprite missing
        variant: Optional sprite variant (e.g., "idle", "attacking")
    """
    if sprite_manager is None:
        sprite_manager = get_sprite_manager()
    if registry is None:
        registry = get_registry()
    
    sprite_id = registry.get_entity_sprite_id(entity_type)
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        sprite_id,
        variant=variant,
        fallback_color=fallback_color,
        size=(width, height),
    )
    
    if sprite:
        surface.blit(sprite, (x, y))


def draw_tile_sprite(
    surface: pygame.Surface,
    tile_type: TileSpriteType,
    x: int,
    y: int,
    size: int,
    sprite_manager: Optional[SpriteManager] = None,
    registry: Optional[SpriteRegistry] = None,
    fallback_color: Optional[Tuple[int, int, int]] = None,
) -> None:
    """
    Draw a tile using its sprite.
    
    Args:
        surface: Surface to draw on
        tile_type: Type of tile to draw
        x, y: Screen coordinates
        size: Tile size (usually TILE_SIZE)
        sprite_manager: Optional sprite manager (uses global if None)
        registry: Optional registry (uses global if None)
        fallback_color: Color if sprite missing
    """
    if sprite_manager is None:
        sprite_manager = get_sprite_manager()
    if registry is None:
        registry = get_registry()
    
    sprite_id = registry.get_tile_sprite_id(tile_type)
    sprite = sprite_manager.get_sprite(
        SpriteCategory.TILE,
        sprite_id,
        fallback_color=fallback_color,
        size=(size, size),
    )
    
    if sprite:
        surface.blit(sprite, (x, y))


def draw_item_sprite(
    surface: pygame.Surface,
    item_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    sprite_manager: Optional[SpriteManager] = None,
    registry: Optional[SpriteRegistry] = None,
    fallback_color: Optional[Tuple[int, int, int]] = None,
) -> None:
    """
    Draw an item using its sprite.
    
    Args:
        surface: Surface to draw on
        item_id: ID of the item
        x, y: Screen coordinates
        width, height: Desired sprite size
        sprite_manager: Optional sprite manager (uses global if None)
        registry: Optional registry (uses global if None)
        fallback_color: Color if sprite missing
    """
    if sprite_manager is None:
        sprite_manager = get_sprite_manager()
    if registry is None:
        registry = get_registry()
    
    sprite_id = registry.get_item_sprite_id(item_id)
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ITEM,
        sprite_id,
        fallback_color=fallback_color,
        size=(width, height),
    )
    
    if sprite:
        surface.blit(sprite, (x, y))


def get_entity_sprite(
    entity_type: EntitySpriteType,
    width: int,
    height: int,
    sprite_manager: Optional[SpriteManager] = None,
    registry: Optional[SpriteRegistry] = None,
    fallback_color: Optional[Tuple[int, int, int]] = None,
    variant: Optional[str] = None,
) -> Optional[pygame.Surface]:
    """
    Get an entity sprite surface (useful for UI, icons, etc.).
    
    Returns:
        pygame.Surface or None if not found
    """
    if sprite_manager is None:
        sprite_manager = get_sprite_manager()
    if registry is None:
        registry = get_registry()
    
    sprite_id = registry.get_entity_sprite_id(entity_type)
    return sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        sprite_id,
        variant=variant,
        fallback_color=fallback_color,
        size=(width, height),
    )


def get_item_sprite(
    item_id: str,
    width: int,
    height: int,
    sprite_manager: Optional[SpriteManager] = None,
    registry: Optional[SpriteRegistry] = None,
    fallback_color: Optional[Tuple[int, int, int]] = None,
) -> Optional[pygame.Surface]:
    """
    Get an item sprite surface (useful for inventory UI, tooltips, etc.).
    
    Returns:
        pygame.Surface or None if not found
    """
    if sprite_manager is None:
        sprite_manager = get_sprite_manager()
    if registry is None:
        registry = get_registry()
    
    sprite_id = registry.get_item_sprite_id(item_id)
    return sprite_manager.get_sprite(
        SpriteCategory.ITEM,
        sprite_id,
        fallback_color=fallback_color,
        size=(width, height),
    )


def draw_sprite_with_camera(
    surface: pygame.Surface,
    sprite: pygame.Surface,
    world_x: float,
    world_y: float,
    camera_x: float,
    camera_y: float,
    zoom: float = 1.0,
) -> None:
    """
    Draw a sprite with camera and zoom transformation.
    
    This is a helper for drawing sprites in the exploration view.
    
    Args:
        surface: Surface to draw on
        sprite: Sprite to draw
        world_x, world_y: World coordinates of the sprite
        camera_x, camera_y: Camera position
        zoom: Zoom level (1.0 = normal)
    """
    if zoom <= 0:
        zoom = 1.0
    
    # Transform world coordinates to screen coordinates
    screen_x = int((world_x - camera_x) * zoom)
    screen_y = int((world_y - camera_y) * zoom)
    
    # Scale sprite if zoom != 1.0
    if zoom != 1.0:
        scaled_w = max(1, int(sprite.get_width() * zoom))
        scaled_h = max(1, int(sprite.get_height() * zoom))
        sprite = pygame.transform.scale(sprite, (scaled_w, scaled_h))
    
    surface.blit(sprite, (screen_x, screen_y))

