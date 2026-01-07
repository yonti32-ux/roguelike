"""
Exploration Tutorial Screen - explains map symbols, entities, and exploration mechanics.
Can be accessed during exploration with H key.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from engine.core.game import Game


def draw_exploration_tutorial(surface: pygame.Surface, font: pygame.font.Font, game: "Game") -> None:
    """
    Draw the exploration tutorial overlay explaining map symbols and mechanics.
    Now with scrolling support.
    """
    screen_w, screen_h = surface.get_size()
    
    # Semi-transparent dark background
    overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))
    
    # Main panel
    panel_width = min(900, screen_w - 40)
    panel_height = min(650, screen_h - 40)
    panel_x = (screen_w - panel_width) // 2
    panel_y = (screen_h - panel_height) // 2
    
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    pygame.draw.rect(surface, (25, 25, 35), panel_rect)
    pygame.draw.rect(surface, (100, 150, 200), panel_rect, width=3)
    
    # Title (fixed at top)
    title_font = pygame.font.Font(None, 36)
    title_text = title_font.render("Exploration Tutorial", True, (255, 255, 255))
    title_x = panel_x + (panel_width - title_text.get_width()) // 2
    surface.blit(title_text, (title_x, panel_y + 20))
    
    # Content area (scrollable)
    content_x = panel_x + 30
    content_start_y = panel_y + 70
    content_end_y = panel_y + panel_height - 50  # Leave space for close hint
    content_height = content_end_y - content_start_y
    line_height = 24
    section_spacing = 35
    
    # Create a clipping rect for the scrollable content
    clip_rect = pygame.Rect(content_x, content_start_y, panel_width - 60, content_height)
    
    # First pass: calculate total height needed
    y = 0  # Start from 0 for calculation
    total_height = 0
    
    # Section: Map Symbols
    y += line_height + 5  # Section title
    y += line_height + 5  # Player
    y += line_height + 5  # Enemy
    y += line_height + 5  # Elite Enemy
    y += line_height + 5  # Chest
    y += line_height + 5  # Event Node
    y += line_height + 5  # Merchant
    y += line_height + 5  # Stairs Up
    y += line_height + 5  # Stairs Down
    y += line_height + 5  # Walls
    y += line_height + 5  # Floor
    y += section_spacing
    
    # Section: Exploration Mechanics
    y += line_height + 5  # Section title
    y += line_height * 8  # 8 mechanics
    y += section_spacing - line_height
    
    # Section: Interaction
    y += line_height + 5  # Section title
    y += line_height * 5  # 5 interactions
    y += section_spacing - line_height
    
    # Additional hints
    y += line_height * 2  # 2 hints
    
    total_height = y
    
    # Apply scroll offset
    scroll_offset = getattr(game, "exploration_tutorial_scroll_offset", 0)
    max_scroll = max(0, total_height - content_height)
    scroll_offset = min(scroll_offset, max_scroll)
    game.exploration_tutorial_scroll_offset = scroll_offset
    
    # Draw scrollbar if needed
    if total_height > content_height:
        scrollbar_width = 8
        scrollbar_x = panel_x + panel_width - scrollbar_width - 5
        scrollbar_height = content_height
        scrollbar_rect = pygame.Rect(scrollbar_x, content_start_y, scrollbar_width, scrollbar_height)
        pygame.draw.rect(surface, (50, 50, 60), scrollbar_rect)
        
        # Draw scrollbar thumb
        thumb_height = max(20, int(content_height * (content_height / total_height)))
        thumb_y = content_start_y + int((scroll_offset / max_scroll) * (content_height - thumb_height)) if max_scroll > 0 else content_start_y
        thumb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height)
        pygame.draw.rect(surface, (120, 150, 200), thumb_rect)
    
    # Apply clipping to content area before drawing
    old_clip = surface.get_clip()
    surface.set_clip(clip_rect)
    
    # Now draw content with scroll offset
    y = content_start_y - scroll_offset
    
    # Section: Map Symbols
    section_title = font.render("MAP SYMBOLS", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    # Player
    from settings import COLOR_PLAYER
    pygame.draw.rect(surface, COLOR_PLAYER, (content_x, y, 30, 30))
    player_text = font.render("Player (Green): You. Move with WASD or arrow keys.", True, (220, 220, 220))
    surface.blit(player_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Enemy
    from settings import COLOR_ENEMY
    pygame.draw.rect(surface, COLOR_ENEMY, (content_x, y, 30, 30))
    enemy_text = font.render("Enemy (Red): Hostile creatures. Walking into them starts combat.", True, (220, 220, 220))
    surface.blit(enemy_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Elite Enemy
    elite_color = (255, 200, 50)
    pygame.draw.rect(surface, COLOR_ENEMY, (content_x, y, 30, 30))
    pygame.draw.rect(surface, elite_color, (content_x, y, 30, 30), width=2)
    elite_text = font.render("Elite Enemy (Red with gold border): Stronger enemies with better rewards.", True, (220, 220, 220))
    surface.blit(elite_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Chest
    chest_color = (210, 180, 80)
    pygame.draw.rect(surface, chest_color, (content_x, y, 30, 30))
    chest_text = font.render("Chest (Gold): Contains loot. Press E when nearby to open.", True, (220, 220, 220))
    surface.blit(chest_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Event Node
    event_color = (150, 120, 255)
    pygame.draw.rect(surface, event_color, (content_x, y, 30, 30))
    event_text = font.render("Event Node (Purple): Interactive locations. Press E to interact.", True, (220, 220, 220))
    surface.blit(event_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Merchant
    merchant_color = (200, 180, 255)
    pygame.draw.rect(surface, merchant_color, (content_x, y, 30, 30))
    merchant_text = font.render("Merchant (Light Purple): Shop NPC. Press E nearby to trade.", True, (220, 220, 220))
    surface.blit(merchant_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Stairs Up
    from world.tiles import UP_STAIRS_COLOR
    pygame.draw.rect(surface, UP_STAIRS_COLOR, (content_x, y, 30, 30))
    # Draw up arrow symbol
    arrow_font = pygame.font.Font(None, 20)
    arrow_text = arrow_font.render("^", True, (255, 255, 255))
    arrow_x = content_x + (30 - arrow_text.get_width()) // 2
    arrow_y = y + (30 - arrow_text.get_height()) // 2
    surface.blit(arrow_text, (arrow_x, arrow_y))
    stairs_up_text = font.render("Stairs Up (Blue with ^): Go to previous floor. Press ',' to ascend.", True, (220, 220, 220))
    surface.blit(stairs_up_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Stairs Down
    from world.tiles import DOWN_STAIRS_COLOR
    pygame.draw.rect(surface, DOWN_STAIRS_COLOR, (content_x, y, 30, 30))
    # Draw down arrow symbol
    arrow_text = arrow_font.render("v", True, (255, 255, 255))
    arrow_x = content_x + (30 - arrow_text.get_width()) // 2
    arrow_y = y + (30 - arrow_text.get_height()) // 2
    surface.blit(arrow_text, (arrow_x, arrow_y))
    stairs_down_text = font.render("Stairs Down (Orange with v): Go to next floor. Press '.' to descend.", True, (220, 220, 220))
    surface.blit(stairs_down_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Walls
    from world.tiles import WALL_COLOR
    pygame.draw.rect(surface, WALL_COLOR, (content_x, y, 30, 30))
    wall_text = font.render("Wall (Gray): Blocks movement. Cannot walk through.", True, (220, 220, 220))
    surface.blit(wall_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Floor
    from world.tiles import FLOOR_COLOR
    pygame.draw.rect(surface, FLOOR_COLOR, (content_x, y, 30, 30))
    floor_text = font.render("Floor (Dark Blue): Walkable terrain.", True, (220, 220, 220))
    surface.blit(floor_text, (content_x + 40, y + 5))
    y += section_spacing
    
    # Section: Exploration Mechanics
    section_title = font.render("EXPLORATION MECHANICS", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    mechanics = [
        "• Movement: Use WASD or arrow keys to move around the dungeon",
        "• Fog of War: Unexplored areas are black. Explored areas stay visible (dimmed).",
        "• Line of Sight: You can only see tiles within your vision radius",
        "• Floor Progression: Use stairs to move between floors (deeper = harder)",
        "• Enemy Encounters: Walk into enemies to start combat",
        "• Chests: Open chests for loot (items and gold)",
        "• Events: Interact with purple event nodes for special encounters",
        "• Merchants: Trade with merchants to buy/sell items",
    ]
    
    for mechanic in mechanics:
        text = font.render(mechanic, True, (200, 200, 200))
        surface.blit(text, (content_x + 20, y))
        y += line_height
    
    y += section_spacing - line_height
    
    # Section: Interaction
    section_title = font.render("INTERACTION", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    interactions = [
        "• E: Interact with nearby objects (chests, events, merchants)",
        "• I: Open/close inventory",
        "• C: Open/close character sheet",
        "• T: Open/close skill/talent screen",
        "• K: Toggle exploration log",
    ]
    
    for interaction in interactions:
        text = font.render(interaction, True, (200, 200, 200))
        surface.blit(text, (content_x + 20, y))
        y += line_height
    
    # Additional hints
    y += section_spacing - line_height
    hints = [
        "Press H to toggle this tutorial",
        "Press Z/X to zoom in/out",
    ]
    
    for hint in hints:
        hint_text = font.render(hint, True, (120, 150, 180))
        surface.blit(hint_text, (content_x + 20, y))
        y += line_height
    
    # Restore clipping
    surface.set_clip(old_clip)
    
    # Close hint (fixed at bottom, drawn after clipping is restored)
    hint_text = font.render("Press H or ESC to close | Scroll: Mouse wheel, Arrow keys, Page Up/Down", True, (150, 150, 150))
    hint_x = panel_x + (panel_width - hint_text.get_width()) // 2
    surface.blit(hint_text, (hint_x, panel_y + panel_height - 35))

