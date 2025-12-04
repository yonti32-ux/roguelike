# world/entities.py

from dataclasses import dataclass
from typing import Tuple

import pygame

from settings import COLOR_PLAYER, COLOR_ENEMY


@dataclass
class Entity:
    """Base entity that lives in the world."""
    x: float
    y: float
    width: int
    height: int
    blocks_movement: bool = True

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def move_to(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def move_by(self, dx: float, dy: float) -> None:
        self.x += dx
        self.y += dy

    def draw(
            self,
            surface: pygame.Surface,
            camera_x: float = 0.0,
            camera_y: float = 0.0,
            zoom: float = 1.0,
    ) -> None:
        """
        Generic entity draw using camera & zoom.
        Subclasses can override for custom colors/shapes.
        """
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        color = getattr(self, "color", (255, 0, 255))
        pygame.draw.rect(surface, color, screen_rect)


@dataclass
class Player(Entity):
    """
    Player entity.
    Later we'll add class, stats, inventory, etc.
    """
    speed: float = 200.0
    color: Tuple[int, int, int] = COLOR_PLAYER

    max_hp: int = 30
    hp: int = 30
    attack_power: int = 6

    def draw(
            self,
            surface: pygame.Surface,
            camera_x: float = 0.0,
            camera_y: float = 0.0,
            zoom: float = 1.0,
    ) -> None:
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        pygame.draw.rect(surface, self.color, screen_rect)

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass
class Enemy(Entity):
    """Simple enemy placeholder (no AI yet, just blocks & takes hits)."""
    speed: float = 0.0  # will matter once we add AI
    color: Tuple[int, int, int] = COLOR_ENEMY

    max_hp: int = 12
    hp: int = 12
    attack_power: int = 4

    def draw(
            self,
            surface: pygame.Surface,
            camera_x: float = 0.0,
            camera_y: float = 0.0,
            zoom: float = 1.0,
    ) -> None:
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        pygame.draw.rect(surface, self.color, screen_rect)

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass
class Chest(Entity):
    """Simple interactive chest placed on the exploration map.

    - Does NOT block movement (player can stand on the tile).
    - Can be opened once; Game.try_open_chest() handles the loot logic.
    """
    opened: bool = False
    color_closed: Tuple[int, int, int] = (210, 180, 80)   # gold-ish
    color_opened: Tuple[int, int, int] = (120, 120, 120)  # dull grey

    def __post_init__(self) -> None:
        # Chests should not block movement in exploration.
        self.blocks_movement = False

    def draw(
            self,
            surface: pygame.Surface,
            camera_x: float = 0.0,
            camera_y: float = 0.0,
            zoom: float = 1.0,
    ) -> None:
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        color = self.color_opened if self.opened else self.color_closed
        pygame.draw.rect(surface, color, screen_rect)


@dataclass
class EventNode(Entity):
    """
    Interactive map event (shrine, lore stone, cache, etc.).

    - Does NOT block movement.
    - Interacting with it triggers a systems.events handler.
    """
    event_id: str = "shrine_of_power"
    color: Tuple[int, int, int] = (150, 120, 255)

    def __post_init__(self) -> None:
        self.blocks_movement = False

    def draw(
            self,
            surface: pygame.Surface,
            camera_x: float = 0.0,
            camera_y: float = 0.0,
            zoom: float = 1.0,
    ) -> None:
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        pygame.draw.rect(surface, self.color, screen_rect)

