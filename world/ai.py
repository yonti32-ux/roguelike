# world/ai.py

from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Optional
import random
import math

import pygame

from settings import TILE_SIZE

if TYPE_CHECKING:
    from engine.game import Game
    from world.entities import Enemy


# Tunables for enemy awareness/behaviour
DETECTION_RANGE_TILES = 7          # how far they can *see* you
SEARCH_DURATION = 2.0              # seconds they keep searching after losing LoS
STOP_SEARCH_DISTANCE_TILES = 0.5   # distance to last_seen to give up

# Patrol behaviour
PATROL_RADIUS_TILES = 4.0          # how far they wander from their home
PATROL_PAUSE_MIN = 0.5             # min idle pause at a patrol point
PATROL_PAUSE_MAX = 2.0             # max idle pause at a patrol point
PATROL_SPEED_FACTOR = 0.6          # patrol speed vs full chase speed


def _ensure_ai_fields(enemy: "Enemy") -> None:
    """
    Ensure this enemy has the AI attributes we expect.
    We attach them dynamically so the Enemy class stays simple.
    """
    if not hasattr(enemy, "ai_state"):
        enemy.ai_state = "idle"  # "idle" | "chase" | "search"
    if not hasattr(enemy, "ai_search_time"):
        enemy.ai_search_time = 0.0
    if not hasattr(enemy, "ai_last_seen_player_pos"):
        enemy.ai_last_seen_player_pos: Optional[Tuple[float, float]] = None

    # Patrol-related fields
    if not hasattr(enemy, "ai_home_pos"):
        # Remember initial spawn as home
        enemy.ai_home_pos: Tuple[float, float] = enemy.rect.center
    if not hasattr(enemy, "ai_patrol_target"):
        enemy.ai_patrol_target: Optional[Tuple[float, float]] = None
    if not hasattr(enemy, "ai_patrol_pause"):
        enemy.ai_patrol_pause: float = 0.0


def _move_enemy_towards(
    enemy: "Enemy",
    target_x: float,
    target_y: float,
    game: "Game",
    dt: float,
    *,
    allow_battle: bool = True,
    speed_factor: float = 1.0,
) -> None:
    """
    Move enemy towards target while respecting walls, other entities,
    and optionally starting battles on contact with the player.
    """
    if game.current_map is None or game.player is None:
        return

    dx = target_x - enemy.rect.centerx
    dy = target_y - enemy.rect.centery

    direction = pygame.Vector2(dx, dy)
    if direction.length_squared() == 0:
        return
    direction = direction.normalize()

    move_vector = direction * enemy.speed * speed_factor * dt
    new_x = enemy.x + move_vector.x
    new_y = enemy.y + move_vector.y

    new_rect = pygame.Rect(
        int(new_x),
        int(new_y),
        enemy.width,
        enemy.height,
    )

    # Can't walk through walls
    if not game.current_map.rect_can_move_to(new_rect):
        return

    # Can't walk through other blocking entities
    for other in game.current_map.entities:
        if other is enemy:
            continue
        if getattr(other, "blocks_movement", False) and other.rect.colliderect(new_rect):
            return

    # If stepping into player -> trigger battle (unless grace or disabled)
    if allow_battle and game.player.rect.colliderect(new_rect):
        if game.post_battle_grace <= 0.0:
            game.start_battle(enemy)
        return

    # Otherwise, move normally
    enemy.move_to(new_x, new_y)


def _update_patrol(enemy: "Enemy", game: "Game", dt: float) -> None:
    """
    Idle behaviour: wander around a small radius from the home position.
    """
    if game.current_map is None:
        return

    # If we're currently paused at a patrol point, count down
    if enemy.ai_patrol_pause > 0.0:
        enemy.ai_patrol_pause -= dt
        if enemy.ai_patrol_pause <= 0.0:
            enemy.ai_patrol_pause = 0.0
        else:
            return  # still pausing

    # If we don't have a patrol target or we've basically reached it,
    # pick a new one around the home position.
    if enemy.ai_patrol_target is None:
        _choose_new_patrol_target(enemy, game)
        if enemy.ai_patrol_target is None:
            return
    else:
        tx, ty = enemy.ai_patrol_target
        dx = tx - enemy.rect.centerx
        dy = ty - enemy.rect.centery
        if dx * dx + dy * dy <= (0.3 * TILE_SIZE) ** 2:
            # Reached patrol point: pause for a bit, then choose a new one
            enemy.ai_patrol_target = None
            enemy.ai_patrol_pause = random.uniform(PATROL_PAUSE_MIN, PATROL_PAUSE_MAX)
            return

    # Move towards the patrol target (no battle triggers while patrolling)
    tx, ty = enemy.ai_patrol_target
    _move_enemy_towards(
        enemy,
        tx,
        ty,
        game,
        dt,
        allow_battle=False,           # don't start battle just because you're strolling past
        speed_factor=PATROL_SPEED_FACTOR,
    )


def _choose_new_patrol_target(enemy: "Enemy", game: "Game") -> None:
    """
    Pick a random walkable tile within PATROL_RADIUS_TILES of the home position.
    """
    if game.current_map is None:
        enemy.ai_patrol_target = None
        return

    home_x, home_y = enemy.ai_home_pos
    radius_px = PATROL_RADIUS_TILES * TILE_SIZE

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
        enemy.ai_patrol_target = (target_x, target_y)
        return

    # Fallback: no good tile found
    enemy.ai_patrol_target = None


def update_enemy_ai(enemy: "Enemy", game: "Game", dt: float) -> None:
    """
    Exploration AI 2.1:

    - Enemies only notice the player if:
        * within DETECTION_RANGE_TILES, AND
        * line-of-sight is clear (no walls).

    - States:
        * idle   : patrol around their home position until they spot you
        * chase  : move directly towards you while they see you
        * search : move to the last seen position for a short time

    - If search timer expires or they reach the last seen spot, they go idle
      and resume patrolling.
    """
    _ensure_ai_fields(enemy)

    if game.player is None or game.current_map is None:
        return

    # No chasing during post-battle grace
    if game.post_battle_grace > 0.0:
        return

    # Dead enemies shouldn't move
    if getattr(enemy, "hp", 1) <= 0:
        return

    # Tile coords
    px, py = game.player.rect.center
    ex, ey = enemy.rect.center

    pt_x, pt_y = game.current_map.world_to_tile(px, py)
    et_x, et_y = game.current_map.world_to_tile(ex, ey)

    dx_tiles = pt_x - et_x
    dy_tiles = pt_y - et_y
    dist_tiles_sq = dx_tiles * dx_tiles + dy_tiles * dy_tiles
    detection_sq = DETECTION_RANGE_TILES * DETECTION_RANGE_TILES

    # LoS: use the same Bresenham-based check as FOV, from enemy to player.
    can_see_player = False
    if dist_tiles_sq <= detection_sq:
        # _line_of_sight is "private" but it's exactly what we want
        if game.current_map._line_of_sight(et_x, et_y, pt_x, pt_y):
            can_see_player = True

    state = enemy.ai_state

    # --- State transitions based on vision ---
    if can_see_player:
        # Refresh last seen position + search timer
        enemy.ai_last_seen_player_pos = (px, py)
        enemy.ai_search_time = SEARCH_DURATION

        if state in ("idle", "search"):
            enemy.ai_state = "chase"
            state = "chase"
    else:
        # No LoS this frame
        if state == "chase":
            # Lost sight -> start searching
            enemy.ai_state = "search"
            state = "search"

    # --- Behaviour by state ---
    if state == "idle":
        # Patrol around their home position when not seeing the player
        _update_patrol(enemy, game, dt)
        return

    if state == "chase":
        # Move directly towards the *current* player position
        _move_enemy_towards(enemy, px, py, game, dt, allow_battle=True, speed_factor=1.0)
        return

    if state == "search":
        # Move towards the last seen player position, but only for a while
        if enemy.ai_last_seen_player_pos is None:
            enemy.ai_state = "idle"
            return

        enemy.ai_search_time -= dt
        if enemy.ai_search_time <= 0.0:
            enemy.ai_state = "idle"
            enemy.ai_last_seen_player_pos = None
            return

        lx, ly = enemy.ai_last_seen_player_pos
        # If we're basically at the last seen spot, give up
        dx = lx - enemy.rect.centerx
        dy = ly - enemy.rect.centery
        if (dx * dx + dy * dy) <= (
            STOP_SEARCH_DISTANCE_TILES * STOP_SEARCH_DISTANCE_TILES * TILE_SIZE * TILE_SIZE
        ):
            enemy.ai_state = "idle"
            enemy.ai_last_seen_player_pos = None
            return

        _move_enemy_towards(
            enemy,
            lx,
            ly,
            game,
            dt,
            allow_battle=True,
            speed_factor=1.0,
        )
