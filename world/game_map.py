# world/game_map.py

from typing import List, Tuple, Set
import math

import pygame

from settings import TILE_SIZE
from world.tiles import Tile
from world.entities import Entity
from world.mapgen import RectRoom  # NEW: to type rooms list


class GameMap:
    """
    Represents a single map (dungeon floor, village, etc.).
    Holds tiles and provides collision, FOV, and drawing helpers.
    """

    def __init__(
        self,
        tiles: List[List[Tile]],
        up_stairs: Tuple[int, int] | None = None,
        down_stairs: Tuple[int, int] | None = None,
        entities: list[Entity] | None = None,
        rooms: list[RectRoom] | None = None,
    ) -> None:
        self.tiles: List[List[Tile]] = tiles
        self.height: int = len(tiles)
        self.width: int = len(tiles[0]) if self.height > 0 else 0

        # Tile coordinates of stairs (tx, ty)
        self.up_stairs: Tuple[int, int] | None = up_stairs
        self.down_stairs: Tuple[int, int] | None = down_stairs

        # Non-player entities on this map (enemies, props, etc.)
        self.entities: list[Entity] = entities if entities is not None else []

        # High-level room structures (with tags like "start", "lair", "treasure", "event")
        self.rooms: list[RectRoom] = rooms if rooms is not None else []

        # FOV / exploration state
        self.visible: Set[Tuple[int, int]] = set()
        self.explored: Set[Tuple[int, int]] = set()

    # ------------------------------------------------------------------
    # Tile helpers
    # ------------------------------------------------------------------

    def world_to_tile(self, x: float, y: float) -> Tuple[int, int]:
        """Convert pixel coordinates to tile coordinates."""
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)
        return tile_x, tile_y

    def is_walkable_tile(self, tile_x: int, tile_y: int) -> bool:
        """Check if a tile is walkable. Outside the map = not walkable."""
        if tile_x < 0 or tile_y < 0:
            return False
        if tile_y >= self.height or tile_x >= self.width:
            return False

        tile = self.tiles[tile_y][tile_x]
        return tile.walkable

    def rect_can_move_to(self, rect: pygame.Rect) -> bool:
        """
        Check if an axis-aligned rectangle can occupy a position on the map
        without intersecting a non-walkable tile.

        We sample the four corners of the rect.
        """
        points = [
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        ]

        for px, py in points:
            tile_x, tile_y = self.world_to_tile(px, py)
            if not self.is_walkable_tile(tile_x, tile_y):
                return False

        return True

    def center_entity_on_tile(
        self,
        tile_x: int,
        tile_y: int,
        entity_width: int,
        entity_height: int,
    ) -> Tuple[float, float]:
        """
        Return world coordinates to center an entity of given size on a tile.
        """
        x = tile_x * TILE_SIZE + (TILE_SIZE - entity_width) / 2
        y = tile_y * TILE_SIZE + (TILE_SIZE - entity_height) / 2
        return x, y

    def get_room_at(self, tile_x: int, tile_y: int) -> RectRoom | None:
        """
        Return the RectRoom whose interior contains this tile, or None if
        this tile is not inside any room (corridor, junction, etc.).
        """
        for room in self.rooms:
            # Interior only: walls are at x1/y1 and x2/y2 boundaries
            if room.x1 < tile_x < room.x2 and room.y1 < tile_y < room.y2:
                return room
        return None

    def get_building_at(self, tile_x: int, tile_y: int):
        """
        Return the Building whose interior contains this tile, or None if
        this tile is not inside any building.
        Only works for village maps that have village_buildings stored.
        Includes the entrance tile for better detection.
        """
        buildings = getattr(self, "village_buildings", None)
        if buildings is None:
            return None
        
        for building in buildings:
            # Check if tile is inside building interior (exclude outer walls)
            # Building interior starts at x+1, y+1 and ends at x2-1, y2-1
            is_inside = (building.x + 1 <= tile_x < building.x2 - 1 and 
                        building.y + 1 <= tile_y < building.y2 - 1)
            
            # Also check if we're on the entrance tile (which is on the wall)
            is_entrance = (building.entrance_x is not None and 
                          building.entrance_y is not None and
                          tile_x == building.entrance_x and 
                          tile_y == building.entrance_y)
            
            if is_inside or is_entrance:
                return building
        return None

    # ------------------------------------------------------------------
    # FOV helpers
    # ------------------------------------------------------------------

    def in_bounds(self, tile_x: int, tile_y: int) -> bool:
        """Return True if the tile coordinate is inside the map."""
        return 0 <= tile_x < self.width and 0 <= tile_y < self.height

    def blocks_sight(self, tile_x: int, tile_y: int) -> bool:
        """Return True if this tile blocks line of sight."""
        if not self.in_bounds(tile_x, tile_y):
            return True
        tile = self.tiles[tile_y][tile_x]
        return tile.blocks_sight

    def _bresenham_line(self, x0: int, y0: int, x1: int, y1: int):
        """Yield tile coordinates along a Bresenham line from (x0, y0) to (x1, y1)."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            yield x0, y0
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dy
                y0 += sy

    def _line_of_sight(self, x0: int, y0: int, x1: int, y1: int) -> bool:
        """
        True if there is clear LoS between (x0, y0) and (x1, y1).
        Tiles *before* the target tile can block sight.
        """
        first = True
        for tx, ty in self._bresenham_line(x0, y0, x1, y1):
            if first:
                first = False
                continue  # skip the origin
            if (tx, ty) == (x1, y1):
                return True
            if self.blocks_sight(tx, ty):
                return False
        return True

    def _cast_ray(self, x0: int, y0: int, x1: int, y1: int, radius_sq: int) -> Set[Tuple[int, int]]:
        """
        Cast a ray from (x0, y0) to (x1, y1) and return all visible tiles along the way.
        Stops when hitting a wall or going out of bounds.
        Uses a more accurate line algorithm that handles diagonals better.
        """
        visible = set()
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            # Check if we're still within radius
            dist_sq = (x - x0) * (x - x0) + (y - y0) * (y - y0)
            if dist_sq > radius_sq:
                break
                
            # Check bounds
            if not self.in_bounds(x, y):
                break
                
            # Add this tile to visible
            visible.add((x, y))
            
            # Stop if we hit a blocking tile (but still mark it as visible)
            if self.blocks_sight(x, y):
                break
                
            # Stop if we reached the target
            if x == x1 and y == y1:
                break
                
            # Bresenham's line algorithm
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
                
        return visible

    def compute_fov(self, center_tx: int, center_ty: int, radius: int = 8) -> None:
        """
        Recompute FOV from (center_tx, center_ty) using improved raycasting.
        Casts rays to all perimeter tiles to create smooth, circular FOV without diagonal artifacts.
        Fills self.visible and updates self.explored.
        
        Once a tile is explored, it stays in self.explored permanently,
        allowing it to remain visible (dimmed) even when out of FOV.
        """
        # Clear only visible tiles (not explored - those persist)
        self.visible.clear()

        if not self.in_bounds(center_tx, center_ty):
            return

        radius_sq = radius * radius

        # Always see your own tile
        self.visible.add((center_tx, center_ty))
        self.explored.add((center_tx, center_ty))

        # Cast rays in evenly spaced directions for smooth, circular FOV
        # Use 8 * radius rays for good coverage (more rays = smoother, but slower)
        num_rays = max(32, radius * 8)
        
        for i in range(num_rays):
            angle = 2 * math.pi * i / num_rays
            # Calculate target point on the circle perimeter
            target_x = center_tx + int(radius * math.cos(angle))
            target_y = center_ty + int(radius * math.sin(angle))
            
            # Cast ray and add all visible tiles
            visible_tiles = self._cast_ray(center_tx, center_ty, target_x, target_y, radius_sq)
            self.visible.update(visible_tiles)
            self.explored.update(visible_tiles)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(
            self,
            surface: pygame.Surface,
            camera_x: float = 0.0,
            camera_y: float = 0.0,
            zoom: float = 1.0,
    ) -> None:
        """
        Draw all tiles with fog-of-war, taking camera & zoom into account.

        - Never seen              -> black
        - Explored, not visible   -> slightly dimmed but clearly visible (stays "lit")
        - Visible now             -> full color
        """
        screen_w, screen_h = surface.get_size()

        if zoom <= 0:
            zoom = 1.0

        tile_screen_size = int(TILE_SIZE * zoom)
        if tile_screen_size <= 0:
            return

        # Calculate which tile range is visible on screen (optimization: only iterate visible tiles)
        # Add one extra tile on each side for safety (partial tiles at edges)
        min_tile_x = max(0, int((camera_x - tile_screen_size) / TILE_SIZE))
        max_tile_x = min(self.width, int((camera_x + screen_w + tile_screen_size) / TILE_SIZE) + 1)
        min_tile_y = max(0, int((camera_y - tile_screen_size) / TILE_SIZE))
        max_tile_y = min(self.height, int((camera_y + screen_h + tile_screen_size) / TILE_SIZE) + 1)

        # Only iterate through tiles that are potentially visible on screen
        for y in range(min_tile_y, max_tile_y):
            row = self.tiles[y]
            world_y = y * TILE_SIZE
            sy = int((world_y - camera_y) * zoom)

            # Skip row if it's completely off-screen vertically
            if sy >= screen_h or sy + tile_screen_size <= 0:
                continue

            for x in range(min_tile_x, max_tile_x):
                tile = row[x]
                world_x = x * TILE_SIZE
                sx = int((world_x - camera_x) * zoom)

                # Skip tile if it's completely off-screen horizontally
                if sx >= screen_w or sx + tile_screen_size <= 0:
                    continue

                coord = (x, y)
                rect = pygame.Rect(sx, sy, tile_screen_size, tile_screen_size)

                if coord not in self.explored:
                    # Completely unseen - pure black
                    pygame.draw.rect(surface, (0, 0, 0), rect)
                    continue

                # Try to use sprite first, fallback to color-based rendering
                sprite_used = False
                try:
                    from engine.sprites.sprites import get_sprite_manager, SpriteCategory
                    from engine.sprites.sprite_registry import get_registry, TileSpriteType
                    
                    sprite_manager = get_sprite_manager()
                    registry = get_registry()
                    
                    # Determine tile type
                    from world.tiles import FLOOR_TILE, WALL_TILE, UP_STAIRS_TILE, DOWN_STAIRS_TILE
                    if tile == FLOOR_TILE:
                        tile_type = TileSpriteType.FLOOR
                    elif tile == WALL_TILE:
                        tile_type = TileSpriteType.WALL
                    elif tile == UP_STAIRS_TILE:
                        tile_type = TileSpriteType.UP_STAIRS
                    elif tile == DOWN_STAIRS_TILE:
                        tile_type = TileSpriteType.DOWN_STAIRS
                    else:
                        tile_type = TileSpriteType.FLOOR  # Default fallback
                    
                    sprite_id = registry.get_tile_sprite_id(tile_type)
                    base_color = tile.color
                    
                    sprite = sprite_manager.get_sprite(
                        SpriteCategory.TILE,
                        sprite_id,
                        fallback_color=None,  # Don't use fallback, we'll use color-based if missing
                        size=(tile_screen_size, tile_screen_size),
                    )
                    
                    if sprite and not sprite_manager.is_sprite_fallback(sprite):
                        # Use sprite (it's a real sprite, not a fallback)
                        # Adjust brightness for visibility
                        if coord in self.visible:
                            # Currently visible - full brightness
                            sprite_surface = sprite.copy()
                        else:
                            # Explored but not currently visible - slightly dimmed
                            factor = 0.85
                            sprite_surface = sprite.copy()
                            sprite_surface.set_alpha(int(255 * factor))
                        
                        surface.blit(sprite_surface, rect)
                        sprite_used = True
                except Exception:
                    pass  # Fall through to color-based rendering
                
                # Fallback: Color-based rendering
                if not sprite_used:
                    base_color = tile.color
                    if coord in self.visible:
                        # Currently visible - full brightness
                        color = base_color
                    else:
                        # Explored but not currently visible - stays "lit" but slightly dimmed
                        # Increased from 0.6 to 0.85 for much better visibility
                        factor = 0.85
                        color = (
                            int(base_color[0] * factor),
                            int(base_color[1] * factor),
                            int(base_color[2] * factor),
                        )

                    pygame.draw.rect(surface, color, rect)
                
                # Draw stairs symbols to make them more obvious
                from world.tiles import UP_STAIRS_TILE, DOWN_STAIRS_TILE
                if tile == UP_STAIRS_TILE and coord in self.explored:
                    # Draw up arrow (^) on stairs up
                    arrow_font = pygame.font.Font(None, max(12, int(tile_screen_size * 0.6)))
                    arrow_text = arrow_font.render("^", True, (255, 255, 255))
                    arrow_x = sx + (tile_screen_size - arrow_text.get_width()) // 2
                    arrow_y = sy + (tile_screen_size - arrow_text.get_height()) // 2
                    surface.blit(arrow_text, (arrow_x, arrow_y))
                elif tile == DOWN_STAIRS_TILE and coord in self.explored:
                    # Draw down arrow (v) on stairs down
                    arrow_font = pygame.font.Font(None, max(12, int(tile_screen_size * 0.6)))
                    arrow_text = arrow_font.render("v", True, (255, 255, 255))
                    arrow_x = sx + (tile_screen_size - arrow_text.get_width()) // 2
                    arrow_y = sy + (tile_screen_size - arrow_text.get_height()) // 2
                    surface.blit(arrow_text, (arrow_x, arrow_y))

