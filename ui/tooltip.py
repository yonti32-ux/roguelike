"""
Tooltip system for displaying detailed information on hover.

This module provides a reusable tooltip system that can display
rich information about items, stats, skills, etc. when the mouse
hovers over UI elements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Dict, Any
import pygame

if TYPE_CHECKING:
    from engine.game import Game
    from systems.inventory import ItemDef


class Tooltip:
    """Manages tooltip display and positioning."""
    
    def __init__(self):
        self.current_tooltip: Optional[TooltipData] = None
        self.mouse_pos: Tuple[int, int] = (0, 0)
        self.show_delay: float = 0.3  # Seconds before showing tooltip
        self.accumulated_time: float = 0.0
        self.hover_target: Optional[Any] = None
    
    def update(self, dt: float, mouse_pos: Tuple[int, int], hover_target: Optional[Any] = None) -> None:
        """Update tooltip state based on mouse position and hover target."""
        if hover_target != self.hover_target:
            # Target changed, reset timer
            self.hover_target = hover_target
            self.accumulated_time = 0.0
            self.current_tooltip = None
        
        if hover_target is not None:
            self.accumulated_time += dt
            if self.accumulated_time >= self.show_delay:
                # Create tooltip data from target
                self.current_tooltip = self._create_tooltip_data(hover_target)
            else:
                self.current_tooltip = None
        else:
            self.current_tooltip = None
            self.accumulated_time = 0.0
        
        self.mouse_pos = mouse_pos
    
    def _create_tooltip_data(self, target: Any) -> Optional[TooltipData]:
        """Create tooltip data from a hover target."""
        if isinstance(target, dict):
            # Dictionary with tooltip info
            return TooltipData(
                title=target.get("title", ""),
                lines=target.get("lines", []),
                stats=target.get("stats", {}),
            )
        elif hasattr(target, "tooltip_data"):
            # Object with tooltip_data method
            return target.tooltip_data()
        return None
    
    def clear(self) -> None:
        """Clear the current tooltip."""
        self.current_tooltip = None
        self.hover_target = None
        self.accumulated_time = 0.0
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the tooltip if it should be visible."""
        if self.current_tooltip is None:
            return
        
        self.current_tooltip.draw(screen, font, self.mouse_pos)


class TooltipData:
    """Data structure for tooltip content."""
    
    def __init__(
        self,
        title: str = "",
        lines: List[str] = None,
        stats: Dict[str, float] = None,
        comparison_stats: Optional[Dict[str, Tuple[float, float]]] = None,
    ):
        self.title = title
        self.lines = lines or []
        self.stats = stats or {}
        self.comparison_stats = comparison_stats  # Dict of stat_name -> (current, new)
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font, mouse_pos: Tuple[int, int]) -> None:
        """Draw the tooltip at the mouse position."""
        if not self.title and not self.lines and not self.stats:
            return
        
        # Calculate tooltip size
        padding = 8
        line_height = 20
        spacing = 4
        
        lines_to_render: List[Tuple[str, Tuple[int, int, int]]] = []
        
        # Title
        if self.title:
            lines_to_render.append((self.title, (255, 255, 200)))
        
        # Regular lines
        for line in self.lines:
            lines_to_render.append((line, (220, 220, 220)))
        
        # Stats
        if self.stats:
            for stat_name, value in self.stats.items():
                stat_label = _format_stat_name(stat_name)
                stat_value = _format_stat_value(value)
                lines_to_render.append((f"{stat_label}: {stat_value}", (200, 220, 255)))
        
        # Comparison stats (show differences)
        if self.comparison_stats:
            lines_to_render.append(("", (0, 0, 0)))  # Separator
            for stat_name, (current, new) in self.comparison_stats.items():
                stat_label = _format_stat_name(stat_name)
                diff = new - current
                if abs(diff) < 0.01:
                    # No change
                    line = f"{stat_label}: {_format_stat_value(new)}"
                    color = (200, 200, 200)
                elif diff > 0:
                    # Increase
                    line = f"{stat_label}: {_format_stat_value(new)} (+{_format_stat_value(diff)})"
                    color = (150, 255, 150)
                else:
                    # Decrease
                    line = f"{stat_label}: {_format_stat_value(new)} ({_format_stat_value(diff)})"
                    color = (255, 150, 150)
                lines_to_render.append((line, color))
        
        if not lines_to_render:
            return
        
        # Calculate dimensions
        max_width = 0
        for line, _ in lines_to_render:
            if line:  # Skip empty separator lines
                surf = font.render(line, True, (255, 255, 255))
                max_width = max(max_width, surf.get_width())
        
        tooltip_width = max_width + padding * 2
        tooltip_height = len(lines_to_render) * line_height + padding * 2
        
        # Position tooltip (prefer top-right of cursor, adjust if off-screen)
        mx, my = mouse_pos
        screen_w, screen_h = screen.get_size()
        
        tooltip_x = mx + 15
        tooltip_y = my - tooltip_height - 5
        
        # Adjust if off-screen
        if tooltip_x + tooltip_width > screen_w:
            tooltip_x = mx - tooltip_width - 15
        if tooltip_y < 0:
            tooltip_y = my + 15
        
        # Draw background
        bg_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        bg_surface.fill((20, 20, 30, 240))
        pygame.draw.rect(bg_surface, (100, 100, 130), (0, 0, tooltip_width, tooltip_height), 2)
        screen.blit(bg_surface, (tooltip_x, tooltip_y))
        
        # Draw text
        y_offset = padding
        for line, color in lines_to_render:
            if line:  # Skip empty separator lines
                text_surf = font.render(line, True, color)
                screen.blit(text_surf, (tooltip_x + padding, tooltip_y + y_offset))
            y_offset += line_height


def _format_stat_name(stat_name: str) -> str:
    """Format a stat name for display."""
    mapping = {
        "attack": "ATK",
        "defense": "DEF",
        "max_hp": "HP",
        "hp": "HP",
        "max_stamina": "STA",
        "max_mana": "MANA",
        "range": "RNG",
        "crit_chance": "CRIT",
        "skill_power": "Skill Power",
    }
    return mapping.get(stat_name.lower(), stat_name.replace("_", " ").title())


def _format_stat_value(value: float) -> str:
    """Format a stat value for display."""
    if isinstance(value, int) or value.is_integer():
        return str(int(value))
    return f"{value:.1f}"


def create_item_tooltip_data(
    item_def: "ItemDef",
    game: "Game",
    character_is_hero: bool = True,
    character_comp: Optional[Any] = None,
) -> TooltipData:
    """
    Create tooltip data for an item, including stat comparison.
    
    Args:
        item_def: The item definition
        game: Game instance
        character_is_hero: True if hero, False if companion
        character_comp: Companion state if character_is_hero is False
    
    Returns:
        TooltipData with item information and stat comparisons
    """
    from systems.inventory import get_item_def
    
    title = item_def.name
    if item_def.rarity:
        title += f" [{item_def.rarity.capitalize()}]"
    
    lines: List[str] = []
    if item_def.description:
        # Wrap description if too long
        desc = item_def.description
        if len(desc) > 60:
            # Simple word wrap
            words = desc.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 60:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                else:
                    current_line += (" " if current_line else "") + word
            if current_line:
                lines.append(current_line)
        else:
            lines.append(desc)
    
    # Get current stats for the character
    current_stats: Dict[str, float] = {}
    if character_is_hero:
        hero_stats = getattr(game, "hero_stats", None)
        if hero_stats:
            current_stats = {
                "attack": float(getattr(hero_stats, "attack_power", 0)),
                "defense": float(getattr(hero_stats, "defense", 0)),
                "max_hp": float(getattr(hero_stats, "max_hp", 0)),
            }
            # Add equipment bonuses
            inv = getattr(game, "inventory", None)
            if inv:
                gear_mods = inv.total_stat_modifiers()
                for stat, value in gear_mods.items():
                    if stat in current_stats:
                        current_stats[stat] -= value  # Remove gear to get base
    else:
        if character_comp:
            current_stats = {
                "attack": float(getattr(character_comp, "attack_power", 0)),
                "defense": float(getattr(character_comp, "defense", 0)),
                "max_hp": float(getattr(character_comp, "max_hp", 0)),
            }
            # Remove equipment bonuses
            comp_equipped = getattr(character_comp, "equipped", None) or {}
            for slot, equipped_id in comp_equipped.items():
                if equipped_id:
                    equipped_item = get_item_def(equipped_id)
                    if equipped_item:
                        for stat, value in equipped_item.stats.items():
                            if stat in current_stats:
                                current_stats[stat] -= value
    
    # Calculate new stats if this item were equipped
    comparison_stats: Dict[str, Tuple[float, float]] = {}
    if item_def.slot and item_def.slot != "consumable":
        # Get currently equipped item in this slot
        if character_is_hero:
            inv = getattr(game, "inventory", None)
            if inv:
                current_equipped_id = inv.equipped.get(item_def.slot)
                if current_equipped_id:
                    current_equipped = get_item_def(current_equipped_id)
                    if current_equipped:
                        # Remove current item's stats
                        for stat, value in current_equipped.stats.items():
                            if stat in current_stats:
                                current_stats[stat] -= value
        else:
            if character_comp:
                comp_equipped = getattr(character_comp, "equipped", None) or {}
                current_equipped_id = comp_equipped.get(item_def.slot)
                if current_equipped_id:
                    current_equipped = get_item_def(current_equipped_id)
                    if current_equipped:
                        for stat, value in current_equipped.stats.items():
                            if stat in current_stats:
                                current_stats[stat] -= value
        
        # Calculate new stats with this item
        for stat_name, base_value in current_stats.items():
            new_value = base_value
            if stat_name in item_def.stats:
                new_value += item_def.stats[stat_name]
            comparison_stats[stat_name] = (base_value, new_value)
    
    # Filter out zero/irrelevant stats from display
    filtered_stats: Dict[str, float] = {}
    for stat_name, stat_value in item_def.stats.items():
        # Only include stats that are non-zero and relevant
        if abs(stat_value) > 0.01:  # Small threshold to avoid floating point issues
            filtered_stats[stat_name] = stat_value
    
    # Filter comparison stats to only show stats that would actually change
    filtered_comparison: Optional[Dict[str, Tuple[float, float]]] = None
    if comparison_stats:
        filtered_comparison = {}
        for stat_name, (current, new) in comparison_stats.items():
            # Only show if the item actually affects this stat or if there's a meaningful change
            if stat_name in item_def.stats and abs(item_def.stats[stat_name]) > 0.01:
                filtered_comparison[stat_name] = (current, new)
            elif abs(new - current) > 0.01:  # Show if there's any change
                filtered_comparison[stat_name] = (current, new)
        if not filtered_comparison:
            filtered_comparison = None
    
    return TooltipData(
        title=title,
        lines=lines,
        stats=filtered_stats,
        comparison_stats=filtered_comparison,
    )

