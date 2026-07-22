"""
Ambient atmosphere for exploration dungeons and battle arenas.
Cosmetic only — does not affect FOV, pathfinding, or combat.

Performance notes:
- Reuses full-screen layers instead of allocating every frame
- Battle static backdrop is cached and only rebuilt on resize
- Particles are drawn onto a shared alpha layer (no per-particle Surfaces)
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

import pygame

from settings import TILE_SIZE
from world.tiles import FLOOR_TILE, WALL_TILE

if TYPE_CHECKING:
    from world.game_map import GameMap


def _tile_hash(x: int, y: int, salt: int = 0) -> int:
    """Stable pseudo-random from tile coords."""
    return (x * 73856093) ^ (y * 19349663) ^ (salt * 83492791)


def _get_layer(
    cache: Dict[str, pygame.Surface],
    key: str,
    size: Tuple[int, int],
) -> pygame.Surface:
    """Return a reusable SRCALPHA surface of the requested size."""
    surf = cache.get(key)
    if surf is None or surf.get_size() != size:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        cache[key] = surf
    else:
        surf.fill((0, 0, 0, 0))
    return surf


class ExplorationAtmosphere:
    """Living dungeon air: sparse torches, soft room light, dust, and mist."""

    def __init__(self) -> None:
        self.timer: float = 0.0
        self.motes: List[Dict] = []
        self.embers: List[Dict] = []
        self.torch_tiles: List[Tuple[int, int]] = []
        self._torch_anchors: Dict[Tuple[int, int], Tuple[float, float]] = {}
        self._map_id: Optional[int] = None
        self._layers: Dict[str, pygame.Surface] = {}

    def on_floor_loaded(self, game_map: "GameMap") -> None:
        """Call when a new floor is generated / loaded."""
        self._map_id = id(game_map)
        self.motes.clear()
        self.embers.clear()
        self.torch_tiles = self._find_torch_sites(game_map)
        self._torch_anchors = {
            (tx, ty): self._torch_offset(game_map, tx, ty) for tx, ty in self.torch_tiles
        }
        self._seed_motes(game_map)

    def update(self, dt: float, game_map: Optional["GameMap"]) -> None:
        if game_map is None:
            return
        if self._map_id != id(game_map):
            self.on_floor_loaded(game_map)

        self.timer += dt
        w_px = game_map.width * TILE_SIZE
        h_px = game_map.height * TILE_SIZE

        while len(self.motes) < 20:
            self.motes.append(self._make_mote(w_px, h_px))

        for mote in self.motes:
            mote["phase"] += dt * mote["speed"]
            mote["x"] += (mote["vx"] + math.sin(mote["phase"]) * 6) * dt
            mote["y"] += (mote["vy"] + math.cos(mote["phase"] * 0.7) * 4) * dt
            if mote["x"] < 0:
                mote["x"] = w_px
            elif mote["x"] > w_px:
                mote["x"] = 0
            if mote["y"] < 0:
                mote["y"] = h_px
            elif mote["y"] > h_px:
                mote["y"] = 0

        visible = game_map.visible
        if len(self.embers) < 8:
            # Avoid scanning all torches every frame
            if self.torch_tiles and random.random() < dt * 1.8:
                tx, ty = random.choice(self.torch_tiles)
                if (tx, ty) in visible:
                    self.embers.append(self._make_ember(tx, ty))

        alive = []
        for ember in self.embers:
            ember["life"] -= dt
            ember["phase"] += dt * 2.6
            ember["x"] += (ember["vx"] + math.sin(ember["phase"]) * 10) * dt
            ember["y"] += ember["vy"] * dt
            if ember["life"] > 0:
                alive.append(ember)
        self.embers = alive

    def draw(
        self,
        surface: pygame.Surface,
        game_map: "GameMap",
        camera_x: float,
        camera_y: float,
        zoom: float,
    ) -> None:
        if zoom <= 0:
            zoom = 1.0
        visible = game_map.visible
        explored = game_map.explored
        tile_px = TILE_SIZE * zoom
        size = surface.get_size()
        layer = _get_layer(self._layers, "fx", size)

        self._draw_room_ambience(
            layer, game_map, camera_x, camera_y, zoom, tile_px, visible, explored, size
        )
        self._draw_torches(
            layer, game_map, camera_x, camera_y, zoom, tile_px, visible, explored, size
        )
        self._draw_motes(layer, camera_x, camera_y, zoom, visible, game_map)
        self._draw_embers(layer, camera_x, camera_y, zoom, visible)
        surface.blit(layer, (0, 0))

    def _find_torch_sites(self, game_map: "GameMap") -> List[Tuple[int, int]]:
        sites: List[Tuple[int, int]] = []
        rooms = getattr(game_map, "rooms", None) or []

        if rooms:
            for room in rooms:
                candidates = self._room_wall_candidates(game_map, room)
                if not candidates:
                    continue
                pick = candidates[_tile_hash(room.x1, room.y1, 5) % len(candidates)]
                sites.append(pick)
                room_w = room.x2 - room.x1
                room_h = room.y2 - room.y1
                if room_w * room_h >= 80 and _tile_hash(room.x1, room.y1, 7) % 3 == 0:
                    opposite = candidates[_tile_hash(room.x2, room.y2, 11) % len(candidates)]
                    if opposite != pick:
                        sites.append(opposite)
            return sites

        for y in range(game_map.height):
            for x in range(game_map.width):
                if game_map.tiles[y][x] != FLOOR_TILE:
                    continue
                if _tile_hash(x, y, 3) % 47 != 0:
                    continue
                if self._adjacent_to_wall(game_map, x, y):
                    sites.append((x, y))
        return sites

    def _room_wall_candidates(self, game_map: "GameMap", room) -> List[Tuple[int, int]]:
        candidates: List[Tuple[int, int]] = []
        for x in range(room.x1 + 1, room.x2):
            for y in (room.y1 + 1, room.y2 - 1):
                if 0 <= x < game_map.width and 0 <= y < game_map.height:
                    if game_map.tiles[y][x] == FLOOR_TILE and self._adjacent_to_wall(game_map, x, y):
                        candidates.append((x, y))
        for y in range(room.y1 + 2, room.y2 - 1):
            for x in (room.x1 + 1, room.x2 - 1):
                if 0 <= x < game_map.width and 0 <= y < game_map.height:
                    if game_map.tiles[y][x] == FLOOR_TILE and self._adjacent_to_wall(game_map, x, y):
                        candidates.append((x, y))
        return candidates

    @staticmethod
    def _adjacent_to_wall(game_map: "GameMap", x: int, y: int) -> bool:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                if game_map.tiles[ny][nx] == WALL_TILE:
                    return True
        return False

    @staticmethod
    def _torch_offset(game_map: "GameMap", tx: int, ty: int) -> Tuple[float, float]:
        for dx, dy, px, py in (
            (0, -1, 0.5, 0.2),
            (0, 1, 0.5, 0.75),
            (-1, 0, 0.2, 0.45),
            (1, 0, 0.8, 0.45),
        ):
            nx, ny = tx + dx, ty + dy
            if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                if game_map.tiles[ny][nx] == WALL_TILE:
                    return px, py
        return 0.5, 0.35

    def _seed_motes(self, game_map: "GameMap") -> None:
        w_px = game_map.width * TILE_SIZE
        h_px = game_map.height * TILE_SIZE
        self.motes = [self._make_mote(w_px, h_px) for _ in range(18)]

    @staticmethod
    def _make_mote(w_px: float, h_px: float) -> Dict:
        return {
            "x": random.uniform(0, w_px),
            "y": random.uniform(0, h_px),
            "vx": random.uniform(-8, 8),
            "vy": random.uniform(-5, 5),
            "size": random.uniform(0.9, 1.8),
            "phase": random.uniform(0, math.pi * 2),
            "speed": random.uniform(0.6, 1.3),
            "color": random.choice([
                (170, 155, 125),
                (130, 140, 155),
                (160, 145, 120),
            ]),
            "base_alpha": random.randint(28, 55),
        }

    @staticmethod
    def _make_ember(tx: int, ty: int) -> Dict:
        wx = tx * TILE_SIZE + TILE_SIZE * 0.5 + random.uniform(-4, 4)
        wy = ty * TILE_SIZE + TILE_SIZE * 0.3 + random.uniform(-3, 3)
        return {
            "x": wx,
            "y": wy,
            "vx": random.uniform(-8, 8),
            "vy": random.uniform(-28, -12),
            "life": random.uniform(0.45, 1.1),
            "max_life": 1.1,
            "size": random.uniform(1.0, 2.2),
            "phase": random.uniform(0, math.pi * 2),
            "color": random.choice([
                (255, 170, 70),
                (255, 130, 50),
                (255, 210, 120),
            ]),
        }

    def _draw_room_ambience(
        self,
        layer: pygame.Surface,
        game_map: "GameMap",
        camera_x: float,
        camera_y: float,
        zoom: float,
        tile_px: float,
        visible: Set[Tuple[int, int]],
        explored: Set[Tuple[int, int]],
        size: Tuple[int, int],
    ) -> None:
        screen_w, screen_h = size
        rooms = getattr(game_map, "rooms", None) or []
        pulse = 0.5 + 0.5 * math.sin(self.timer * 0.55)

        for room in rooms:
            cx = (room.x1 + room.x2) * 0.5 * TILE_SIZE
            cy = (room.y1 + room.y2) * 0.5 * TILE_SIZE
            sx = int((cx - camera_x) * zoom)
            sy = int((cy - camera_y) * zoom)
            room_w = (room.x2 - room.x1) * TILE_SIZE * zoom
            room_h = (room.y2 - room.y1) * TILE_SIZE * zoom
            if sx + room_w < -40 or sy + room_h < -40 or sx - room_w > screen_w + 40 or sy - room_h > screen_h + 40:
                continue

            samples = (
                (int(cx // TILE_SIZE), int(cy // TILE_SIZE)),
                (room.x1 + 1, room.y1 + 1),
                (room.x2 - 1, room.y2 - 1),
            )
            room_visible = any(sample in visible for sample in samples)
            if not room_visible and samples[0] not in explored:
                continue

            radius = int(max(room_w, room_h) * 0.5)
            if radius <= 0:
                continue
            alpha = int((18 + 8 * pulse) if room_visible else 6)
            # One soft circle instead of three nested ones
            pygame.draw.circle(layer, (210, 150, 90, alpha), (sx, sy), radius)
            if room_visible and radius > 8:
                pygame.draw.circle(
                    layer,
                    (230, 180, 110, int(alpha * 0.7)),
                    (sx, sy),
                    max(4, radius // 3),
                )

    def _draw_torches(
        self,
        layer: pygame.Surface,
        game_map: "GameMap",
        camera_x: float,
        camera_y: float,
        zoom: float,
        tile_px: float,
        visible: Set[Tuple[int, int]],
        explored: Set[Tuple[int, int]],
        size: Tuple[int, int],
    ) -> None:
        screen_w, screen_h = size
        for tx, ty in self.torch_tiles:
            if (tx, ty) not in explored:
                continue
            sx = int((tx * TILE_SIZE - camera_x) * zoom)
            sy = int((ty * TILE_SIZE - camera_y) * zoom)
            if sx + tile_px * 2 < 0 or sy + tile_px * 2 < 0 or sx > screen_w or sy > screen_h:
                continue

            in_view = (tx, ty) in visible
            # Skip dim off-screen explored torches unless nearby
            if not in_view:
                continue

            flicker = 0.65 + 0.35 * abs(math.sin(self.timer * 6.0 + _tile_hash(tx, ty) * 0.04))
            ox, oy = self._torch_anchors.get((tx, ty), (0.5, 0.35))
            cx = int(sx + tile_px * ox)
            cy = int(sy + tile_px * oy)
            radius = int(tile_px * (1.05 + 0.15 * flicker))

            pygame.draw.circle(layer, (255, 145, 55, int(28 * flicker)), (cx, cy), radius)
            pygame.draw.circle(layer, (255, 180, 80, int(70 * flicker)), (cx, cy), max(2, radius // 3))

            if tile_px >= 12:
                bracket = max(2, int(tile_px * 0.08))
                pygame.draw.rect(
                    layer,
                    (70, 55, 40, 200),
                    (cx - bracket, cy, bracket * 2, int(tile_px * 0.18)),
                )
                flame_h = max(3, int(tile_px * 0.18 * flicker))
                pygame.draw.ellipse(
                    layer,
                    (255, 220, 130, int(160 * flicker)),
                    (cx - 2, cy - flame_h, 4, flame_h + 2),
                )

    def _draw_motes(
        self,
        layer: pygame.Surface,
        camera_x: float,
        camera_y: float,
        zoom: float,
        visible: Set[Tuple[int, int]],
        game_map: "GameMap",
    ) -> None:
        for mote in self.motes:
            tx = int(mote["x"] // TILE_SIZE)
            ty = int(mote["y"] // TILE_SIZE)
            if (tx, ty) not in visible:
                continue
            if not (0 <= tx < game_map.width and 0 <= ty < game_map.height):
                continue
            if game_map.tiles[ty][tx] == WALL_TILE:
                continue
            sx = int((mote["x"] - camera_x) * zoom)
            sy = int((mote["y"] - camera_y) * zoom)
            alpha = int(mote["base_alpha"] * (0.5 + 0.5 * abs(math.sin(mote["phase"]))))
            size = max(1, int(mote["size"] * zoom))
            pygame.draw.circle(layer, (*mote["color"], alpha), (sx, sy), size)

    def _draw_embers(
        self,
        layer: pygame.Surface,
        camera_x: float,
        camera_y: float,
        zoom: float,
        visible: Set[Tuple[int, int]],
    ) -> None:
        for ember in self.embers:
            tx = int(ember["x"] // TILE_SIZE)
            ty = int(ember["y"] // TILE_SIZE)
            if (tx, ty) not in visible:
                continue
            life_t = max(0.0, ember["life"] / ember["max_life"])
            sx = int((ember["x"] - camera_x) * zoom)
            sy = int((ember["y"] - camera_y) * zoom)
            size = max(1, int(ember["size"] * zoom * (0.5 + 0.5 * life_t)))
            alpha = int(170 * life_t)
            pygame.draw.circle(layer, (*ember["color"], alpha // 3), (sx, sy), size * 2)
            pygame.draw.circle(layer, (*ember["color"], alpha), (sx, sy), size)


class BattleAtmosphere:
    """Dungeon-chamber backdrop and ambient life for the battle arena."""

    def __init__(self) -> None:
        self.timer: float = 0.0
        self.particles: List[Dict] = []
        self.embers: List[Dict] = []
        self.mist: List[Dict] = []
        self._ember_cd: float = 0.0
        self._layers: Dict[str, pygame.Surface] = {}
        self._static_backdrop: Optional[pygame.Surface] = None
        self._static_size: Tuple[int, int] = (0, 0)
        self._init_particles()

    def _init_particles(self) -> None:
        self.particles = [self._make_dust() for _ in range(16)]
        self.mist = []
        for i in range(3):
            self.mist.append({
                "y_ratio": 0.3 + i * 0.18,
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.12, 0.25),
                "height": random.randint(40, 64),
                "alpha": random.randint(12, 20),
            })

    @staticmethod
    def _make_dust() -> Dict:
        return {
            "x": random.uniform(0, 1280),
            "y": random.uniform(0, 720),
            "vx": random.uniform(-10, 10),
            "vy": random.uniform(-7, 7),
            "size": random.uniform(1.0, 2.0),
            "phase": random.uniform(0, math.pi * 2),
            "color": random.choice([
                (170, 155, 130),
                (140, 145, 165),
                (160, 140, 120),
            ]),
            "base_alpha": random.randint(22, 50),
        }

    def update(self, dt: float, screen_w: int, screen_h: int) -> None:
        self.timer += dt
        self._ember_cd -= dt

        for p in self.particles:
            p["phase"] += dt * 1.15
            p["x"] += (p["vx"] + math.sin(p["phase"]) * 8) * dt
            p["y"] += (p["vy"] + math.cos(p["phase"] * 0.8) * 5) * dt
            if p["x"] < -10:
                p["x"] = screen_w + 10
            elif p["x"] > screen_w + 10:
                p["x"] = -10
            if p["y"] < -10:
                p["y"] = screen_h + 10
            elif p["y"] > screen_h + 10:
                p["y"] = -10

        for band in self.mist:
            band["phase"] += dt * band["speed"]

        if self._ember_cd <= 0:
            self._ember_cd = random.uniform(0.35, 0.7)
            side = random.choice(("left", "right"))
            x = screen_w * (random.uniform(0.06, 0.18) if side == "left" else random.uniform(0.82, 0.94))
            self.embers.append({
                "x": x,
                "y": screen_h * random.uniform(0.58, 0.85),
                "vx": random.uniform(-14, 14),
                "vy": random.uniform(-48, -22),
                "life": random.uniform(0.5, 1.2),
                "max_life": 1.2,
                "size": random.uniform(1.2, 2.4),
                "phase": random.uniform(0, math.pi * 2),
                "color": random.choice([
                    (255, 160, 70),
                    (255, 120, 50),
                    (255, 210, 120),
                ]),
            })

        alive = []
        for ember in self.embers:
            ember["life"] -= dt
            ember["phase"] += dt * 2.5
            ember["x"] += (ember["vx"] + math.sin(ember["phase"]) * 12) * dt
            ember["y"] += ember["vy"] * dt
            if ember["life"] > 0:
                alive.append(ember)
        self.embers = alive[:10]

    def _rebuild_static_backdrop(self, screen_w: int, screen_h: int) -> pygame.Surface:
        """Heavy chamber art — built once per resolution."""
        surf = pygame.Surface((screen_w, screen_h))

        # Gradient via a few large bands (not per-scanline)
        bands = (
            (0.00, 0.35, (18, 16, 28), (28, 24, 36)),
            (0.35, 0.65, (28, 24, 36), (36, 28, 32)),
            (0.65, 1.00, (36, 28, 32), (48, 36, 34)),
        )
        for y0r, y1r, c0, c1 in bands:
            y0 = int(screen_h * y0r)
            y1 = int(screen_h * y1r)
            steps = max(1, (y1 - y0) // 8)
            for i in range(steps):
                t = i / steps
                color = (
                    int(c0[0] + (c1[0] - c0[0]) * t),
                    int(c0[1] + (c1[1] - c0[1]) * t),
                    int(c0[2] + (c1[2] - c0[2]) * t),
                )
                yy = y0 + i * 8
                pygame.draw.rect(surf, color, (0, yy, screen_w, 9))

        # Back wall
        wall_y = int(screen_h * 0.18)
        wall_h = int(screen_h * 0.42)
        wall = pygame.Surface((screen_w, wall_h), pygame.SRCALPHA)
        wall.fill((55, 48, 46, 90))
        for ly in range(10, wall_h, 18):
            pygame.draw.line(wall, (35, 30, 28, 70), (0, ly), (screen_w, ly), 1)
        surf.blit(wall, (0, wall_y))

        # Floor plane
        floor = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        floor_top = int(screen_h * 0.58)
        steps = max(1, (screen_h - floor_top) // 10)
        for i in range(steps):
            t = i / steps
            alpha = int(40 + 70 * t)
            yy = floor_top + i * 10
            pygame.draw.rect(floor, (42, 36, 34, alpha), (0, yy, screen_w, 11))
        mid_x = screen_w // 2
        for k in range(-4, 5):
            x0 = mid_x + k * int(screen_w * 0.08)
            pygame.draw.line(
                floor,
                (60, 52, 48, 35),
                (x0, floor_top),
                (mid_x + k * int(screen_w * 0.22), screen_h),
                1,
            )
        surf.blit(floor, (0, 0))

        # Pillars
        pillar_w = max(28, screen_w // 28)
        top = int(screen_h * 0.12)
        bottom = int(screen_h * 0.85)
        for side, x in (("left", int(screen_w * 0.04)), ("right", int(screen_w * 0.96) - pillar_w)):
            pygame.draw.rect(surf, (52, 46, 42), (x, top, pillar_w, bottom - top))
            hx = x + 3 if side == "left" else x + pillar_w - 5
            pygame.draw.rect(surf, (78, 70, 62), (hx, top, 3, bottom - top))
            pygame.draw.rect(surf, (62, 54, 48), (x - 6, top, pillar_w + 12, 14))
            pygame.draw.rect(surf, (62, 54, 48), (x - 8, bottom - 18, pillar_w + 16, 18))
        for x in (int(screen_w * 0.14), int(screen_w * 0.86) - pillar_w // 2):
            pygame.draw.rect(surf, (42, 38, 36), (x, int(screen_h * 0.2), pillar_w // 2, int(screen_h * 0.55)))

        # Soft vignette (coarse bands, not per-pixel)
        vignette = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        band = max(40, min(screen_w, screen_h) // 7)
        step = 4
        for i in range(0, band, step):
            t = 1.0 - (i / band)
            a = int(100 * (t * t))
            pygame.draw.rect(vignette, (0, 0, 0, a), (0, i, screen_w, step))
            pygame.draw.rect(vignette, (0, 0, 0, a), (0, screen_h - i - step, screen_w, step))
            pygame.draw.rect(vignette, (0, 0, 0, a), (i, 0, step, screen_h))
            pygame.draw.rect(vignette, (0, 0, 0, a), (screen_w - i - step, 0, step, screen_h))
        surf.blit(vignette, (0, 0))

        self._static_backdrop = surf
        self._static_size = (screen_w, screen_h)
        return surf

    def draw_scene_backdrop(self, surface: pygame.Surface) -> None:
        """Blit cached chamber + cheap animated overlays."""
        screen_w, screen_h = surface.get_size()
        if self._static_backdrop is None or self._static_size != (screen_w, screen_h):
            self._rebuild_static_backdrop(screen_w, screen_h)

        surface.blit(self._static_backdrop, (0, 0))

        pulse = 0.5 + 0.5 * math.sin(self.timer * 0.45)
        overlay = _get_layer(self._layers, "dyn", (screen_w, screen_h))

        # Light shaft
        shaft_x = screen_w * (0.42 + 0.08 * math.sin(self.timer * 0.2))
        shaft_w = screen_w * (0.16 + 0.03 * math.sin(self.timer * 0.35))
        points = [
            (shaft_x - shaft_w * 0.15, -20),
            (shaft_x + shaft_w * 0.15, -20),
            (shaft_x + shaft_w, screen_h * 0.75),
            (shaft_x - shaft_w, screen_h * 0.75),
        ]
        pygame.draw.polygon(overlay, (255, 200, 140, int(14 + 7 * pulse)), points)

        # Mist
        for band in self.mist:
            y = int(screen_h * band["y_ratio"] + math.sin(band["phase"]) * 10)
            drift = math.sin(band["phase"] * 0.7) * (screen_w * 0.05)
            alpha = int(band["alpha"] * (0.7 + 0.3 * abs(math.sin(band["phase"]))))
            pygame.draw.ellipse(
                overlay,
                (90, 75, 60, alpha),
                (int(-screen_w * 0.1 + drift), y - band["height"] // 2, int(screen_w * 1.2), band["height"]),
            )

        # Brazier glows (simple circles, no extra Surfaces)
        for cx, cy, phase in (
            (int(screen_w * 0.08), int(screen_h * 0.72), 0.0),
            (int(screen_w * 0.92), int(screen_h * 0.72), 1.7),
        ):
            flicker = 0.55 + 0.45 * abs(math.sin(self.timer * 6.5 + phase))
            pygame.draw.circle(
                overlay,
                (255, 130, 50, int(40 * flicker)),
                (cx, cy - 10),
                int(22 + 5 * flicker),
            )
            pygame.draw.circle(
                overlay,
                (255, 210, 120, int(90 * flicker)),
                (cx, cy - 14),
                int(7 + 2 * flicker),
            )
            pygame.draw.ellipse(overlay, (70, 55, 40, 200), (cx - 14, cy, 28, 10))
            pygame.draw.rect(overlay, (55, 45, 35, 200), (cx - 4, cy + 8, 8, 22))

        surface.blit(overlay, (0, 0))

    def draw_background(
        self,
        surface: pygame.Surface,
        grid_origin_x: float,
        grid_origin_y: float,
        grid_w: int,
        grid_h: int,
        cell_size: int,
    ) -> None:
        """Arena platform under the grid + drifting dust."""
        screen_w, screen_h = surface.get_size()
        ax = int(grid_origin_x)
        ay = int(grid_origin_y)
        aw = grid_w * cell_size
        ah = grid_h * cell_size
        pulse = 0.5 + 0.5 * math.sin(self.timer * 0.7)

        layer = _get_layer(self._layers, "arena", (screen_w, screen_h))
        pygame.draw.rect(layer, (0, 0, 0, 60), (ax - 4, ay + 8, aw + 24, ah + 16), border_radius=10)
        pygame.draw.rect(layer, (48, 42, 40, int(110 + 16 * pulse)), (ax - 12, ay - 12, aw + 24, ah + 24), border_radius=10)
        pygame.draw.rect(layer, (255, 170, 90, int(24 + 10 * pulse)), (ax - 12, ay - 12, aw + 24, ah + 24), width=2, border_radius=10)

        for p in self.particles:
            alpha = int(p["base_alpha"] * (0.55 + 0.45 * abs(math.sin(p["phase"]))))
            size = max(1, int(p["size"]))
            pygame.draw.circle(layer, (*p["color"], alpha), (int(p["x"]), int(p["y"])), size)

        surface.blit(layer, (0, 0))

    def draw_cell_life(
        self,
        surface: pygame.Surface,
        gx: int,
        gy: int,
        x: int,
        y: int,
        cell_size: int,
        terrain_type: str,
    ) -> None:
        """Cheap solid cell tint — no per-cell Surface allocation."""
        pulse = 0.5 + 0.5 * math.sin(self.timer * 1.2 + gx * 0.7 + gy * 0.5)
        shade = 6 if (gx + gy) % 2 == 0 else 0
        base = (
            52 + shade + int(4 * pulse),
            48 + shade + int(3 * pulse),
            46 + shade,
        )
        pygame.draw.rect(surface, base, (x, y, cell_size, cell_size))

        if terrain_type == "hazard":
            flicker = 0.5 + 0.5 * abs(math.sin(self.timer * 4.5 + gx + gy))
            # Approximate translucent red with a darker blend toward red
            tint = (
                min(255, int(base[0] * 0.45 + 160 * flicker)),
                max(0, int(base[1] * 0.45)),
                max(0, int(base[2] * 0.45)),
            )
            pygame.draw.rect(surface, tint, (x, y, cell_size, cell_size))
        elif terrain_type == "cover":
            tint = (
                max(0, int(base[0] * 0.55 + 30)),
                min(255, int(base[1] * 0.55 + 70)),
                max(0, int(base[2] * 0.55 + 35)),
            )
            pygame.draw.rect(surface, tint, (x, y, cell_size, cell_size))
        elif terrain_type == "obstacle":
            # Keep atmosphere fill very dark so the obstacle block reads clearly
            pygame.draw.rect(surface, (14, 12, 14), (x, y, cell_size, cell_size))

    def draw_foreground(
        self,
        surface: pygame.Surface,
        grid_origin_x: float,
        grid_origin_y: float,
        grid_w: int,
        grid_h: int,
        cell_size: int,
    ) -> None:
        """Embers over the arena (under units)."""
        if not self.embers:
            return
        screen_w, screen_h = surface.get_size()
        layer = _get_layer(self._layers, "embers", (screen_w, screen_h))
        ax = grid_origin_x
        ay = grid_origin_y
        aw = grid_w * cell_size
        ah = grid_h * cell_size

        for ember in self.embers:
            over = ax <= ember["x"] <= ax + aw and ay <= ember["y"] <= ay + ah
            life_t = max(0.0, ember["life"] / ember["max_life"])
            alpha = int((180 if over else 100) * life_t)
            size = max(1, int(ember["size"] * (0.5 + 0.5 * life_t)))
            x = int(ember["x"])
            y = int(ember["y"])
            pygame.draw.circle(layer, (*ember["color"], alpha // 3), (x, y), size * 2)
            pygame.draw.circle(layer, (*ember["color"], alpha), (x, y), size)

        surface.blit(layer, (0, 0))
