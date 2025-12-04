# world/game_map.py

from typing import List, Tuple, Set

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

    def compute_fov(self, center_tx: int, center_ty: int, radius: int = 8) -> None:
        """
        Recompute FOV from (center_tx, center_ty).
        Fills self.visible and updates self.explored.
        """
        self.visible.clear()

        if not self.in_bounds(center_tx, center_ty):
            return

        radius_sq = radius * radius

        # Always see your own tile
        self.visible.add((center_tx, center_ty))
        self.explored.add((center_tx, center_ty))

        for ty in range(center_ty - radius, center_ty + radius + 1):
            for tx in range(center_tx - radius, center_tx + radius + 1):
                if not self.in_bounds(tx, ty):
                    continue
                dx = tx - center_tx
                dy = ty - center_ty
                if dx * dx + dy * dy > radius_sq:
                    continue
                if (tx, ty) == (center_tx, center_ty):
                    continue
                if self._line_of_sight(center_tx, center_ty, tx, ty):
                    self.visible.add((tx, ty))
                    self.explored.add((tx, ty))

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
        - Explored, not visible   -> darkened
        - Visible now             -> full color
        """
        screen_w, screen_h = surface.get_size()

        if zoom <= 0:
            zoom = 1.0

        tile_screen_size = int(TILE_SIZE * zoom)
        if tile_screen_size <= 0:
            return

        for y, row in enumerate(self.tiles):
            world_y = y * TILE_SIZE
            sy = int((world_y - camera_y) * zoom)

            # Skip row if it's completely off-screen vertically
            if sy >= screen_h or sy + tile_screen_size <= 0:
                continue

            for x, tile in enumerate(row):
                world_x = x * TILE_SIZE
                sx = int((world_x - camera_x) * zoom)

                # Skip tile if it's completely off-screen horizontally
                if sx >= screen_w or sx + tile_screen_size <= 0:
                    continue

                coord = (x, y)
                rect = pygame.Rect(sx, sy, tile_screen_size, tile_screen_size)

                if coord not in self.explored:
                    # Completely unseen
                    pygame.draw.rect(surface, (0, 0, 0), rect)
                    continue

                base_color = tile.color
                if coord in self.visible:
                    color = base_color
                else:
                    # Seen before, but not in current FOV
                    factor = 0.6  # dim but clearly different from black
                    color = (
                        int(base_color[0] * factor),
                        int(base_color[1] * factor),
                        int(base_color[2] * factor),
                    )

                pygame.draw.rect(surface, color, rect)

