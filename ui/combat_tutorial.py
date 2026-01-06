"""
Combat Tutorial Screen - explains battle mechanics, terrain, status effects, etc.
Can be accessed during battle with H key.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from engine.battle_scene import BattleScene


def draw_combat_tutorial(surface: pygame.Surface, font: pygame.font.Font, battle_scene: "BattleScene") -> None:
    """
    Draw the combat tutorial overlay explaining battle mechanics.
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
    title_text = title_font.render("Combat Tutorial", True, (255, 255, 255))
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
    
    # Section: Terrain Types
    y += line_height + 5  # Section title
    y += line_height + 5  # Cover
    y += line_height + 5  # Obstacle
    y += line_height + 5  # Hazard
    y += section_spacing
    
    # Section: Combat Mechanics
    y += line_height + 5  # Section title
    y += line_height * 10  # 10 mechanics
    y += section_spacing - line_height
    
    # Section: Status Effects
    y += line_height + 5  # Section title
    y += line_height * 9  # 9 statuses
    y += section_spacing - line_height
    
    # Section: Stats
    y += line_height + 5  # Section title
    y += line_height * 5  # 5 stats
    y += section_spacing - line_height
    
    # Additional hints
    y += line_height * 2  # 2 hints
    
    total_height = y
    
    # Apply scroll offset
    scroll_offset = getattr(battle_scene, "tutorial_scroll_offset", 0)
    max_scroll = max(0, total_height - content_height)
    scroll_offset = min(scroll_offset, max_scroll)
    battle_scene.tutorial_scroll_offset = scroll_offset
    
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
    
    # Section: Terrain Types
    section_title = font.render("TERRAIN TYPES", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    # Cover
    cover_color = (120, 150, 100)
    pygame.draw.rect(surface, cover_color, (content_x, y, 30, 30))
    # Draw small shield icon in top-right corner (like in game)
    shield_x = content_x + 30 - 12
    shield_y = y + 4
    shield_size = 8
    shield_points = [
        (shield_x + shield_size // 2, shield_y),
        (shield_x, shield_y + shield_size // 4),
        (shield_x, shield_y + shield_size * 3 // 4),
        (shield_x + shield_size // 2, shield_y + shield_size),
        (shield_x + shield_size, shield_y + shield_size * 3 // 4),
        (shield_x + shield_size, shield_y + shield_size // 4),
    ]
    pygame.draw.polygon(surface, (100, 180, 120), shield_points)
    pygame.draw.polygon(surface, (80, 160, 100), shield_points, width=1)
    cover_text = font.render("Cover (Green shield icon): Reduces ranged damage by 50%. Stand on it for protection.", True, (220, 220, 220))
    surface.blit(cover_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Obstacle
    obstacle_color = (50, 50, 50)
    pygame.draw.rect(surface, obstacle_color, (content_x, y, 30, 30))
    pygame.draw.line(surface, (100, 100, 100), (content_x + 5, y + 5), (content_x + 25, y + 25), 2)
    pygame.draw.line(surface, (100, 100, 100), (content_x + 25, y + 5), (content_x + 5, y + 25), 2)
    obstacle_text = font.render("Obstacle (Gray): Blocks movement and line of sight. Cannot walk through.", True, (220, 220, 220))
    surface.blit(obstacle_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Hazard
    hazard_color = (150, 50, 50)
    pygame.draw.rect(surface, hazard_color, (content_x, y, 30, 30))
    pygame.draw.circle(surface, (200, 100, 100), (content_x + 15, y + 12), 3)
    pygame.draw.line(surface, (200, 100, 100), (content_x + 15, y + 17), (content_x + 15, y + 23), 2)
    hazard_text = font.render("Hazard (Red): Deals 2 damage per turn if you stand on it.", True, (220, 220, 220))
    surface.blit(hazard_text, (content_x + 40, y + 5))
    y += section_spacing
    
    # Section: Combat Mechanics
    section_title = font.render("COMBAT MECHANICS", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    mechanics = [
        "• Movement Points: Each unit has 3 movement points per turn",
        "• Movement: Click on a reachable tile to move, or use WASD/Arrow keys",
        "• Pathfinding: Movement mode auto-starts - hover to see path preview",
        "• Cover: Reduces ranged attack damage by 50% (shield icon on tile)",
        "• Flanking: Attack from side/behind for +25% damage (melee only)",
        "• Hazards: Cost extra movement points (2 MP) to cross",
        "• Basic Attack: SPACE to attack, or click enemy when targeting",
        "• Skills: Use hotkeys (Q, R, E, F, etc.) for special abilities",
        "• Guard: G key to halve incoming damage for one turn",
        "• Targeting: Click enemies to select, or use arrow keys/TAB to cycle",
    ]
    
    for mechanic in mechanics:
        text = font.render(mechanic, True, (200, 200, 200))
        surface.blit(text, (content_x + 20, y))
        y += line_height
    
    y += section_spacing - line_height
    
    # Section: Status Effects
    section_title = font.render("STATUS EFFECTS", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    statuses = [
        ("Guard", "Halves incoming damage for 1 turn"),
        ("Weakened", "Deal 30% less damage for 2 turns"),
        ("Stunned", "Cannot act this turn"),
        ("Poisoned", "Take damage each turn for 3 turns"),
        ("Bleeding", "Take damage each turn for 2 turns"),
        ("Cursed", "Take 25% more damage for 2 turns"),
        ("Marked", "Take 25% more damage from all sources for 3 turns"),
        ("Berserker Rage", "Deal 50% more damage for 3 turns"),
        ("Regenerating", "Heal 2 HP each turn for 4 turns"),
    ]
    
    for status_name, description in statuses:
        name_text = font.render(f"• {status_name}:", True, (255, 220, 150))
        surface.blit(name_text, (content_x + 20, y))
        desc_text = font.render(description, True, (180, 180, 180))
        surface.blit(desc_text, (content_x + 150, y))
        y += line_height
    
    y += section_spacing - line_height
    
    # Section: Stats
    section_title = font.render("STATS", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    stats = [
        ("HP", "Health points. When reduced to 0, unit is defeated"),
        ("ATK", "Attack power. Determines base damage dealt"),
        ("DEF", "Defense. Reduces incoming damage"),
        ("STA", "Stamina. Used for physical skills"),
        ("MP", "Mana. Used for magical skills"),
    ]
    
    for stat_name, description in stats:
        name_text = font.render(f"• {stat_name}:", True, (255, 220, 150))
        surface.blit(name_text, (content_x + 20, y))
        desc_text = font.render(description, True, (180, 180, 180))
        surface.blit(desc_text, (content_x + 100, y))
        y += line_height
    
    # Additional hints
    y += section_spacing - line_height
    hints = [
        "Press L to view full combat log history",
        "Press H to toggle this tutorial",
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

