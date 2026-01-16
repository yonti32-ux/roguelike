"""
Overworld Tutorial Screen - explains terrain types, POIs, movement, and overworld mechanics.
Can be accessed during overworld with H key.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from engine.core.game import Game


def draw_overworld_tutorial(surface: pygame.Surface, font: pygame.font.Font, game: "Game") -> None:
    """
    Draw the overworld tutorial overlay explaining terrain, POIs, and mechanics.
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
    title_text = title_font.render("Overworld Tutorial", True, (255, 255, 255))
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
    y += line_height + 5  # Grass
    y += line_height + 5  # Forest
    y += line_height + 5  # Plains
    y += line_height + 5  # Desert
    y += line_height + 5  # Beach
    y += line_height + 5  # Snow
    y += line_height + 5  # Mountain
    y += line_height + 5  # Water
    y += section_spacing
    
    # Section: Points of Interest (POIs)
    y += line_height + 5  # Section title
    y += line_height + 5  # Dungeon
    y += line_height + 5  # Village
    y += line_height + 5  # Town
    y += line_height + 5  # Camp
    y += section_spacing
    
    # Section: Movement & Exploration
    y += line_height + 5  # Section title
    y += line_height * 8  # 8 mechanics
    y += section_spacing - line_height
    
    # Section: Interaction
    y += line_height + 5  # Section title
    y += line_height * 6  # 6 interactions
    y += section_spacing - line_height
    
    # Section: Roaming Parties
    y += line_height + 5  # Section title
    y += line_height * 3  # 3 party mechanics
    y += section_spacing - line_height
    
    # Section: Zoom Controls
    y += line_height + 5  # Section title
    y += line_height * 3  # 3 zoom controls
    y += section_spacing - line_height
    
    # Additional hints
    y += line_height * 2  # 2 hints
    
    total_height = y
    
    # Apply scroll offset
    scroll_offset = getattr(game, "overworld_tutorial_scroll_offset", 0)
    max_scroll = max(0, total_height - content_height)
    scroll_offset = min(scroll_offset, max_scroll)
    game.overworld_tutorial_scroll_offset = scroll_offset
    
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
    
    # Import terrain types for colors
    from world.overworld.terrain import (
        TERRAIN_GRASS, TERRAIN_FOREST, TERRAIN_PLAINS, TERRAIN_DESERT,
        TERRAIN_BEACH, TERRAIN_SNOW, TERRAIN_MOUNTAIN, TERRAIN_WATER
    )
    
    # Grass
    pygame.draw.rect(surface, TERRAIN_GRASS.color, (content_x, y, 30, 30))
    grass_text = font.render("Grass (Green): Normal terrain. Movement cost: 1.0x", True, (220, 220, 220))
    surface.blit(grass_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Forest
    pygame.draw.rect(surface, TERRAIN_FOREST.color, (content_x, y, 30, 30))
    forest_text = font.render("Forest (Dark Green): Slower movement. Cost: 1.5x", True, (220, 220, 220))
    surface.blit(forest_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Plains
    pygame.draw.rect(surface, TERRAIN_PLAINS.color, (content_x, y, 30, 30))
    plains_text = font.render("Plains (Light Green): Faster movement. Cost: 0.9x", True, (220, 220, 220))
    surface.blit(plains_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Desert
    pygame.draw.rect(surface, TERRAIN_DESERT.color, (content_x, y, 30, 30))
    desert_text = font.render("Desert (Beige): Slightly slower. Cost: 1.2x", True, (220, 220, 220))
    surface.blit(desert_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Beach
    pygame.draw.rect(surface, TERRAIN_BEACH.color, (content_x, y, 30, 30))
    beach_text = font.render("Beach (Sandy): Slightly slower. Cost: 1.1x", True, (220, 220, 220))
    surface.blit(beach_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Snow
    pygame.draw.rect(surface, TERRAIN_SNOW.color, (content_x, y, 30, 30))
    pygame.draw.rect(surface, (200, 200, 200), (content_x, y, 30, 30), width=1)  # Border for visibility
    snow_text = font.render("Snow (White): Slower movement. Cost: 1.3x", True, (220, 220, 220))
    surface.blit(snow_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Mountain
    pygame.draw.rect(surface, TERRAIN_MOUNTAIN.color, (content_x, y, 30, 30))
    mountain_text = font.render("Mountain (Gray): Blocks movement. Cannot walk through.", True, (220, 220, 220))
    surface.blit(mountain_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Water
    pygame.draw.rect(surface, TERRAIN_WATER.color, (content_x, y, 30, 30))
    water_text = font.render("Water (Blue): Blocks movement. Cannot walk through.", True, (220, 220, 220))
    surface.blit(water_text, (content_x + 40, y + 5))
    y += section_spacing
    
    # Section: Points of Interest (POIs)
    section_title = font.render("POINTS OF INTEREST (POIs)", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    # Dungeon
    dungeon_color = (200, 50, 50)
    pygame.draw.circle(surface, dungeon_color, (content_x + 15, y + 15), 15)
    dungeon_text = font.render("Dungeon (Red circle): Enter to explore. Shows level number.", True, (220, 220, 220))
    surface.blit(dungeon_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Village
    village_color = (50, 200, 50)
    pygame.draw.circle(surface, village_color, (content_x + 15, y + 15), 15)
    village_text = font.render("Village (Green circle): Small settlement. Trade and rest.", True, (220, 220, 220))
    surface.blit(village_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Town
    town_color = (50, 50, 200)
    pygame.draw.circle(surface, town_color, (content_x + 15, y + 15), 15)
    town_text = font.render("Town (Blue circle): Large settlement. More services.", True, (220, 220, 220))
    surface.blit(town_text, (content_x + 40, y + 5))
    y += line_height + 5
    
    # Camp
    camp_color = (200, 200, 50)
    pygame.draw.circle(surface, camp_color, (content_x + 15, y + 15), 15)
    camp_text = font.render("Camp (Yellow circle): Temporary location. Rest and trade.", True, (220, 220, 220))
    surface.blit(camp_text, (content_x + 40, y + 5))
    y += section_spacing
    
    # Section: Movement & Exploration
    section_title = font.render("MOVEMENT & EXPLORATION", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    mechanics = [
        "• Movement: Use WASD or arrow keys to move one tile at a time",
        "• Diagonal Movement: Use Q (NW), E (NE), Z (SW), C (SE) for diagonal movement",
        "• Fog of War: Unexplored areas are black. Explored areas stay visible (dimmed)",
        "• Sight Radius: You can see tiles within 8 tiles of your position",
        "• POI Discovery: POIs are discovered when you get within sight radius",
        "• Time System: Movement consumes time based on terrain type",
        "• Terrain Costs: Different terrains have different movement costs",
        "• Player Icon: White circle with arrow shows your position and facing direction",
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
        "• E: Enter POI when standing directly on it",
        "• E: Interact with roaming parties when adjacent or on same tile",
        "• I: Open/close inventory",
        "• C: Open/close character sheet",
        "• J: Open/close quest screen (journal)",
        "• Hover: Mouse over POIs or parties to see detailed information",
    ]
    
    for interaction in interactions:
        text = font.render(interaction, True, (200, 200, 200))
        surface.blit(text, (content_x + 20, y))
        y += line_height
    
    y += section_spacing - line_height
    
    # Section: Roaming Parties
    section_title = font.render("ROAMING PARTIES", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    party_mechanics = [
        "• Colored Circles: Different party types appear as colored circles on the map",
        "• Interaction: Stand on or adjacent to a party and press E to interact",
        "• Party Types: Merchants, enemies, and other groups roam the overworld",
    ]
    
    for mechanic in party_mechanics:
        text = font.render(mechanic, True, (200, 200, 200))
        surface.blit(text, (content_x + 20, y))
        y += line_height
    
    y += section_spacing - line_height
    
    # Section: Zoom Controls
    section_title = font.render("ZOOM CONTROLS", True, (150, 200, 255))
    surface.blit(section_title, (content_x, y))
    y += line_height + 5
    
    zoom_controls = [
        "• +/- or Mouse Wheel: Zoom in/out on the map",
        "• 0: Reset zoom to 100%",
        "• Zoom Level: Displayed in top-right corner",
    ]
    
    for control in zoom_controls:
        text = font.render(control, True, (200, 200, 200))
        surface.blit(text, (content_x + 20, y))
        y += line_height
    
    # Additional hints
    y += section_spacing - line_height
    hints = [
        "Press H to toggle this tutorial",
        "Time passes as you move - check the time display in the top-left",
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

