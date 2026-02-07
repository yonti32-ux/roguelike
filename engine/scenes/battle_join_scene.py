"""
Battle join scene.

Shows a dialog when the player can join an ongoing battle between parties.
"""

import pygame
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from world.overworld.party_manager import BattleState
    from world.overworld.roaming_party import RoamingParty
    from engine.core.game import Game


class BattleJoinScene:
    """
    Scene for joining an ongoing battle.
    
    Allows player to choose which side to join.
    """
    
    def __init__(self, screen: pygame.Surface, battle: "BattleState", game: "Game"):
        self.screen = screen
        self.battle = battle
        self.game = game
        
        self.font_title = pygame.font.SysFont("consolas", 32)
        self.font_main = pygame.font.SysFont("consolas", 24)
        self.font_small = pygame.font.SysFont("consolas", 18)
        
        # Get party information
        if game.overworld_map and game.overworld_map.party_manager:
            self.party1 = game.overworld_map.party_manager.get_party(battle.party1_id)
            self.party2 = game.overworld_map.party_manager.get_party(battle.party2_id)
        else:
            self.party1 = None
            self.party2 = None
        
        self.selected_side = "party1"  # "party1" or "party2"
        self.closed = False
        self.result = None  # (side, party1, party2) if joined, None if cancelled
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events."""
        if event.type != pygame.KEYDOWN:
            return
        
        key = event.key
        
        # Toggle selection
        if key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            self.selected_side = "party2" if self.selected_side == "party1" else "party1"
            return
        
        # Join battle
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER, pygame.K_e):
            if self.party1 and self.party2:
                self.result = (self.selected_side, self.party1, self.party2)
                self.closed = True
            return
        
        # Cancel
        if key in (pygame.K_ESCAPE, pygame.K_x):
            self.closed = True
            return
    
    def draw(self) -> None:
        """Draw the battle join dialog."""
        screen = self.screen
        screen_w, screen_h = screen.get_size()
        
        # Semi-transparent background
        overlay = pygame.Surface((screen_w, screen_h))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Dialog box
        box_width = 600
        box_height = 400
        box_x = (screen_w - box_width) // 2
        box_y = (screen_h - box_height) // 2
        
        # Draw dialog box background
        pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (100, 100, 100), (box_x, box_y, box_width, box_height), 3)
        
        # Title
        title_text = "Battle in Progress!"
        title_surface = self.font_title.render(title_text, True, (255, 0, 0))
        title_rect = title_surface.get_rect(center=(box_x + box_width // 2, box_y + 40))
        screen.blit(title_surface, title_rect)
        
        # Description
        desc_text = "A battle is raging nearby. Which side will you join?"
        desc_surface = self.font_small.render(desc_text, True, (200, 200, 200))
        screen.blit(desc_surface, (box_x + 20, box_y + 80))
        
        # Party information
        from world.overworld.party_types import get_party_type
        
        y_offset = box_y + 120
        
        # Party 1
        if self.party1:
            party1_type = get_party_type(self.party1.party_type_id)
            party1_name = party1_type.name if party1_type else "Unknown"
            party1_health = f"Health: {self.battle.party1_health}%"
            
            # Highlight if selected
            if self.selected_side == "party1":
                pygame.draw.rect(screen, (60, 60, 100), 
                               (box_x + 20, y_offset - 5, box_width - 40, 80))
                color = (255, 255, 0)
            else:
                color = (200, 200, 200)
            
            party1_title = f"{'> ' if self.selected_side == 'party1' else '  '}Side 1: {party1_name}"
            title_surf = self.font_main.render(party1_title, True, color)
            screen.blit(title_surf, (box_x + 30, y_offset))
            
            health_surf = self.font_small.render(party1_health, True, color)
            screen.blit(health_surf, (box_x + 30, y_offset + 30))
            
            if self.party1.party_name:
                name_surf = self.font_small.render(f"({self.party1.party_name})", True, color)
                screen.blit(name_surf, (box_x + 30, y_offset + 50))
        
        y_offset += 100
        
        # Party 2
        if self.party2:
            party2_type = get_party_type(self.party2.party_type_id)
            party2_name = party2_type.name if party2_type else "Unknown"
            party2_health = f"Health: {self.battle.party2_health}%"
            
            # Highlight if selected
            if self.selected_side == "party2":
                pygame.draw.rect(screen, (60, 60, 100), 
                               (box_x + 20, y_offset - 5, box_width - 40, 80))
                color = (255, 255, 0)
            else:
                color = (200, 200, 200)
            
            party2_title = f"{'> ' if self.selected_side == 'party2' else '  '}Side 2: {party2_name}"
            title_surf = self.font_main.render(party2_title, True, color)
            screen.blit(title_surf, (box_x + 30, y_offset))
            
            health_surf = self.font_small.render(party2_health, True, color)
            screen.blit(health_surf, (box_x + 30, y_offset + 30))
            
            if self.party2.party_name:
                name_surf = self.font_small.render(f"({self.party2.party_name})", True, color)
                screen.blit(name_surf, (box_x + 30, y_offset + 50))
        
        # Instructions
        instructions = "LEFT/RIGHT: Choose side | ENTER: Join | ESC: Cancel"
        inst_surface = self.font_small.render(instructions, True, (150, 150, 150))
        inst_rect = inst_surface.get_rect(center=(box_x + box_width // 2, box_y + box_height - 30))
        screen.blit(inst_surface, inst_rect)
    
    def run(self) -> Optional[Tuple[str, "RoamingParty", "RoamingParty"]]:
        """
        Run the battle join scene.
        
        Returns:
            (side, party1, party2) if joined, None if cancelled
        """
        clock = pygame.time.Clock()
        
        # Draw the game state once as background
        if hasattr(self.game, "draw"):
            self.game.draw()
            background = self.screen.copy()
        else:
            background = None
        
        while not self.closed:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                
                self.handle_event(event)
            
            # Draw
            if background:
                self.screen.blit(background, (0, 0))
            else:
                if hasattr(self.game, "draw"):
                    self.game.draw()
            
            self.draw()
            
            pygame.display.flip()
            clock.tick(60)
        
        return self.result
