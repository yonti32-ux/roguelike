"""
Debug Console System

Provides a real-time debug overlay showing:
- Error logs
- Performance metrics (FPS, memory)
- Game state information
- System information
- Recent events

Toggle with F12 or ~ (tilde key)
"""
import pygame
import sys
import traceback
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

# Try to import psutil for system info (optional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import os

class DebugConsole:
    """
    Debug console overlay that displays backend information.
    """
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = False
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Console dimensions
        screen_w, screen_h = screen.get_size()
        self.console_width = int(screen_w * 0.8)
        self.console_height = int(screen_h * 0.7)
        self.console_x = (screen_w - self.console_width) // 2
        self.console_y = (screen_h - self.console_height) // 2
        
        # Font setup
        self.font_size = 14
        self.font = pygame.font.Font(None, self.font_size)
        self.font_bold = pygame.font.Font(None, self.font_size)
        self.font_bold.set_bold(True)
        
        # Colors
        self.bg_color = (20, 20, 30, 240)  # Semi-transparent dark
        self.text_color = (200, 200, 200)
        self.error_color = (255, 100, 100)
        self.warning_color = (255, 200, 100)
        self.info_color = (100, 200, 255)
        self.success_color = (100, 255, 100)
        self.header_color = (150, 150, 255)
        self.border_color = (100, 100, 150)
        
        # Sections
        self.current_section = "overview"  # overview, errors, performance, state, logs
        self.sections = ["overview", "errors", "performance", "state", "logs"]
        
        # Error log cache (last 50 errors)
        self.error_log: List[Dict[str, Any]] = []
        self.max_error_log = 50
        
        # Performance metrics
        self.fps_history: List[float] = []
        self.max_fps_history = 60
        
        # Event log (recent game events)
        self.event_log: List[Dict[str, Any]] = []
        self.max_event_log = 100
        
        # Line height for scrolling
        self.line_height = self.font_size + 4
        self.lines_per_page = (self.console_height - 80) // self.line_height
        
    def toggle(self) -> None:
        """Toggle console visibility."""
        self.visible = not self.visible
        if self.visible:
            self.scroll_offset = 0
    
    def is_visible(self) -> bool:
        """Check if console is visible."""
        return self.visible
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """Add an error to the error log."""
        error_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "traceback": traceback.format_exc(),
        }
        self.error_log.append(error_entry)
        if len(self.error_log) > self.max_error_log:
            self.error_log.pop(0)
    
    def log_event(self, event_type: str, message: str, data: Optional[Dict] = None) -> None:
        """Add an event to the event log."""
        event_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "type": event_type,
            "message": message,
            "data": data or {},
        }
        self.event_log.append(event_entry)
        if len(self.event_log) > self.max_event_log:
            self.event_log.pop(0)
    
    def update_fps(self, fps: float) -> None:
        """Update FPS history."""
        self.fps_history.append(fps)
        if len(self.fps_history) > self.max_fps_history:
            self.fps_history.pop(0)
    
    def handle_event(self, event: pygame.event.Event, game: Optional[Any] = None) -> bool:
        """
        Handle input events for the debug console.
        
        Returns True if event was consumed by console.
        """
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            # Close console
            if event.key == pygame.K_F12 or event.key == pygame.K_BACKQUOTE:  # F12 or ~
                self.toggle()
                return True
            
            # Section navigation
            if event.key == pygame.K_TAB:
                # Cycle through sections
                current_idx = self.sections.index(self.current_section)
                next_idx = (current_idx + 1) % len(self.sections)
                self.current_section = self.sections[next_idx]
                self.scroll_offset = 0
                return True
            
            # Scrolling
            if event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
                return True
            if event.key == pygame.K_DOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 1)
                return True
            if event.key == pygame.K_PAGEUP:
                self.scroll_offset = max(0, self.scroll_offset - self.lines_per_page)
                return True
            if event.key == pygame.K_PAGEDOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.lines_per_page)
                return True
            if event.key == pygame.K_HOME:
                self.scroll_offset = 0
                return True
            if event.key == pygame.K_END:
                self.scroll_offset = self.max_scroll
                return True
            
            # Clear logs
            if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                if self.current_section == "errors":
                    self.error_log.clear()
                elif self.current_section == "logs":
                    self.event_log.clear()
                return True
        
        return False
    
    def draw(self, game: Optional[Any] = None, clock: Optional[pygame.time.Clock] = None) -> None:
        """Draw the debug console overlay."""
        if not self.visible:
            return
        
        # Update FPS if clock provided
        if clock:
            self.update_fps(clock.get_fps())
        
        # Create semi-transparent background
        overlay = pygame.Surface((self.console_width, self.console_height), pygame.SRCALPHA)
        overlay.fill(self.bg_color)
        
        # Draw border
        pygame.draw.rect(overlay, self.border_color, overlay.get_rect(), 2)
        
        # Draw header
        header_text = f"DEBUG CONSOLE - {self.current_section.upper()} (F12 or ~ to close, TAB to switch sections)"
        header_surface = self.font_bold.render(header_text, True, self.header_color)
        overlay.blit(header_surface, (10, 10))
        
        # Draw section tabs
        tab_y = 35
        tab_width = 120
        for i, section in enumerate(self.sections):
            tab_x = 10 + i * (tab_width + 5)
            tab_color = self.header_color if section == self.current_section else self.text_color
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, 25)
            pygame.draw.rect(overlay, tab_color, tab_rect, 1)
            tab_text = self.font.render(section.capitalize(), True, tab_color)
            text_rect = tab_text.get_rect(center=tab_rect.center)
            overlay.blit(tab_text, text_rect)
        
        # Draw content based on current section
        content_y = 70
        content_height = self.console_height - content_y - 30
        
        if self.current_section == "overview":
            self._draw_overview(overlay, content_y, content_height, game, clock)
        elif self.current_section == "errors":
            self._draw_errors(overlay, content_y, content_height)
        elif self.current_section == "performance":
            self._draw_performance(overlay, content_y, content_height, clock)
        elif self.current_section == "state":
            self._draw_state(overlay, content_y, content_height, game)
        elif self.current_section == "logs":
            self._draw_logs(overlay, content_y, content_height)
        
        # Draw footer with controls
        footer_text = "UP/DOWN: Scroll | HOME/END: Top/Bottom | CTRL+C: Clear logs"
        footer_surface = self.font.render(footer_text, True, self.text_color)
        overlay.blit(footer_surface, (10, self.console_height - 20))
        
        # Blit overlay to screen
        self.screen.blit(overlay, (self.console_x, self.console_y))
    
    def _draw_overview(self, overlay: pygame.Surface, y: int, height: int, 
                      game: Optional[Any], clock: Optional[pygame.time.Clock]) -> None:
        """Draw overview section."""
        lines = []
        
        # Performance
        if clock:
            fps = clock.get_fps()
            avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
            lines.append(("Performance", self.header_color))
            lines.append((f"  FPS: {fps:.1f} (avg: {avg_fps:.1f})", self.info_color))
        
        # Memory
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                lines.append((f"  Memory: {memory_mb:.1f} MB", self.info_color))
            except:
                lines.append(("  Memory: N/A", self.text_color))
        else:
            lines.append(("  Memory: psutil not available", self.warning_color))
        
        # Game state
        if game:
            lines.append(("", None))
            lines.append(("Game State", self.header_color))
            lines.append((f"  Mode: {getattr(game, 'mode', 'unknown')}", self.text_color))
            lines.append((f"  Floor: {getattr(game, 'floor', 0)}", self.text_color))
            if hasattr(game, 'player') and game.player:
                lines.append((f"  Player HP: {game.player.hp}/{getattr(game.player, 'max_hp', 0)}", 
                            self.success_color if game.player.hp > game.player.max_hp * 0.5 else self.warning_color))
        
        # Recent errors
        lines.append(("", None))
        lines.append(("Recent Errors", self.header_color))
        if self.error_log:
            recent_errors = self.error_log[-5:]
            for error in recent_errors:
                lines.append((f"  [{error['timestamp']}] {error['type']}: {error['message'][:50]}", 
                            self.error_color))
        else:
            lines.append(("  No errors", self.success_color))
        
        # Recent events
        lines.append(("", None))
        lines.append(("Recent Events", self.header_color))
        if self.event_log:
            recent_events = self.event_log[-5:]
            for event in recent_events:
                lines.append((f"  [{event['timestamp']}] {event['type']}: {event['message'][:50]}", 
                            self.info_color))
        else:
            lines.append(("  No events", self.text_color))
        
        self._draw_lines(overlay, lines, y, height)
    
    def _draw_errors(self, overlay: pygame.Surface, y: int, height: int) -> None:
        """Draw errors section."""
        lines = []
        
        if not self.error_log:
            lines.append(("No errors logged", self.success_color))
        else:
            # Show errors in reverse order (newest first)
            for error in reversed(self.error_log):
                lines.append((f"[{error['timestamp']}] {error['type']}", self.error_color))
                lines.append((f"  Context: {error['context']}", self.text_color))
                lines.append((f"  Message: {error['message']}", self.warning_color))
                
                # Show first few lines of traceback
                tb_lines = error['traceback'].split('\n')[:3]
                for tb_line in tb_lines:
                    if tb_line.strip():
                        lines.append((f"    {tb_line[:80]}", self.text_color))
                
                lines.append(("", None))  # Spacing
        
        self._draw_lines(overlay, lines, y, height)
    
    def _draw_performance(self, overlay: pygame.Surface, y: int, height: int, 
                         clock: Optional[pygame.time.Clock]) -> None:
        """Draw performance section."""
        lines = []
        
        # FPS
        if clock:
            fps = clock.get_fps()
            avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
            min_fps = min(self.fps_history) if self.fps_history else 0
            max_fps = max(self.fps_history) if self.fps_history else 0
            
            lines.append(("FPS Statistics", self.header_color))
            lines.append((f"  Current: {fps:.1f}", self.info_color))
            lines.append((f"  Average: {avg_fps:.1f}", self.info_color))
            lines.append((f"  Min: {min_fps:.1f}", self.error_color if min_fps < 30 else self.text_color))
            lines.append((f"  Max: {max_fps:.1f}", self.success_color))
            lines.append((f"  Samples: {len(self.fps_history)}", self.text_color))
        
        # Memory
        lines.append(("", None))
        lines.append(("Memory Usage", self.header_color))
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                lines.append((f"  RSS: {memory_mb:.1f} MB", self.info_color))
                
                # System memory
                system_memory = psutil.virtual_memory()
                lines.append((f"  System Total: {system_memory.total / 1024 / 1024 / 1024:.1f} GB", self.text_color))
                lines.append((f"  System Available: {system_memory.available / 1024 / 1024 / 1024:.1f} GB", 
                            self.success_color if system_memory.percent < 80 else self.warning_color))
                lines.append((f"  System Used: {system_memory.percent:.1f}%", 
                            self.error_color if system_memory.percent > 90 else self.text_color))
            except Exception as e:
                lines.append((f"  Error getting memory info: {str(e)}", self.error_color))
        else:
            lines.append(("  psutil not available (install for memory stats)", self.warning_color))
        
        # CPU
        lines.append(("", None))
        lines.append(("CPU Usage", self.header_color))
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(os.getpid())
                cpu_percent = process.cpu_percent(interval=0.1)
                lines.append((f"  Process: {cpu_percent:.1f}%", self.info_color))
                
                system_cpu = psutil.cpu_percent(interval=0.1)
                lines.append((f"  System: {system_cpu:.1f}%", self.text_color))
            except Exception as e:
                lines.append((f"  Error getting CPU info: {str(e)}", self.error_color))
        else:
            lines.append(("  psutil not available (install for CPU stats)", self.warning_color))
        
        self._draw_lines(overlay, lines, y, height)
    
    def _draw_state(self, overlay: pygame.Surface, y: int, height: int, game: Optional[Any]) -> None:
        """Draw game state section."""
        lines = []
        
        if not game:
            lines.append(("No game instance available", self.error_color))
        else:
            # Basic game info
            lines.append(("Game Information", self.header_color))
            lines.append((f"  Mode: {getattr(game, 'mode', 'unknown')}", self.text_color))
            lines.append((f"  Floor: {getattr(game, 'floor', 0)}", self.text_color))
            lines.append((f"  Paused: {getattr(game, 'paused', False)}", self.text_color))
            
            # Hero stats
            if hasattr(game, 'hero_stats'):
                hero = game.hero_stats
                lines.append(("", None))
                lines.append(("Hero Stats", self.header_color))
                lines.append((f"  Level: {getattr(hero, 'level', 0)}", self.text_color))
                lines.append((f"  XP: {getattr(hero, 'xp', 0)}", self.text_color))
                lines.append((f"  Gold: {getattr(hero, 'gold', 0)}", self.text_color))
                lines.append((f"  Class: {getattr(hero, 'hero_class_id', 'unknown')}", self.text_color))
                lines.append((f"  Name: {getattr(hero, 'hero_name', 'unknown')}", self.text_color))
            
            # Player entity
            if hasattr(game, 'player') and game.player:
                player = game.player
                lines.append(("", None))
                lines.append(("Player Entity", self.header_color))
                lines.append((f"  HP: {player.hp}/{getattr(player, 'max_hp', 0)}", 
                            self.success_color if player.hp > getattr(player, 'max_hp', 0) * 0.5 else self.warning_color))
                lines.append((f"  Position: ({player.x:.1f}, {player.y:.1f})", self.text_color))
                if hasattr(player, 'max_stamina'):
                    lines.append((f"  Stamina: {getattr(player, 'stamina', 0)}/{player.max_stamina}", self.text_color))
                if hasattr(player, 'max_mana'):
                    lines.append((f"  Mana: {getattr(player, 'mana', 0)}/{player.max_mana}", self.text_color))
            
            # Inventory
            if hasattr(game, 'inventory'):
                inv = game.inventory
                lines.append(("", None))
                lines.append(("Inventory", self.header_color))
                lines.append((f"  Items: {len(getattr(inv, 'items', []))}", self.text_color))
                lines.append((f"  Equipped: {len(getattr(inv, 'equipped', {}))}", self.text_color))
            
            # Party
            if hasattr(game, 'party'):
                party = game.party
                lines.append(("", None))
                lines.append(("Party", self.header_color))
                lines.append((f"  Companions: {len(party)}", self.text_color))
                for i, comp in enumerate(party):
                    comp_name = getattr(comp, 'name_override', None) or getattr(comp, 'template_id', 'Unknown')
                    comp_level = getattr(comp, 'level', 0)
                    lines.append((f"    {i+1}. {comp_name} (Lv.{comp_level})", self.text_color))
            
            # Map info
            if hasattr(game, 'current_map') and game.current_map:
                map_obj = game.current_map
                lines.append(("", None))
                lines.append(("Map", self.header_color))
                lines.append((f"  Size: {getattr(map_obj, 'width', 0)}x{getattr(map_obj, 'height', 0)}", self.text_color))
                lines.append((f"  Explored: {len(getattr(map_obj, 'explored', set()))} tiles", self.text_color))
                lines.append((f"  Visible: {len(getattr(map_obj, 'visible', set()))} tiles", self.text_color))
                lines.append((f"  Entities: {len(getattr(map_obj, 'entities', []))}", self.text_color))
        
        self._draw_lines(overlay, lines, y, height)
    
    def _draw_logs(self, overlay: pygame.Surface, y: int, height: int) -> None:
        """Draw event logs section."""
        lines = []
        
        if not self.event_log:
            lines.append(("No events logged", self.text_color))
        else:
            # Show events in reverse order (newest first)
            for event in reversed(self.event_log):
                color = self.info_color
                if event['type'] == 'error':
                    color = self.error_color
                elif event['type'] == 'warning':
                    color = self.warning_color
                elif event['type'] == 'success':
                    color = self.success_color
                
                lines.append((f"[{event['timestamp']}] {event['type'].upper()}: {event['message']}", color))
                
                # Show data if available
                if event.get('data'):
                    for key, value in event['data'].items():
                        lines.append((f"    {key}: {value}", self.text_color))
        
        self._draw_lines(overlay, lines, y, height)
    
    def _draw_lines(self, overlay: pygame.Surface, lines: List[tuple], y: int, height: int) -> None:
        """Draw a list of text lines with scrolling."""
        current_y = y - (self.scroll_offset * self.line_height)
        
        visible_lines = []
        for line_text, color in lines:
            if current_y >= y and current_y < y + height:
                visible_lines.append((line_text, color, current_y))
            current_y += self.line_height
        
        # Update max scroll
        total_lines = len(lines)
        self.max_scroll = max(0, total_lines - self.lines_per_page)
        
        # Draw visible lines
        for line_text, color, line_y in visible_lines:
            if color is None:
                continue
            
            # Wrap long lines
            max_width = self.console_width - 20
            if self.font.size(line_text)[0] > max_width:
                # Simple word wrap (could be improved)
                words = line_text.split(' ')
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if self.font.size(test_line)[0] > max_width:
                        if current_line:
                            text_surface = self.font.render(current_line, True, color)
                            overlay.blit(text_surface, (10, line_y))
                            line_y += self.line_height
                        current_line = word
                    else:
                        current_line = test_line
                if current_line:
                    text_surface = self.font.render(current_line, True, color)
                    overlay.blit(text_surface, (10, line_y))
            else:
                text_surface = self.font.render(line_text, True, color)
                overlay.blit(text_surface, (10, line_y))

