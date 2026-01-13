"""
Party interaction scene.

Shows a dialog screen when the player interacts with a roaming party.
"""

import pygame
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from world.overworld.roaming_party import RoamingParty
    from world.overworld.party_types import PartyType
    from engine.core.game import Game


class PartyInteractionScene:
    """
    Scene for interacting with roaming parties.
    
    Shows party information and available actions (trade, talk, attack, etc.)
    """
    
    def __init__(self, screen: pygame.Surface, party: "RoamingParty", party_type: "PartyType", game: "Game"):
        self.screen = screen
        self.party = party
        self.party_type = party_type
        self.game = game
        
        self.font_title = pygame.font.SysFont("consolas", 32)
        self.font_main = pygame.font.SysFont("consolas", 24)
        self.font_small = pygame.font.SysFont("consolas", 18)
        
        # Available actions
        self.actions = []
        self._build_actions()
        
        self.selected_action_index = 0
        self.closed = False
    
    def _build_actions(self) -> None:
        """Build list of available actions based on party type."""
        self.actions = []
        
        # Talk (always available)
        self.actions.append(("Talk", "talk", self._action_talk))
        
        # Trade (if party can trade)
        if self.party_type.can_trade:
            self.actions.append(("Trade", "trade", self._action_trade))
        
        # Recruit (if party can recruit)
        if self.party_type.can_recruit:
            self.actions.append(("Recruit", "recruit", self._action_recruit))
        
        # Quest (if party gives quests)
        if self.party_type.gives_quests:
            self.actions.append(("Quest", "quest", self._action_quest))
        
        # Attack (if party can be attacked and is hostile)
        if self.party_type.can_be_attacked and self.party_type.alignment.value == "hostile":
            self.actions.append(("Attack", "attack", self._action_attack))
        
        # Leave (always available)
        self.actions.append(("Leave", "leave", self._action_leave))
    
    def _action_talk(self) -> None:
        """Talk to the party."""
        # Generate a random greeting based on party type
        greetings = {
            "merchant": [
                "Greetings, traveler! I have fine wares for sale.",
                "Welcome! Care to browse my goods?",
                "Good day! I'm always looking for customers.",
            ],
            "villager": [
                "Hello there! Safe travels!",
                "Good day, stranger. Where are you headed?",
                "Nice to meet you! The roads can be dangerous.",
            ],
            "guard": [
                "Halt! State your business.",
                "Good day, citizen. All is well on the roads.",
                "Stay safe out there, traveler.",
            ],
            "adventurer": [
                "Greetings, fellow adventurer!",
                "Well met! Are you on a quest?",
                "Good to see another explorer!",
            ],
            "bandit": [
                "Well, well... what do we have here?",
                "Hand over your gold, and no one gets hurt!",
                "This is a robbery! Give me everything!",
            ],
            "monster": [
                "*Growls menacingly*",
                "*Snarls and bares teeth*",
            ],
        }
        
        party_greetings = greetings.get(self.party_type.id, ["Hello."])
        import random
        greeting = random.choice(party_greetings)
        self.game.add_message(f"{self.party_type.name}: {greeting}")
        self.closed = True
    
    def _action_trade(self) -> None:
        """Open trade interface."""
        # TODO: Implement trade interface
        self.game.add_message(f"You begin trading with {self.party_type.name}.")
        # For now, just close
        self.closed = True
    
    def _action_recruit(self) -> None:
        """Attempt to recruit from party."""
        # TODO: Implement recruitment
        self.game.add_message(f"You attempt to recruit from {self.party_type.name}.")
        self.closed = True
    
    def _action_quest(self) -> None:
        """Check for quests."""
        # TODO: Implement quest system
        self.game.add_message(f"{self.party_type.name} may have quests for you.")
        self.closed = True
    
    def _action_attack(self) -> None:
        """Attack the party and trigger combat."""
        try:
            from world.overworld.battle_conversion import party_to_battle_enemies
            
            # Convert party to enemies
            player_level = 1
            if self.game.player:
                if hasattr(self.game.player, 'level'):
                    player_level = self.game.player.level
                elif hasattr(self.game, 'hero_stats') and self.game.hero_stats:
                    player_level = getattr(self.game.hero_stats, 'level', 1)
            
            enemies = party_to_battle_enemies(
                party=self.party,
                party_type=self.party_type,
                game=self.game,
                player_level=player_level
            )
            
            if not enemies:
                self.game.add_message("Unable to engage in combat.")
                self.closed = True
                return
            
            # Close interaction screen
            self.closed = True
            
            # Trigger battle
            self.game.start_battle_from_overworld(enemies, context_party=self.party)
        except Exception as e:
            # Log error and show message to player
            import traceback
            print(f"Error starting battle: {e}")
            traceback.print_exc()
            self.game.add_message(f"Error: Unable to start combat. {str(e)}")
            self.closed = True
    
    def _action_leave(self) -> None:
        """Leave the interaction."""
        self.closed = True
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle input events."""
        if event.type != pygame.KEYDOWN:
            return
        
        key = event.key
        
        # Navigation
        if key in (pygame.K_UP, pygame.K_w):
            if self.selected_action_index > 0:
                self.selected_action_index -= 1
            return
        
        if key in (pygame.K_DOWN, pygame.K_s):
            if self.selected_action_index < len(self.actions) - 1:
                self.selected_action_index += 1
            return
        
        # Selection
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER, pygame.K_e):
            if self.actions:
                action_name, action_id, action_func = self.actions[self.selected_action_index]
                action_func()
            return
        
        # Cancel
        if key in (pygame.K_ESCAPE, pygame.K_x):
            self._action_leave()
            return
    
    def draw(self) -> None:
        """Draw the interaction screen."""
        screen = self.screen
        screen_w, screen_h = screen.get_size()
        
        # Semi-transparent background
        overlay = pygame.Surface((screen_w, screen_h))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Calculate dialog box size dynamically based on content
        # Base height for title, description, and info
        base_height = 200
        # Height per action (with spacing)
        action_height = 35
        actions_height = len(self.actions) * action_height + 40  # +40 for "Actions:" title and spacing
        # Instructions height
        instructions_height = 40
        
        # Calculate total height needed
        box_width = 650  # Slightly wider for better readability
        box_height = base_height + actions_height + instructions_height
        
        # Ensure minimum size and cap at screen size
        box_height = max(400, min(box_height, screen_h - 40))
        box_width = min(box_width, screen_w - 40)
        
        box_x = (screen_w - box_width) // 2
        box_y = (screen_h - box_height) // 2
        
        # Draw dialog box background
        pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (100, 100, 100), (box_x, box_y, box_width, box_height), 3)
        
        # Title
        title_text = self.party_type.name
        title_surface = self.font_title.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(box_x + box_width // 2, box_y + 40))
        screen.blit(title_surface, title_rect)
        
        # Alignment indicator
        alignment_colors = {
            "friendly": (0, 255, 0),
            "neutral": (255, 255, 0),
            "hostile": (255, 0, 0),
        }
        alignment_color = alignment_colors.get(self.party_type.alignment.value, (255, 255, 255))
        alignment_text = f"Alignment: {self.party_type.alignment.value.title()}"
        alignment_surface = self.font_small.render(alignment_text, True, alignment_color)
        screen.blit(alignment_surface, (box_x + 20, box_y + 70))
        
        # Description
        desc_lines = self._wrap_text(self.party_type.description, box_width - 40, self.font_small)
        y_offset = box_y + 100
        for line in desc_lines:
            desc_surface = self.font_small.render(line, True, (200, 200, 200))
            screen.blit(desc_surface, (box_x + 20, y_offset))
            y_offset += 25
        
        # Party info
        info_y = y_offset + 20
        info_lines = [
            f"Behavior: {self.party_type.behavior.value.title()}",
        ]
        
        if self.party.gold > 0:
            info_lines.append(f"Gold: {self.party.gold}")
        
        if self.party_type.combat_strength > 0:
            info_lines.append(f"Combat Strength: {self.party_type.combat_strength}/5")
        
        for line in info_lines:
            info_surface = self.font_small.render(line, True, (180, 180, 180))
            screen.blit(info_surface, (box_x + 20, info_y))
            info_y += 20
        
        # Actions list
        actions_start_y = info_y + 30
        actions_title = self.font_main.render("Actions:", True, (255, 255, 255))
        screen.blit(actions_title, (box_x + 20, actions_start_y))
        
        action_y = actions_start_y + 35
        action_height = 35
        instructions_height = 40
        
        # Draw all actions (box is now dynamically sized to fit them)
        for i, (action_name, action_id, _) in enumerate(self.actions):
            # Check if this action would go past the instructions area
            if action_y + action_height > box_y + box_height - instructions_height - 10:
                # This shouldn't happen with dynamic sizing, but just in case
                break
                
            # Highlight selected action
            if i == self.selected_action_index:
                # Draw selection background
                pygame.draw.rect(screen, (60, 60, 100), 
                               (box_x + 15, action_y - 2, box_width - 30, 30))
                color = (255, 255, 0)
            else:
                color = (200, 200, 200)
            
            # Draw action text
            action_text = f"> {action_name}" if i == self.selected_action_index else f"  {action_name}"
            action_surface = self.font_main.render(action_text, True, color)
            screen.blit(action_surface, (box_x + 30, action_y))
            action_y += action_height
        
        # Instructions
        instructions = "UP/DOWN: Navigate | ENTER: Select | ESC: Leave"
        inst_surface = self.font_small.render(instructions, True, (150, 150, 150))
        inst_rect = inst_surface.get_rect(center=(box_x + box_width // 2, box_y + box_height - 30))
        screen.blit(inst_surface, inst_rect)
    
    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = font.render(word + " ", True, (255, 255, 255))
            word_width = word_surface.get_width()
            
            if current_width + word_width > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    def run(self) -> Optional[str]:
        """
        Run the interaction scene.
        
        Returns:
            Action ID that was selected, or None if closed without action
        """
        clock = pygame.time.Clock()
        
        # Draw the game state once as background (cache it)
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
            # Restore the cached background instead of redrawing every frame
            if background:
                self.screen.blit(background, (0, 0))
            else:
                # Fallback: draw game state if no background cached
                if hasattr(self.game, "draw"):
                    self.game.draw()
            
            # Then draw the interaction screen overlay
            self.draw()
            
            pygame.display.flip()
            clock.tick(60)
        
        # Return the selected action if one was chosen
        if self.actions and self.selected_action_index < len(self.actions):
            return self.actions[self.selected_action_index][1]
        return None

