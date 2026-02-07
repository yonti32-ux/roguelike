"""
NPC AI system for wandering behavior in villages and towns.

NPCs will wander around their spawn position, similar to enemy patrol behavior.
"""

import random
import math
from typing import Optional, Tuple, TYPE_CHECKING

from settings import TILE_SIZE

if TYPE_CHECKING:
    from engine.core.game import Game

# Patrol settings for NPCs (slower and more relaxed than enemies)
NPC_PATROL_RADIUS_TILES = 5.0  # NPCs can wander 5 tiles from spawn
NPC_PATROL_SPEED_FACTOR = 0.3  # NPCs move slower than enemies
NPC_PATROL_PAUSE_MIN = 1.0  # Minimum pause time at patrol point (seconds)
NPC_PATROL_PAUSE_MAX = 3.0  # Maximum pause time at patrol point (seconds)


def _ensure_npc_ai_fields(npc) -> None:
    """Ensure NPC has all required AI fields for wandering."""
    if not hasattr(npc, "ai_home_pos"):
        # Store spawn position as home
        npc.ai_home_pos = (npc.x, npc.y)
    if not hasattr(npc, "ai_patrol_target"):
        npc.ai_patrol_target = None
    if not hasattr(npc, "ai_patrol_pause"):
        npc.ai_patrol_pause = 0.0
    if not hasattr(npc, "speed"):
        # NPCs need a speed attribute for movement
        npc.speed = 30.0  # Slower than enemies


def _can_npc_move_to_position(
    npc,
    new_x: float,
    new_y: float,
    game: "Game",
) -> bool:
    """
    Check if NPC can move to a position (not blocked by walls or other entities).
    """
    if game.current_map is None:
        return False
    
    import pygame
    
    # Check tile walkability (check center and corners)
    center_x = new_x + npc.width / 2
    center_y = new_y + npc.height / 2
    tx, ty = game.current_map.world_to_tile(center_x, center_y)
    if not game.current_map.is_walkable_tile(tx, ty):
        return False
    
    # Check collision with other entities (but allow passing through player)
    new_rect = pygame.Rect(int(new_x), int(new_y), npc.width, npc.height)
    
    for entity in game.current_map.entities:
        if entity is npc:
            continue
        if entity is game.player:
            continue  # NPCs can pass through player
        if hasattr(entity, "rect") and new_rect.colliderect(entity.rect):
            # Check if entity blocks movement
            if getattr(entity, "blocks_movement", False):
                return False
    
    return True


def _move_npc_towards(
    npc,
    target_x: float,
    target_y: float,
    game: "Game",
    dt: float,
) -> None:
    """
    Move NPC towards target while respecting walls and other entities.
    Uses sliding movement to navigate corners.
    """
    if game.current_map is None:
        return
    
    import pygame
    
    dx = target_x - npc.rect.centerx
    dy = target_y - npc.rect.centery
    
    direction = pygame.Vector2(dx, dy)
    if direction.length_squared() == 0:
        return
    direction = direction.normalize()
    
    move_vector = direction * npc.speed * NPC_PATROL_SPEED_FACTOR * dt
    new_x = npc.x + move_vector.x
    new_y = npc.y + move_vector.y
    
    # Try full diagonal movement first
    if _can_npc_move_to_position(npc, new_x, new_y, game):
        npc.move_to(new_x, new_y)
        return
    
    # If diagonal movement is blocked, try sliding along one axis
    # Try X-axis movement (horizontal sliding)
    slide_x = npc.x + move_vector.x
    if _can_npc_move_to_position(npc, slide_x, npc.y, game):
        npc.move_to(slide_x, npc.y)
        return
    
    # Try Y-axis movement (vertical sliding)
    slide_y = npc.y + move_vector.y
    if _can_npc_move_to_position(npc, npc.x, slide_y, game):
        npc.move_to(npc.x, slide_y)
        return
    
    # Completely blocked - can't move


def _choose_new_patrol_target(npc, game: "Game") -> None:
    """
    Pick a random walkable tile within PATROL_RADIUS_TILES of the home position.
    """
    if game.current_map is None:
        npc.ai_patrol_target = None
        return
    
    home_x, home_y = npc.ai_home_pos
    radius_px = NPC_PATROL_RADIUS_TILES * TILE_SIZE
    
    for _ in range(8):  # try a few times to find something walkable
        angle = random.random() * 2.0 * math.pi
        r = random.random() * radius_px
        px = home_x + math.cos(angle) * r
        py = home_y + math.sin(angle) * r
        
        tx, ty = game.current_map.world_to_tile(px, py)
        if not game.current_map.is_walkable_tile(tx, ty):
            continue
        
        # Center on that tile
        target_x = tx * TILE_SIZE + TILE_SIZE / 2
        target_y = ty * TILE_SIZE + TILE_SIZE / 2
        npc.ai_patrol_target = (target_x, target_y)
        return
    
    # Fallback: no good tile found
    npc.ai_patrol_target = None


def _update_npc_patrol(npc, game: "Game", dt: float) -> None:
    """
    Idle behavior: wander around a small radius from the home position.
    """
    if game.current_map is None:
        return
    
    _ensure_npc_ai_fields(npc)
    
    # If we're currently paused at a patrol point, count down
    if npc.ai_patrol_pause > 0.0:
        npc.ai_patrol_pause -= dt
        if npc.ai_patrol_pause <= 0.0:
            npc.ai_patrol_pause = 0.0
        else:
            return  # still pausing
    
    # If we don't have a patrol target or we've basically reached it,
    # pick a new one around the home position.
    if npc.ai_patrol_target is None:
        _choose_new_patrol_target(npc, game)
        if npc.ai_patrol_target is None:
            return
    else:
        tx, ty = npc.ai_patrol_target
        dx = tx - npc.rect.centerx
        dy = ty - npc.rect.centery
        if dx * dx + dy * dy <= (0.3 * TILE_SIZE) ** 2:
            # Reached patrol point: pause for a bit, then choose a new one
            npc.ai_patrol_target = None
            npc.ai_patrol_pause = random.uniform(NPC_PATROL_PAUSE_MIN, NPC_PATROL_PAUSE_MAX)
            return
    
    # Move towards patrol target
    tx, ty = npc.ai_patrol_target
    _move_npc_towards(npc, tx, ty, game, dt)


def update_npc_ai(npc, game: "Game", dt: float) -> None:
    """
    Update NPC wandering behavior.
    
    NPCs will wander around their spawn position in a relaxed manner.
    They don't chase or fight - just peaceful wandering.
    """
    _ensure_npc_ai_fields(npc)
    
    if game.current_map is None:
        return
    
    # Only wandering citizens/villagers should wander (not building NPCs)
    # Building NPCs stay in their buildings
    npc_type = getattr(npc, "npc_type", "")
    if npc_type not in ("villager", "citizen"):
        return
    
    # Update patrol/wandering behavior
    _update_npc_patrol(npc, game, dt)
