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
    
    # Get sprite with original size tracking for debug overlay
    # First get sprite at canonical size to check original size
    original_sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        sprite_id,
        variant=variant,
        fallback_color=None,  # Don't use fallback for original check
        size=None,  # Get at canonical size first
    )
    original_size = original_sprite.get_size() if original_sprite else None
    
    # Now get sprite at requested size
    sprite = sprite_manager.get_sprite(
        SpriteCategory.ENTITY,
        sprite_id,
        variant=variant,
        fallback_color=fallback_color,
        size=(width, height),
    )
    
    if sprite:
        surface.blit(sprite, (x, y))
    else:
        # Sprite is None, but we still want to show debug overlay
        draw_sprite_debug_overlay(
            surface, None, sprite_id, x, y,
            width, height,
            original_size=original_size,
            requested_size=(width, height),
            sprite_manager=sprite_manager,
        )
        return
    
    # Draw debug overlay if enabled
    final_size = sprite.get_size()
    draw_sprite_debug_overlay(
        surface, sprite, sprite_id, x, y,
        final_size[0], final_size[1],
        original_size=original_size,
        requested_size=(width, height),
        sprite_manager=sprite_manager,
    )


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
    
    # Get sprite with original size tracking for debug overlay
    # First get sprite at canonical size to check original size
    original_sprite = sprite_manager.get_sprite(
        SpriteCategory.TILE,
        sprite_id,
        fallback_color=None,  # Don't use fallback for original check
        size=None,  # Get at canonical size first
    )
    original_size = original_sprite.get_size() if original_sprite else None
    
    # Now get sprite at requested size
    sprite = sprite_manager.get_sprite(
        SpriteCategory.TILE,
        sprite_id,
        fallback_color=fallback_color,
        size=(size, size),
    )
    
    if sprite:
        surface.blit(sprite, (x, y))
    else:
        # Sprite is None, but we still want to show debug overlay
        draw_sprite_debug_overlay(
            surface, None, sprite_id, x, y,
            size, size,
            original_size=original_size,
            requested_size=(size, size),
            sprite_manager=sprite_manager,
        )
        return
    
    # Draw debug overlay if enabled
    final_size = sprite.get_size()
    draw_sprite_debug_overlay(
        surface, sprite, sprite_id, x, y,
        final_size[0], final_size[1],
        original_size=original_size,
        requested_size=(size, size),
        sprite_manager=sprite_manager,
    )


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
    sprite_id: Optional[str] = None,
    original_size: Optional[Tuple[int, int]] = None,
    sprite_manager: Optional[SpriteManager] = None,
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
        sprite_id: Optional sprite ID for debug overlay
        original_size: Optional original size for debug overlay
        sprite_manager: Optional sprite manager for debug overlay
    """
    if zoom <= 0:
        zoom = 1.0
    
    # Transform world coordinates to screen coordinates
    screen_x = int((world_x - camera_x) * zoom)
    screen_y = int((world_y - camera_y) * zoom)
    
    # Store original size before scaling for debug overlay
    orig_w, orig_h = sprite.get_size()
    
    # Scale sprite if zoom != 1.0
    if zoom != 1.0:
        scaled_w = max(1, int(sprite.get_width() * zoom))
        scaled_h = max(1, int(sprite.get_height() * zoom))
        sprite = pygame.transform.scale(sprite, (scaled_w, scaled_h))
    
    surface.blit(sprite, (screen_x, screen_y))
    
    # Draw debug overlay if enabled and sprite_id provided
    if sprite_id:
        final_size = sprite.get_size()
        draw_sprite_debug_overlay(
            surface, sprite, sprite_id, screen_x, screen_y,
            final_size[0], final_size[1],
            original_size=original_size or (orig_w, orig_h),
            requested_size=final_size,  # Final size is what was requested after zoom
            sprite_manager=sprite_manager,
        )


def draw_sprite_debug_overlay(
    surface: pygame.Surface,
    sprite: Optional[pygame.Surface],
    sprite_id: str,
    screen_x: int,
    screen_y: int,
    sprite_width: int,
    sprite_height: int,
    original_size: Optional[Tuple[int, int]] = None,
    requested_size: Optional[Tuple[int, int]] = None,
    sprite_manager: Optional[SpriteManager] = None,
) -> None:
    """
    Draw debug overlay for sprites when DEBUG_SPRITES is enabled.
    
    Shows:
    - "MISSING: sprite_id" if sprite is missing or is a fallback
    - "SCALED: original_size -> final_size" if scaled unexpectedly
    - Optional thin rect around the sprite bounds
    
    Args:
        surface: Surface to draw on
        sprite: The sprite surface (or None if missing)
        sprite_id: ID of the sprite for display
        screen_x, screen_y: Screen position where sprite was drawn
        sprite_width, sprite_height: Actual size of the sprite on screen
        original_size: Original sprite size before scaling (width, height)
        requested_size: Requested size (width, height)
        sprite_manager: Optional sprite manager to check if sprite is fallback
    """
    from ..utils.cheats import is_debug_sprites_enabled
    
    if not is_debug_sprites_enabled():
        return
    
    if sprite_manager is None:
        sprite_manager = get_sprite_manager()
    
    # Check if sprite is missing or is a fallback
    is_missing = sprite is None
    is_fallback = False
    if sprite is not None:
        is_fallback = sprite_manager.is_sprite_fallback(sprite)
    
    # Check if sprite was scaled unexpectedly
    was_scaled = False
    scale_info = None
    if sprite is not None and original_size is not None and requested_size is not None:
        orig_w, orig_h = original_size
        req_w, req_h = requested_size
        final_w, final_h = sprite.get_size()
        
        # Check if scaling happened (original size != final size)
        # and if the final size matches what was requested
        if (orig_w != final_w or orig_h != final_h):
            was_scaled = True
            scale_info = f"{orig_w}x{orig_h} -> {final_w}x{final_h}"
    
    # Create debug messages
    messages = []
    if is_missing or is_fallback:
        messages.append(f"MISSING: {sprite_id}")
    if was_scaled and scale_info:
        messages.append(f"SCALED: {scale_info}")
    
    if not messages:
        return  # Nothing to show
    
    # Create a small font for debug text
    try:
        debug_font = pygame.font.Font(None, 16)
    except:
        debug_font = pygame.font.SysFont("consolas", 12)
    
    # Draw debug text slightly above the sprite
    text_y = screen_y - 15
    for i, msg in enumerate(messages):
        # Draw text with background for readability
        text_surf = debug_font.render(msg, True, (255, 0, 0))  # Red text
        bg_rect = pygame.Rect(
            screen_x - 2,
            text_y - 2 + i * 12,
            text_surf.get_width() + 4,
            text_surf.get_height() + 4
        )
        # Semi-transparent black background
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 200))
        surface.blit(bg_surf, bg_rect.topleft)
        surface.blit(text_surf, (screen_x, text_y + i * 12))
    
    # Draw thin rect around sprite bounds
    debug_rect = pygame.Rect(screen_x, screen_y, sprite_width, sprite_height)
    pygame.draw.rect(surface, (255, 0, 0), debug_rect, width=1)  # Red outline
