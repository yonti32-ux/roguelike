from dataclasses import dataclass
from typing import Tuple, Optional

import pygame

from settings import COLOR_PLAYER, COLOR_ENEMY
from engine.sprites.sprite_helpers import draw_sprite_with_camera
from engine.sprites.sprites import get_sprite_manager, SpriteCategory
from engine.sprites.sprite_registry import get_registry, EntitySpriteType


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
        # Try to use sprite first, fallback to color-based rendering
        sprite_id = None
        sprite_manager = None
        try:
            sprite_manager = get_sprite_manager()
            registry = get_registry()
            
            sprite_id = registry.get_entity_sprite_id(EntitySpriteType.PLAYER)
            sprite = sprite_manager.get_sprite(
                SpriteCategory.ENTITY,
                sprite_id,
                fallback_color=None,  # Don't use fallback, we'll use color-based if missing
                size=(self.width, self.height),
            )
            
            if sprite and not sprite_manager.is_sprite_fallback(sprite):
                # Use sprite (it's a real sprite, not a fallback)
                # Get original size for debug overlay
                original_sprite = sprite_manager.get_sprite(
                    SpriteCategory.ENTITY,
                    sprite_id,
                    fallback_color=None,
                    size=None,  # Get at canonical size
                )
                original_size = original_sprite.get_size() if original_sprite else sprite.get_size()
                draw_sprite_with_camera(
                    surface, sprite,
                    self.x, self.y,
                    camera_x, camera_y, zoom,
                    sprite_id=sprite_id,
                    original_size=original_size,
                    sprite_manager=sprite_manager,
                )
                return
        except Exception:
            pass  # Fall through to color-based rendering
        
        # Fallback: Color-based rendering
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        pygame.draw.rect(surface, self.color, screen_rect)
        
        # Draw debug overlay even in fallback rendering if enabled
        if sprite_id and sprite_manager:
            from engine.sprites.sprite_helpers import draw_sprite_debug_overlay
            draw_sprite_debug_overlay(
                surface, None, sprite_id, sx, sy,
                sw, sh,
                original_size=None,
                requested_size=(self.width, self.height),
                sprite_manager=sprite_manager,
            )

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
        # Try to use sprite first, fallback to color-based rendering
        sprite_id = None
        sprite_manager = None
        try:
            sprite_manager = get_sprite_manager()
            registry = get_registry()
            
            # Get enemy type for sprite lookup
            enemy_type = getattr(self, "archetype_id", None) or "default"
            sprite_id = registry.get_enemy_sprite_id(enemy_type)
            
            sprite = sprite_manager.get_sprite(
                SpriteCategory.ENTITY,
                sprite_id,
                fallback_color=None,  # Don't use fallback, we'll use color-based if missing
                size=(self.width, self.height),
            )
            
            if sprite and not sprite_manager.is_sprite_fallback(sprite):
                # Use sprite (it's a real sprite, not a fallback)
                # Get original size for debug overlay
                original_sprite = sprite_manager.get_sprite(
                    SpriteCategory.ENTITY,
                    sprite_id,
                    fallback_color=None,
                    size=None,  # Get at canonical size
                )
                original_size = original_sprite.get_size() if original_sprite else sprite.get_size()
                draw_sprite_with_camera(
                    surface, sprite,
                    self.x, self.y,
                    camera_x, camera_y, zoom,
                    sprite_id=sprite_id,
                    original_size=original_size,
                    sprite_manager=sprite_manager,
                )
                
                # Still draw elite glow if needed
                is_elite = getattr(self, "is_elite", False)
                if is_elite:
                    world_rect = self.rect
                    if zoom <= 0:
                        zoom = 1.0
                    sx = int((world_rect.x - camera_x) * zoom)
                    sy = int((world_rect.y - camera_y) * zoom)
                    sw = max(1, int(world_rect.width * zoom))
                    sh = max(1, int(world_rect.height * zoom))
                    
                    glow_size = 3
                    glow_rect = pygame.Rect(
                        sx - glow_size,
                        sy - glow_size,
                        sw + glow_size * 2,
                        sh + glow_size * 2
                    )
                    glow_color = (255, 220, 100, 100)
                    glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect())
                    surface.blit(glow_surf, (glow_rect.x, glow_rect.y))
                    
                    screen_rect = pygame.Rect(sx, sy, sw, sh)
                    border_color = (255, 200, 50)
                    pygame.draw.rect(surface, border_color, screen_rect, width=2)
                return
        except Exception:
            pass  # Fall through to color-based rendering
        
        # Fallback: Color-based rendering
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        
        # Elite enemies get a pulsing glow effect
        is_elite = getattr(self, "is_elite", False)
        if is_elite:
            # Draw outer glow (static glow for exploration view)
            # Create a slightly larger glow rect
            glow_size = 3
            glow_rect = pygame.Rect(
                sx - glow_size,
                sy - glow_size,
                sw + glow_size * 2,
                sh + glow_size * 2
            )
            
            # Elite glow color (yellow/gold tint)
            glow_color = (255, 220, 100, 100)  # Semi-transparent yellow
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect())
            surface.blit(glow_surf, (glow_rect.x, glow_rect.y))
            
            # Draw bright border around elite enemy
            border_color = (255, 200, 50)  # Bright gold
            pygame.draw.rect(surface, border_color, screen_rect, width=2)
        
        pygame.draw.rect(surface, self.color, screen_rect)
        
        # Draw debug overlay even in fallback rendering if enabled
        if sprite_id and sprite_manager:
            from engine.sprites.sprite_helpers import draw_sprite_debug_overlay
            draw_sprite_debug_overlay(
                surface, None, sprite_id, sx, sy,
                sw, sh,
                original_size=None,
                requested_size=(self.width, self.height),
                sprite_manager=sprite_manager,
            )

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
        # Try to use sprite first, fallback to color-based rendering
        sprite_id = None
        sprite_manager = None
        try:
            sprite_manager = get_sprite_manager()
            registry = get_registry()
            
            sprite_id = registry.get_entity_sprite_id(EntitySpriteType.CHEST)
            variant = "opened" if self.opened else "closed"
            fallback_color = self.color_opened if self.opened else self.color_closed
            
            sprite = sprite_manager.get_sprite(
                SpriteCategory.ENTITY,
                sprite_id,
                variant=variant,
                fallback_color=None,  # Don't use fallback, we'll use color-based if missing
                size=(self.width, self.height),
            )
            
            if sprite and not sprite_manager.is_sprite_fallback(sprite):
                # Use sprite (it's a real sprite, not a fallback)
                # Get original size for debug overlay
                original_sprite = sprite_manager.get_sprite(
                    SpriteCategory.ENTITY,
                    sprite_id,
                    variant=variant,
                    fallback_color=None,
                    size=None,  # Get at canonical size
                )
                original_size = original_sprite.get_size() if original_sprite else sprite.get_size()
                draw_sprite_with_camera(
                    surface, sprite,
                    self.x, self.y,
                    camera_x, camera_y, zoom,
                    sprite_id=sprite_id,
                    original_size=original_size,
                    sprite_manager=sprite_manager,
                )
                return
        except Exception:
            pass  # Fall through to color-based rendering
        
        # Fallback: Color-based rendering
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
        
        # Draw debug overlay even in fallback rendering if enabled
        if sprite_id and sprite_manager:
            from engine.sprites.sprite_helpers import draw_sprite_debug_overlay
            draw_sprite_debug_overlay(
                surface, None, sprite_id, sx, sy,
                sw, sh,
                original_size=None,
                requested_size=(self.width, self.height),
                sprite_manager=sprite_manager,
            )


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


@dataclass
class Merchant(Entity):
    """
    Stationary merchant NPC used in shop rooms.

    - Blocks movement so the player walks around them.
    - Interaction (press E near them) is handled by ExplorationController.
    """
    color: Tuple[int, int, int] = (200, 180, 255)

    def __post_init__(self) -> None:
        # Merchants should feel like solid NPCs.
        self.blocks_movement = True
    
    def draw(
        self,
        surface: pygame.Surface,
        camera_x: float = 0.0,
        camera_y: float = 0.0,
        zoom: float = 1.0,
    ) -> None:
        # Try to use sprite first, fallback to color-based rendering
        sprite_id = None
        sprite_manager = None
        try:
            sprite_manager = get_sprite_manager()
            registry = get_registry()
            
            sprite_id = registry.get_entity_sprite_id(EntitySpriteType.MERCHANT)
            sprite = sprite_manager.get_sprite(
                SpriteCategory.ENTITY,
                sprite_id,
                fallback_color=None,  # Don't use fallback, we'll use color-based if missing
                size=(self.width, self.height),
            )
            
            if sprite and not sprite_manager.is_sprite_fallback(sprite):
                # Use sprite (it's a real sprite, not a fallback)
                # Get original size for debug overlay
                original_sprite = sprite_manager.get_sprite(
                    SpriteCategory.ENTITY,
                    sprite_id,
                    fallback_color=None,
                    size=None,  # Get at canonical size
                )
                original_size = original_sprite.get_size() if original_sprite else sprite.get_size()
                draw_sprite_with_camera(
                    surface, sprite,
                    self.x, self.y,
                    camera_x, camera_y, zoom,
                    sprite_id=sprite_id,
                    original_size=original_size,
                    sprite_manager=sprite_manager,
                )
                return
        except Exception:
            pass  # Fall through to color-based rendering
        
        # Fallback: Color-based rendering
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        pygame.draw.rect(surface, self.color, screen_rect)
        
        # Draw debug overlay even in fallback rendering if enabled
        if sprite_id and sprite_manager:
            from engine.sprites.sprite_helpers import draw_sprite_debug_overlay
            draw_sprite_debug_overlay(
                surface, None, sprite_id, sx, sy,
                sw, sh,
                original_size=None,
                requested_size=(self.width, self.height),
                sprite_manager=sprite_manager,
            )


@dataclass
class Trap(Entity):
    """
    Environmental trap that triggers when stepped on.
    
    - Does NOT block movement (player can walk over it).
    - Triggers when player's center is within trigger radius.
    - Can be detected (becomes visible) and disarmed.
    - Once triggered or disarmed, becomes inactive.
    """
    trap_id: str = "spike_trap"
    detected: bool = False  # If True, trap is visible to player
    triggered: bool = False  # If True, trap has been activated
    disarmed: bool = False  # If True, trap was safely disarmed
    color_hidden: Tuple[int, int, int] = (80, 80, 80)  # Subtle gray when hidden
    color_detected: Tuple[int, int, int] = (200, 150, 50)  # Orange when detected
    color_triggered: Tuple[int, int, int] = (150, 150, 150)  # Gray when triggered/disarmed
    
    def __post_init__(self) -> None:
        # Traps don't block movement - you walk over them
        self.blocks_movement = False
    
    @property
    def is_active(self) -> bool:
        """Return True if trap can still trigger."""
        return not (self.triggered or self.disarmed)
    
    def draw(
        self,
        surface: pygame.Surface,
        camera_x: float = 0.0,
        camera_y: float = 0.0,
        zoom: float = 1.0,
    ) -> None:
        """Draw trap with visual state based on detection/trigger status."""
        world_rect = self.rect
        if zoom <= 0:
            zoom = 1.0

        sx = int((world_rect.x - camera_x) * zoom)
        sy = int((world_rect.y - camera_y) * zoom)
        sw = max(1, int(world_rect.width * zoom))
        sh = max(1, int(world_rect.height * zoom))

        screen_rect = pygame.Rect(sx, sy, sw, sh)
        
        # Choose color based on state
        if self.triggered or self.disarmed:
            color = self.color_triggered
        elif self.detected:
            color = self.color_detected
        else:
            # Hidden: draw very subtly (only if in FOV)
            color = self.color_hidden
        
        # Draw trap as a small square/circle
        pygame.draw.rect(surface, color, screen_rect)
        
        # If detected but not triggered, add a warning indicator (small X or !)
        if self.detected and not self.triggered and not self.disarmed:
            # Draw a small warning symbol
            center_x = sx + sw // 2
            center_y = sy + sh // 2
            # Draw a small X
            line_w = max(1, int(2 * zoom))
            pygame.draw.line(
                surface, (255, 100, 100),
                (center_x - sw // 4, center_y - sh // 4),
                (center_x + sw // 4, center_y + sh // 4),
                line_w
            )
            pygame.draw.line(
                surface, (255, 100, 100),
                (center_x + sw // 4, center_y - sh // 4),
                (center_x - sw // 4, center_y + sh // 4),
                line_w
            )