"""
Battle renderer module.

Handles all rendering/drawing logic for the battle scene.
Extracted from battle_scene.py for better code organization.
"""

from typing import List, Dict, Optional
import math
import pygame

from settings import (
    COLOR_PLAYER,
    COLOR_ENEMY,
    BASE_CRIT_CHANCE,
)
from engine.battle.types import BattleUnit
from ui.hud_utils import _draw_status_indicators


class BattleRenderer:
    """
    Handles all rendering for the battle scene.
    
    Takes a reference to the BattleScene to access its state.
    """
    
    def __init__(self, scene):
        """
        Initialize the renderer with a reference to the battle scene.
        
        Args:
            scene: The BattleScene instance to render
        """
        self.scene = scene
        self.font = scene.font
        # Create a larger font for damage numbers
        try:
            # Try to get font size from the scene font
            font_size = scene.font.get_height()
            # Make damage numbers 1.5x bigger
            self.damage_font = pygame.font.Font(None, int(font_size * 1.5))
        except:
            # Fallback to a fixed larger size
            self.damage_font = pygame.font.Font(None, 30)
    
    def draw_active_unit_panel(
        self,
        surface: pygame.Surface,
        unit: Optional[BattleUnit],
        screen_w: int,
    ) -> None:
        """
        Draw a small HUD panel for the currently active unit (hero, companion,
        or enemy), showing name, HP, and basic stats.
        """
        if unit is None:
            return

        panel_width = 320
        panel_height = 80
        x = (screen_w - panel_width) // 2
        y = 16

        bg_rect = pygame.Rect(x, y, panel_width, panel_height)
        # Background
        pygame.draw.rect(surface, (18, 18, 28), bg_rect)

        # Border colour by side
        border_color = COLOR_PLAYER if unit.side == "player" else COLOR_ENEMY
        pygame.draw.rect(surface, border_color, bg_rect, width=2)

        # Name + role
        role = "Party" if unit.side == "player" else "Enemy"
        name_line = f"{unit.name} ({role})"
        name_surf = self.font.render(name_line, True, (230, 230, 230))
        surface.blit(name_surf, (x + 10, y + 8))

        # HP + stats line
        hp_line = f"HP {unit.hp}/{unit.max_hp}"
        atk = getattr(unit.entity, "attack_power", 0)
        defense = getattr(unit.entity, "defense", 0)
        stats_line = f"ATK {atk}   DEF {defense}"

        # Resource line (stamina, and later mana)
        res_line = ""
        max_sta = getattr(unit, "max_stamina", 0)
        cur_sta = getattr(unit, "current_stamina", 0)
        max_mana = getattr(unit, "max_mana", 0)
        cur_mana = getattr(unit, "current_mana", 0)

        if max_sta > 0:
            res_line = f"STA {cur_sta}/{max_sta}"
        if max_mana > 0:
            if res_line:
                res_line = f"MP {cur_mana}/{max_mana}   {res_line}"
            else:
                res_line = f"MP {cur_mana}/{max_mana}"

        hp_surf = self.font.render(hp_line, True, (210, 210, 210))
        stats_surf = self.font.render(stats_line, True, (200, 200, 200))
        res_surf = self.font.render(res_line, True, (190, 190, 230)) if res_line else None

        surface.blit(hp_surf, (x + 10, y + 32))
        surface.blit(stats_surf, (x + 10, y + 48))
        if res_surf is not None:
            surface.blit(res_surf, (x + 10, y + 64))

        # Simple status indicators on the right side of the panel
        icon_x = x + panel_width - 18
        icon_y = y + 10
        
        _draw_status_indicators(
            surface,
            self.font,
            icon_x,
            icon_y,
            has_guard=self.scene._has_status(unit, "guard"),
            has_weakened=self.scene._has_status(unit, "weakened"),
            has_stunned=self.scene._is_stunned(unit),
            has_dot=self.scene._has_dot(unit),
            icon_spacing=18,
        )

    def draw_grid(self, surface: pygame.Surface) -> None:
        """Draw the battle grid with terrain and movement highlights."""
        # Draw reachable cells if in movement mode
        reachable_cells: Dict[tuple[int, int], int] = {}
        if self.scene.movement_mode:
            unit = self.scene._active_unit()
            if unit.side == "player":
                reachable_cells = self.scene.pathfinding.get_reachable_cells(unit)
        
        for gy in range(self.scene.grid_height):
            for gx in range(self.scene.grid_width):
                x = self.scene.grid_origin_x + gx * self.scene.cell_size
                y = self.scene.grid_origin_y + gy * self.scene.cell_size
                rect = pygame.Rect(x, y, self.scene.cell_size, self.scene.cell_size)
                
                # Draw cell background
                pygame.draw.rect(surface, (40, 40, 60), rect, width=1)
                
                # Draw reachable cells highlight (movement mode)
                if (gx, gy) in reachable_cells:
                    reachable_surf = pygame.Surface((self.scene.cell_size, self.scene.cell_size), pygame.SRCALPHA)
                    pygame.draw.rect(reachable_surf, (60, 80, 120, 80), reachable_surf.get_rect())
                    surface.blit(reachable_surf, (x, y))
                
                # Draw movement path (movement mode)
                if self.scene.movement_mode and (gx, gy) in self.scene.movement_path:
                    path_index = self.scene.movement_path.index((gx, gy))
                    if path_index > 0:  # Not the starting position
                        path_surf = pygame.Surface((self.scene.cell_size, self.scene.cell_size), pygame.SRCALPHA)
                        # Different intensity based on position in path
                        alpha = 120 + (path_index * 10)
                        alpha = min(255, alpha)
                        pygame.draw.rect(path_surf, (100, 150, 200, alpha), path_surf.get_rect())
                        surface.blit(path_surf, (x, y))
                        # Draw arrow pointing to next cell
                        if path_index < len(self.scene.movement_path) - 1:
                            next_pos = self.scene.movement_path[path_index + 1]
                            dx = next_pos[0] - gx
                            dy = next_pos[1] - gy
                            center_x = x + self.scene.cell_size // 2
                            center_y = y + self.scene.cell_size // 2
                            # Draw arrow
                            if dx > 0:  # Right
                                pygame.draw.polygon(surface, (150, 200, 255), [
                                    (center_x + 10, center_y),
                                    (center_x, center_y - 5),
                                    (center_x, center_y + 5)
                                ])
                            elif dx < 0:  # Left
                                pygame.draw.polygon(surface, (150, 200, 255), [
                                    (center_x - 10, center_y),
                                    (center_x, center_y - 5),
                                    (center_x, center_y + 5)
                                ])
                            elif dy > 0:  # Down
                                pygame.draw.polygon(surface, (150, 200, 255), [
                                    (center_x, center_y + 10),
                                    (center_x - 5, center_y),
                                    (center_x + 5, center_y)
                                ])
                            elif dy < 0:  # Up
                                pygame.draw.polygon(surface, (150, 200, 255), [
                                    (center_x, center_y - 10),
                                    (center_x - 5, center_y),
                                    (center_x + 5, center_y)
                                ])
                
                # Draw terrain
                terrain = self.scene.terrain_manager.get_terrain(gx, gy)
                is_on_path = self.scene.movement_mode and (gx, gy) in self.scene.movement_path
                
                if terrain.terrain_type == "cover":
                    # Cover: small shield icon on the side (top-right corner)
                    # Draw small shield icon in top-right corner
                    shield_x = x + self.scene.cell_size - 12  # Right side with small margin
                    shield_y = y + 4  # Top with small margin
                    shield_size = 8  # Small shield icon
                    
                    # Draw shield shape (rounded top, pointed bottom) - smaller version
                    shield_points = [
                        (shield_x + shield_size // 2, shield_y),  # Top
                        (shield_x, shield_y + shield_size // 4),  # Top left
                        (shield_x, shield_y + shield_size * 3 // 4),  # Bottom left
                        (shield_x + shield_size // 2, shield_y + shield_size),  # Bottom point
                        (shield_x + shield_size, shield_y + shield_size * 3 // 4),  # Bottom right
                        (shield_x + shield_size, shield_y + shield_size // 4),  # Top right
                    ]
                    pygame.draw.polygon(surface, (100, 180, 120), shield_points)
                    pygame.draw.polygon(surface, (80, 160, 100), shield_points, width=1)
                    
                    # Highlight cover on path more prominently
                    if is_on_path:
                        highlight_surf = pygame.Surface((self.scene.cell_size, self.scene.cell_size), pygame.SRCALPHA)
                        pygame.draw.rect(highlight_surf, (100, 200, 140, 180), highlight_surf.get_rect())
                        surface.blit(highlight_surf, (x, y))
                elif terrain.terrain_type == "obstacle":
                    # Obstacle: dark gray block
                    pygame.draw.rect(surface, (50, 50, 50), rect)
                    pygame.draw.rect(surface, (70, 70, 70), rect, width=2)
                    # Draw X pattern to indicate blocking
                    pygame.draw.line(surface, (100, 100, 100), (x + 5, y + 5), (x + self.scene.cell_size - 5, y + self.scene.cell_size - 5), 2)
                    pygame.draw.line(surface, (100, 100, 100), (x + self.scene.cell_size - 5, y + 5), (x + 5, y + self.scene.cell_size - 5), 2)
                elif terrain.terrain_type == "hazard":
                    # Hazard: red/orange tint
                    hazard_surf = pygame.Surface((self.scene.cell_size, self.scene.cell_size), pygame.SRCALPHA)
                    pygame.draw.rect(hazard_surf, (150, 50, 50, 100), hazard_surf.get_rect())
                    surface.blit(hazard_surf, (x, y))
                    # Draw warning symbol (exclamation)
                    center_x = x + self.scene.cell_size // 2
                    center_y = y + self.scene.cell_size // 2
                    pygame.draw.circle(surface, (200, 100, 100), (center_x, center_y - 5), 3)
                    pygame.draw.line(surface, (200, 100, 100), (center_x, center_y + 2), (center_x, center_y + 8), 2)

    def draw_log_history(self, surface: pygame.Surface) -> None:
        """
        Draw the combat log history viewer overlay.
        Shows all log messages from the current battle.
        """
        screen_w, screen_h = surface.get_size()
        
        # Semi-transparent dark background
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Main panel
        panel_width = min(800, screen_w - 40)
        panel_height = min(600, screen_h - 40)
        panel_x = (screen_w - panel_width) // 2
        panel_y = (screen_h - panel_height) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, (25, 25, 35), panel_rect)
        pygame.draw.rect(surface, (150, 200, 150), panel_rect, width=3)
        
        # Title
        title_font = pygame.font.Font(None, 36)
        title_text = title_font.render("Combat Log History", True, (255, 255, 255))
        title_x = panel_x + (panel_width - title_text.get_width()) // 2
        surface.blit(title_text, (title_x, panel_y + 20))
        
        # Content area with scrollable log
        content_x = panel_x + 20
        content_y = panel_y + 70
        content_width = panel_width - 40
        content_height = panel_height - 120
        line_height = 20
        
        # Draw log messages (all of them, not just recent)
        log_lines = self.scene.log  # Show full log history
        y = content_y
        
        # If log is too long, show most recent messages
        max_visible_lines = content_height // line_height
        if len(log_lines) > max_visible_lines:
            log_lines = log_lines[-max_visible_lines:]
            # Show indicator that there are more messages
            more_text = self.font.render(f"... ({len(self.scene.log) - max_visible_lines} older messages)", True, (150, 150, 150))
            surface.blit(more_text, (content_x, y))
            y += line_height + 5
        
        # Draw log messages
        for msg in log_lines:
            if y + line_height > panel_y + panel_height - 50:
                break  # Don't draw beyond panel
            
            # Wrap long messages
            words = msg.split()
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surf = self.font.render(test_line, True, (220, 220, 220))
                if test_surf.get_width() > content_width - 20:
                    if current_line:
                        text = self.font.render(current_line, True, (220, 220, 220))
                        surface.blit(text, (content_x, y))
                        y += line_height
                        if y + line_height > panel_y + panel_height - 50:
                            break
                    current_line = word
                else:
                    current_line = test_line
            
            if current_line and y + line_height <= panel_y + panel_height - 50:
                text = self.font.render(current_line, True, (220, 220, 220))
                surface.blit(text, (content_x, y))
                y += line_height
        
        # If no log messages yet
        if not self.scene.log:
            no_log_text = self.font.render("No combat log messages yet.", True, (150, 150, 150))
            surface.blit(no_log_text, (content_x, content_y))
        
        # Close hint
        hint_text = self.font.render("Press L or ESC to close", True, (150, 150, 150))
        hint_x = panel_x + (panel_width - hint_text.get_width()) // 2
        surface.blit(hint_text, (hint_x, panel_y + panel_height - 35))

    def draw_hp_bar(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        unit: BattleUnit,
        *,
        is_player: bool,
    ) -> None:
        """
        Draw a small HP bar just above the unit's rectangle.
        """
        max_hp = unit.max_hp
        if max_hp <= 0:
            return

        hp = max(0, min(unit.hp, max_hp))
        ratio = hp / float(max_hp)

        bar_height = 6
        bar_width = rect.width
        bar_x = rect.x
        bar_y = rect.y - bar_height - 2

        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, (25, 25, 32), bg_rect)

        if ratio <= 0.0:
            return

        fg_width = max(1, int(bar_width * ratio))
        color = COLOR_PLAYER if is_player else COLOR_ENEMY
        fg_rect = pygame.Rect(bar_x, bar_y, fg_width, bar_height)
        pygame.draw.rect(surface, color, fg_rect)

    def draw_units(self, surface: pygame.Surface, screen_w: int) -> None:
        """Draw all units on the battle grid."""
        active = self.scene._active_unit() if self.scene.status == "ongoing" else None
        
        # Get current target if in targeting mode
        current_target = self.scene._get_current_target() if self.scene.targeting_mode is not None else None
        valid_targets: List[BattleUnit] = []
        if self.scene.targeting_mode is not None:
            valid_targets = self.scene.targeting_mode.get("targets", [])

        # ---------------- Player units ----------------
        for unit in self.scene.player_units:
            if not unit.is_alive:
                continue

            x = self.scene.grid_origin_x + unit.gx * self.scene.cell_size
            y = self.scene.grid_origin_y + unit.gy * self.scene.cell_size
            rect = pygame.Rect(
                x + 10,
                y + 10,
                self.scene.cell_size - 20,
                self.scene.cell_size - 20,
            )

            # Body
            pygame.draw.rect(surface, COLOR_PLAYER, rect)
            # Highlight active unit with pulsing glow
            if active is unit:
                # Pulsing glow effect - use animation_time from scene
                pulse = (math.sin(self.scene.animation_time * 4.0) + 1.0) / 2.0  # 0 to 1
                glow_alpha = int(80 + pulse * 100)  # Pulse between 80 and 180 alpha
                glow_size = 3 + int(pulse * 3)  # Pulse between 3 and 6 pixels
                
                # Draw outer glow
                for i in range(glow_size):
                    alpha = int(glow_alpha * (1.0 - i / glow_size))
                    glow_rect = pygame.Rect(
                        rect.x - i - 1,
                        rect.y - i - 1,
                        rect.width + (i + 1) * 2,
                        rect.height + (i + 1) * 2
                    )
                    glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (255, 255, 150, alpha), glow_surf.get_rect())
                    surface.blit(glow_surf, (glow_rect.x, glow_rect.y))
                
                # Bright border
                pygame.draw.rect(surface, (255, 255, 150), rect, width=4)

            # HP bar
            self.draw_hp_bar(surface, rect, unit, is_player=True)

            # Status icons above the HP bar (horizontal layout, going upward)
            icon_y = rect.y - 18
            _draw_status_indicators(
                surface,
                self.font,
                rect.x + 4,  # Start x position
                icon_y,
                has_guard=self.scene._has_status(unit, "guard"),
                has_weakened=self.scene._has_status(unit, "weakened"),
                has_stunned=self.scene._is_stunned(unit),
                has_dot=self.scene._has_dot(unit),
                icon_spacing=-18,  # Negative for upward
                vertical=True,
            )

            # Cooldown indicator for hero's Power Strike
            hero = self.scene._hero_unit()
            if hero is unit:
                cd = unit.cooldowns.get("power_strike", 0)
                if cd > 0:
                    cd_text = self.font.render(str(cd), True, (255, 200, 0))
                    surface.blit(cd_text, (rect.x + rect.width - 16, rect.y + 2))

            # Name label under unit
            name_surf = self.font.render(unit.name, True, (230, 230, 230))
            name_x = rect.centerx - name_surf.get_width() // 2
            name_y = rect.bottom + 10
            surface.blit(name_surf, (name_x, name_y))

        # ---------------- Enemy units ----------------
        for unit in self.scene.enemy_units:
            if not unit.is_alive:
                continue

            x = self.scene.grid_origin_x + unit.gx * self.scene.cell_size
            y = self.scene.grid_origin_y + unit.gy * self.scene.cell_size
            rect = pygame.Rect(
                x + 10,
                y + 10,
                self.scene.cell_size - 20,
                self.scene.cell_size - 20,
            )

            # Check if this enemy is elite
            is_elite = False
            if hasattr(unit, "entity") and hasattr(unit.entity, "is_elite"):
                is_elite = getattr(unit.entity, "is_elite", False)
            
            # Elite enemies get a gold glow effect (always visible)
            if is_elite:
                # Draw pulsing elite glow
                pulse = (math.sin(self.scene.animation_time * 3.0) + 1.0) / 2.0  # 0 to 1
                glow_alpha = int(120 + pulse * 80)  # Pulse between 120 and 200 alpha
                glow_size = 4 + int(pulse * 2)  # Pulse between 4 and 6 pixels
                
                # Draw outer glow
                for i in range(glow_size):
                    alpha = int(glow_alpha * (1.0 - i / glow_size))
                    glow_rect = pygame.Rect(
                        rect.x - i - 1,
                        rect.y - i - 1,
                        rect.width + (i + 1) * 2,
                        rect.height + (i + 1) * 2
                    )
                    glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (255, 200, 50, alpha), glow_surf.get_rect())
                    surface.blit(glow_surf, (glow_rect.x, glow_rect.y))
                
                # Bright gold border for elites
                pygame.draw.rect(surface, (255, 220, 100), rect, width=3)
            
            # Body
            enemy_color = COLOR_ENEMY
            if is_elite and hasattr(unit.entity, "color"):
                # Use the elite-tinted color if available
                enemy_color = getattr(unit.entity, "color", COLOR_ENEMY)
            pygame.draw.rect(surface, enemy_color, rect)
            
            # Highlight active unit with pulsing glow
            if active is unit:
                # Pulsing glow effect - use animation_time from scene
                pulse = (math.sin(self.scene.animation_time * 4.0) + 1.0) / 2.0  # 0 to 1
                glow_alpha = int(80 + pulse * 100)  # Pulse between 80 and 180 alpha
                glow_size = 3 + int(pulse * 3)  # Pulse between 3 and 6 pixels
                
                # Draw outer glow
                for i in range(glow_size):
                    alpha = int(glow_alpha * (1.0 - i / glow_size))
                    glow_rect = pygame.Rect(
                        rect.x - i - 1,
                        rect.y - i - 1,
                        rect.width + (i + 1) * 2,
                        rect.height + (i + 1) * 2
                    )
                    glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (255, 180, 100, alpha), glow_surf.get_rect())
                    surface.blit(glow_surf, (glow_rect.x, glow_rect.y))
                
                # Bright border
                pygame.draw.rect(surface, (255, 200, 120), rect, width=4)
            
            # Highlight valid targets in targeting mode
            if unit in valid_targets:
                if current_target is unit:
                    # Selected target: bright yellow highlight
                    pygame.draw.rect(surface, (255, 255, 100), rect, width=4)
                    # Draw an additional outer glow effect
                    outer_rect = pygame.Rect(
                        rect.x - 3,
                        rect.y - 3,
                        rect.width + 6,
                        rect.height + 6,
                    )
                    pygame.draw.rect(surface, (255, 255, 150, 100), outer_rect, width=2)
                else:
                    # Valid but not selected: lighter highlight
                    pygame.draw.rect(surface, (200, 200, 100), rect, width=3)

            # HP bar
            self.draw_hp_bar(surface, rect, unit, is_player=False)

            # Status icons (horizontal layout, going upward)
            icon_y = rect.y - 18
            _draw_status_indicators(
                surface,
                self.font,
                rect.x + 4,  # Start x position
                icon_y,
                has_guard=self.scene._has_status(unit, "guard"),
                has_weakened=self.scene._has_status(unit, "weakened"),
                has_stunned=self.scene._is_stunned(unit),
                has_dot=self.scene._has_dot(unit),
                icon_spacing=-18,  # Negative for upward
                vertical=True,
            )

            # Name label
            name_surf = self.font.render(unit.name, True, (230, 210, 210))
            name_x = rect.centerx - name_surf.get_width() // 2
            name_y = rect.bottom + 10
            surface.blit(name_surf, (name_x, name_y))
        
        # ---------------- Floating damage numbers ----------------
        self.draw_floating_damage(surface)
        
        # ---------------- Hit sparks (drawn after units) ----------------
        self.draw_hit_sparks(surface)

    def draw_floating_damage(self, surface: pygame.Surface) -> None:
        """Draw floating damage numbers that rise and fade."""
        for damage_info in self.scene._floating_damage:
            target = damage_info["target"]
            damage = damage_info["damage"]
            y_offset = damage_info["y_offset"]
            timer = damage_info["timer"]
            is_crit = damage_info.get("is_crit", False)
            is_kill = damage_info.get("is_kill", False)
            
            if not target.is_alive and not is_kill:
                continue
            
            # Calculate position above the target unit
            x = self.scene.grid_origin_x + target.gx * self.scene.cell_size + self.scene.cell_size // 2
            y = self.scene.grid_origin_y + target.gy * self.scene.cell_size - y_offset
            
            # Calculate alpha based on remaining time (fade out)
            # Use longer max time for more visibility
            max_time = 2.0 if is_crit else 1.8
            alpha = min(255, int(255 * (timer / max_time)))
            
            # Color based on crit status and damage
            if is_crit:
                color = (255, 255, 100)  # Bright yellow for crits
                damage_text = f"CRIT! -{damage}"
            elif is_kill:
                color = (255, 200, 0)  # Orange for kills
                damage_text = f"-{damage}!"
            elif damage >= 20:
                color = (255, 100, 100)  # Bright red for big hits
                damage_text = f"-{damage}"
            elif damage >= 10:
                color = (255, 150, 150)  # Medium red
                damage_text = f"-{damage}"
            else:
                color = (255, 200, 200)  # Light red for small hits
                damage_text = f"-{damage}"
            
            # Use larger font for damage numbers
            damage_font = getattr(self, "damage_font", self.font)
            
            # Render damage text with shadow for visibility (larger shadow for bigger text)
            # Shadow
            shadow_surf = damage_font.render(damage_text, True, (0, 0, 0))
            surface.blit(shadow_surf, (x - shadow_surf.get_width() // 2 + 2, y + 2))
            # Main text
            text_surf = damage_font.render(damage_text, True, color)
            text_x = x - text_surf.get_width() // 2
            text_y = y
            surface.blit(text_surf, (text_x, text_y))
            
            # Draw additional crit indicator (star or sparkle) - bigger for larger font
            if is_crit:
                crit_size = 12  # Increased from 8
                pygame.draw.circle(surface, (255, 255, 200), (x, y - 20), crit_size, 2)
                pygame.draw.line(surface, (255, 255, 200), (x - crit_size, y - 20), (x + crit_size, y - 20), 2)
                pygame.draw.line(surface, (255, 255, 200), (x, y - 20 - crit_size), (x, y - 20 + crit_size), 2)

    def draw_hit_sparks(self, surface: pygame.Surface) -> None:
        """Draw hit spark effects at impact locations."""
        for spark in self.scene._hit_sparks:
            x = spark["x"]
            y = spark["y"]
            timer = spark["timer"]
            is_crit = spark.get("is_crit", False)
            
            # Spark size based on remaining time (fade out)
            max_time = 0.3
            size = int(6 * (timer / max_time))
            
            if size <= 0:
                continue
            
            # Color based on crit
            if is_crit:
                color = (255, 255, 150)  # Yellow spark for crits
                # Draw multiple sparks for crit (4 sparks in a cross pattern)
                for i in range(4):
                    angle = (i * 90) * math.pi / 180
                    offset = size
                    spark_x = int(x + offset * math.cos(angle))
                    spark_y = int(y + offset * math.sin(angle))
                    pygame.draw.circle(surface, color, (spark_x, spark_y), size // 2)
                # Center spark
                pygame.draw.circle(surface, (255, 255, 200), (x, y), size)
            else:
                color = (255, 200, 100)  # Orange spark
                pygame.draw.circle(surface, color, (x, y), size)
    
    def draw_damage_preview(self, surface: pygame.Surface, target: BattleUnit, normal_damage: int, crit_damage: Optional[int]) -> None:
        """Draw damage preview above the selected target."""
        x = self.scene.grid_origin_x + target.gx * self.scene.cell_size + self.scene.cell_size // 2
        y = self.scene.grid_origin_y + target.gy * self.scene.cell_size - 35  # Above the unit
        
        # Build preview text
        if crit_damage is not None and crit_damage > normal_damage:
            preview_text = f"{normal_damage}-{crit_damage} dmg ({int(BASE_CRIT_CHANCE * 100)}% crit)"
        else:
            preview_text = f"{normal_damage} dmg"
        
        # Create background panel
        text_surf = self.font.render(preview_text, True, (255, 255, 255))
        panel_w = text_surf.get_width() + 12
        panel_h = text_surf.get_height() + 6
        panel_x = x - panel_w // 2
        panel_y = y - panel_h // 2
        
        # Semi-transparent dark background
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 200))
        surface.blit(panel, (panel_x, panel_y))
        
        # Border
        pygame.draw.rect(surface, (150, 200, 255), (panel_x, panel_y, panel_w, panel_h), 2)
        
        # Text
        text_x = x - text_surf.get_width() // 2
        text_y = y - text_surf.get_height() // 2
        surface.blit(text_surf, (text_x, text_y))
    
    def draw_enemy_info_panel(self, surface: pygame.Surface, target: BattleUnit, screen_w: int) -> None:
        """Draw enemy stat information panel when targeting."""
        if target.side == "player":
            return  # Only show for enemies
        
        # Calculate position based on enemy cards
        # Enemy cards are drawn starting at enemy_y = 20, with 70 height + 10 spacing each
        card_width = 180
        enemy_x = screen_w - card_width - 20
        enemy_y = 20
        card_h = 70
        card_spacing = 10
        
        # Count how many enemy cards are drawn (alive enemies)
        num_enemy_cards = sum(1 for u in self.scene.enemy_units if u.is_alive)
        
        # Position panel below all enemy cards
        panel_w = 200
        panel_h = 100
        panel_x = screen_w - panel_w - 20
        panel_y = enemy_y + (num_enemy_cards * (card_h + card_spacing)) + 10  # Below all enemy cards with spacing
        
        # Background
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 30, 220))
        surface.blit(panel, (panel_x, panel_y))
        
        # Border
        pygame.draw.rect(surface, (150, 100, 100), (panel_x, panel_y, panel_w, panel_h), 2)
        
        # Title
        title_surf = self.font.render("Target Info", True, (255, 200, 200))
        surface.blit(title_surf, (panel_x + 6, panel_y + 4))
        
        # Stats
        text_y = panel_y + 24
        atk = getattr(target.entity, "attack_power", 0)
        defense = getattr(target.entity, "defense", 0)
        hp_ratio = target.hp / target.max_hp if target.max_hp > 0 else 0
        
        stats = [
            f"HP: {target.hp}/{target.max_hp} ({int(hp_ratio * 100)}%)",
            f"ATK: {atk}",
            f"DEF: {defense}",
        ]
        
        for stat_text in stats:
            stat_surf = self.font.render(stat_text, True, (220, 220, 220))
            surface.blit(stat_surf, (panel_x + 6, text_y))
            text_y += 18
        
        # Status effects
        if target.statuses:
            status_names = [s.name.title() for s in target.statuses[:3]]  # Show first 3
            status_text = "Status: " + ", ".join(status_names)
            if len(target.statuses) > 3:
                status_text += "..."
            status_surf = self.font.render(status_text, True, (200, 200, 255))
            surface.blit(status_surf, (panel_x + 6, text_y))
    
    def draw_range_visualization(self, surface: pygame.Surface, unit: BattleUnit) -> None:
        """Draw range visualization on the grid when targeting."""
        if self.scene.targeting_mode is None:
            return
        
        action_type = self.scene.targeting_mode.get("action_type")
        skill = self.scene.targeting_mode.get("skill")
        current_target = self.scene._get_current_target()
        
        # Determine range
        max_range = 1
        if action_type == "attack":
            max_range = self.scene.combat._get_weapon_range(unit)
        elif action_type == "skill" and skill is not None:
            max_range = getattr(skill, "range_tiles", 1)
        
        # Draw range tiles (where you can target)
        range_color = (100, 150, 255, 80)  # Semi-transparent blue
        unit_gx, unit_gy = unit.gx, unit.gy
        
        # Determine if we should use Chebyshev distance (for melee) or Manhattan (for ranged)
        use_chebyshev = False
        if action_type == "attack":
            weapon_range = self.scene.combat._get_weapon_range(unit)
            use_chebyshev = (weapon_range == 1)  # Melee uses Chebyshev
        elif action_type == "skill" and skill is not None:
            # Skills can opt into Manhattan targeting (future ranged-by-tiles),
            # but default to Chebyshev so "adjacent" includes diagonals.
            use_chebyshev = getattr(skill, "range_metric", "chebyshev") == "chebyshev"
        
        for gx in range(self.scene.grid_width):
            for gy in range(self.scene.grid_height):
                # Calculate distance using appropriate metric
                if use_chebyshev:
                    dx = abs(gx - unit_gx)
                    dy = abs(gy - unit_gy)
                    distance = max(dx, dy)
                else:
                    distance = abs(gx - unit_gx) + abs(gy - unit_gy)
                
                if distance <= max_range and distance > 0:  # Don't highlight unit's own tile
                    x = self.scene.grid_origin_x + gx * self.scene.cell_size
                    y = self.scene.grid_origin_y + gy * self.scene.cell_size
                    rect = pygame.Rect(x, y, self.scene.cell_size, self.scene.cell_size)
                    
                    # Semi-transparent overlay
                    overlay = pygame.Surface((self.scene.cell_size, self.scene.cell_size), pygame.SRCALPHA)
                    overlay.fill(range_color)
                    surface.blit(overlay, (x, y))
        
        # Draw AoE area if skill has AoE and a target is selected
        if action_type == "skill" and skill is not None and current_target is not None:
            aoe_radius = getattr(skill, "aoe_radius", 0)
            if aoe_radius > 0:
                from engine.battle.aoe import get_tiles_in_aoe
                
                # Get AoE tiles centered on the selected target
                aoe_tiles = get_tiles_in_aoe(
                    current_target.gx,
                    current_target.gy,
                    aoe_radius,
                    getattr(skill, "aoe_shape", "circle"),
                    self.scene.grid_width,
                    self.scene.grid_height,
                )
                
                # Draw AoE area overlay (red/orange tint to indicate damage area)
                aoe_color = (255, 150, 100, 120)  # Semi-transparent orange-red
                for gx, gy in aoe_tiles:
                    x = self.scene.grid_origin_x + gx * self.scene.cell_size
                    y = self.scene.grid_origin_y + gy * self.scene.cell_size
                    
                    # Draw AoE overlay
                    overlay = pygame.Surface((self.scene.cell_size, self.scene.cell_size), pygame.SRCALPHA)
                    overlay.fill(aoe_color)
                    surface.blit(overlay, (x, y))
                    
                    # Draw border to make it more visible
                    rect = pygame.Rect(x, y, self.scene.cell_size, self.scene.cell_size)
                    pygame.draw.rect(surface, (255, 200, 150), rect, width=2)

    def draw_turn_order_indicator(self, surface: pygame.Surface, screen_w: int) -> None:
        """Draw a small indicator showing the next few units in turn order."""
        if not self.scene.turn_order:
            return
        
        # Get next 4 units in turn order (current + next 3)
        next_units: List[BattleUnit] = []
        current_idx = self.scene.turn_index
        
        for i in range(4):
            idx = (current_idx + i) % len(self.scene.turn_order)
            unit = self.scene.turn_order[idx]
            if unit.is_alive:
                next_units.append(unit)
            if len(next_units) >= 4:
                break
        
        if len(next_units) <= 1:
            return  # Don't show if only current unit
        
        # Draw small icons/names for upcoming turns
        indicator_y = 115  # Just below the active unit panel
        indicator_w = len(next_units) * 90
        if indicator_w < 200:
            indicator_w = 200  # Minimum width
        indicator_x = (screen_w - indicator_w) // 2
        
        # Background panel
        panel_h = 30
        panel = pygame.Surface((indicator_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        surface.blit(panel, (indicator_x, indicator_y))
        
        # Draw each upcoming unit
        x_offset = 0
        for i, unit in enumerate(next_units):
            if i == 0:
                label = "NOW"
                color = (255, 255, 150)  # Current turn
            else:
                label = unit.name[:6]  # Truncate long names
                if unit.side == "player":
                    color = COLOR_PLAYER
                else:
                    color = COLOR_ENEMY
            
            # Small icon/indicator
            icon_size = 20
            icon_x = indicator_x + x_offset + 5
            icon_y = indicator_y + 5
            
            # Draw colored square for the unit
            pygame.draw.rect(surface, color, (icon_x, icon_y, icon_size, icon_size))
            pygame.draw.rect(surface, (100, 100, 100), (icon_x, icon_y, icon_size, icon_size), 1)
            
            # Unit name/label
            label_surf = self.font.render(label, True, (220, 220, 220))
            label_x = icon_x + icon_size + 4
            label_y = icon_y + (icon_size - label_surf.get_height()) // 2
            surface.blit(label_surf, (label_x, label_y))
            
            x_offset += 90

