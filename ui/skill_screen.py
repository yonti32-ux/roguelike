"""
Full-screen skill allocation screen with visual skill tree.

Allows players to allocate skill points to upgrade unlocked skills for
the hero and companions. Features a visual tree layout with nodes and connections.
"""

from typing import Optional, List, TYPE_CHECKING, Dict, Tuple

import pygame
import math

from settings import COLOR_BG, FPS
from systems import skills as skill_system
from systems.skills import (
    get as get_skill,
    calculate_skill_power_at_rank,
    calculate_skill_cooldown_at_rank,
    calculate_skill_cost_at_rank,
    calculate_skill_status_duration_at_rank,
    calculate_skill_status_strength_at_rank,
    calculate_skill_dot_damage_at_rank,
    calculate_skill_aoe_radius_at_rank,
    get_skill_rank_cost,
    get_skill_rank_effects,
)
from systems.party import get_companion, CompanionState
from systems.classes import get_class
from ui.skill_tree_layout import (
    build_skill_tree,
    SkillTreeLayout,
    SkillNode,
    BRANCH_COLORS,
)

if TYPE_CHECKING:
    from engine.core.game import Game


def get_unlocked_skills_for_hero(game: "Game") -> List[str]:
    """
    Get all unlocked skill IDs for the hero.
    
    Skills are unlocked via:
    - Starting skills from class
    - Skills granted by perks
    
    Only returns skills available for the hero's class.
    """
    hero_stats = game.hero_stats
    class_id = hero_stats.hero_class_id
    unlocked: List[str] = []
    
    # Get starting skills from class
    from systems.classes import get_class
    from systems.skills import is_skill_available_for_class
    try:
        class_def = get_class(class_id)
        for skill_id in class_def.starting_skills:
            if skill_id and skill_id not in unlocked:
                try:
                    get_skill(skill_id)  # Verify exists
                    # Check if skill is available for this class
                    if is_skill_available_for_class(skill_id, class_id):
                        unlocked.append(skill_id)
                except KeyError:
                    pass
    except KeyError:
        pass
    
    # Get skills from perks
    from systems import perks as perk_system
    for perk_id in hero_stats.perks:
        try:
            perk = perk_system.get(perk_id)
            for skill_id in getattr(perk, "grant_skills", []):
                if skill_id and skill_id not in unlocked:
                    try:
                        get_skill(skill_id)  # Verify exists
                        # Check if skill is available for this class
                        if is_skill_available_for_class(skill_id, class_id):
                            unlocked.append(skill_id)
                    except KeyError:
                        pass
        except Exception:
            continue
    
    return unlocked


def get_unlocked_skills_for_companion(comp_state: CompanionState) -> List[str]:
    """
    Get all unlocked skill IDs for a companion.
    
    Skills are unlocked via:
    - Starting skills from template
    - Starting skills from companion's class
    - Skills granted by perks
    
    Only returns skills available for the companion's class.
    """
    unlocked: List[str] = []
    
    # Get companion's class
    companion_class_id = getattr(comp_state, "class_id", None)
    if not companion_class_id:
        # Try to get from template
        try:
            template = get_companion(comp_state.template_id)
            companion_class_id = getattr(template, "class_id", None)
        except KeyError:
            pass
    
    from systems.skills import is_skill_available_for_class
    
    # Get starting skills from template
    try:
        template = get_companion(comp_state.template_id)
        for skill_id in template.skill_ids:
            if skill_id and skill_id not in unlocked:
                try:
                    get_skill(skill_id)  # Verify exists
                    # Check class restriction if companion has a class
                    if companion_class_id:
                        if is_skill_available_for_class(skill_id, companion_class_id):
                            unlocked.append(skill_id)
                    else:
                        # No class restriction, allow all
                        unlocked.append(skill_id)
                except KeyError:
                    pass
    except KeyError:
        pass
    
    # Get starting skills from companion's class (if they have one)
    if companion_class_id:
        try:
            from systems.classes import get_class
            class_def = get_class(companion_class_id)
            for skill_id in class_def.starting_skills:
                if skill_id and skill_id not in unlocked:
                    try:
                        get_skill(skill_id)  # Verify exists
                        if is_skill_available_for_class(skill_id, companion_class_id):
                            unlocked.append(skill_id)
                    except KeyError:
                        pass
        except KeyError:
            pass
    
    # Get skills from perks
    from systems import perks as perk_system
    for perk_id in comp_state.perks:
        try:
            perk = perk_system.get(perk_id)
            for skill_id in getattr(perk, "grant_skills", []):
                if skill_id and skill_id not in unlocked:
                    try:
                        get_skill(skill_id)  # Verify exists
                        # Check class restriction if companion has a class
                        if companion_class_id:
                            if is_skill_available_for_class(skill_id, companion_class_id):
                                unlocked.append(skill_id)
                        else:
                            # No class restriction, allow all
                            unlocked.append(skill_id)
                    except KeyError:
                        pass
        except Exception:
            continue
    
    return unlocked


class SkillScreenCore:
    """
    Core skill allocation screen logic.
    
    Features:
    - Switch between hero and companions (Q/E keys)
    - List all unlocked skills with current ranks
    - Show skill details and upgrade preview
    - Allocate skill points to upgrade skills
    - Visual feedback for upgrades
    """
    
    def __init__(self, game: "Game") -> None:
        self.game = game
        self.font = game.ui_font
        self.font_title = pygame.font.SysFont("consolas", 28)
        self.font_small = pygame.font.SysFont("consolas", 16)
        
        # Current focus: 0 = hero, 1+ = companions
        self.focus_index: int = 0
        
        # Selected skill ID (for tree view)
        self.selected_skill_id: Optional[str] = None
        
        # Visual state
        self.cursor_visible: bool = True
        self.cursor_timer: float = 0.0
        
        # Tree view state
        self.tree_layout: Optional[SkillTreeLayout] = None
        self.camera_x: float = 0.0  # Panning offset
        self.camera_y: float = 0.0
        self.zoom: float = 1.0  # Zoom level
        
        # Node rendering constants
        self.NODE_SIZE = 80.0
        self.NODE_RADIUS = 35.0
        
        # Cached unlocked skills (refresh when focus changes)
        self._cached_unlocked_skills: Optional[List[str]] = None
        self._cached_focus_index: int = -1
    
    def get_focused_entity(self) -> Tuple[bool, Optional[CompanionState], Optional[str]]:
        """
        Get the currently focused entity (hero or companion).
        
        Returns:
            Tuple of (is_hero, companion_state, display_name)
        """
        party_list: List[CompanionState] = getattr(self.game, "party", None) or []
        total_slots = 1 + len(party_list)
        
        if total_slots <= 1:
            self.focus_index = 0
        
        if self.focus_index == 0:
            # Hero
            hero_name = getattr(self.game.hero_stats, "hero_name", "Hero")
            return True, None, hero_name
        else:
            # Companion
            comp_idx = self.focus_index - 1
            if 0 <= comp_idx < len(party_list):
                comp = party_list[comp_idx]
                if isinstance(comp, CompanionState):
                    display_name = getattr(comp, "name_override", None)
                    if not display_name:
                        try:
                            template = get_companion(comp.template_id)
                            display_name = template.name
                        except KeyError:
                            display_name = f"Companion {comp_idx + 1}"
                    return False, comp, display_name
        
        # Fallback
        return True, None, "Hero"
    
    def get_unlocked_skills(self) -> List[str]:
        """Get unlocked skills for the currently focused entity."""
        is_hero, comp, _ = self.get_focused_entity()
        
        # Cache results if focus hasn't changed
        if self._cached_focus_index == self.focus_index and self._cached_unlocked_skills is not None:
            return self._cached_unlocked_skills
        
        if is_hero:
            skills = get_unlocked_skills_for_hero(self.game)
        else:
            if comp is None:
                skills = []
            else:
                skills = get_unlocked_skills_for_companion(comp)
        
        self._cached_unlocked_skills = skills
        self._cached_focus_index = self.focus_index
        
        # Rebuild tree layout
        if skills:
            self.tree_layout = build_skill_tree(skills)
            from ui.skill_tree_layout import layout_tree
            layout_tree(self.tree_layout, node_size=self.NODE_SIZE)
            
            # Update node ranks
            for skill_id in skills:
                if skill_id in self.tree_layout.nodes:
                    self.tree_layout.nodes[skill_id].rank = self.get_skill_rank(skill_id)
        else:
            self.tree_layout = None
        
        # Reset selected skill if not in unlocked list
        if self.selected_skill_id not in skills:
            self.selected_skill_id = skills[0] if skills else None
        
        return skills
    
    def get_skill_points(self) -> int:
        """Get available skill points for the focused entity."""
        is_hero, comp, _ = self.get_focused_entity()
        
        if is_hero:
            return getattr(self.game.hero_stats, "skill_points", 0)
        else:
            if comp is None:
                return 0
            return getattr(comp, "skill_points", 0)
    
    def get_skill_rank(self, skill_id: str) -> int:
        """Get current rank of a skill for the focused entity."""
        is_hero, comp, _ = self.get_focused_entity()
        
        if is_hero:
            ranks = getattr(self.game.hero_stats, "skill_ranks", {})
        else:
            if comp is None:
                return 0
            ranks = getattr(comp, "skill_ranks", {})
        
        return ranks.get(skill_id, 0)
    
    def can_upgrade_skill(self, skill_id: str) -> bool:
        """Check if a skill can be upgraded."""
        is_hero, comp, _ = self.get_focused_entity()
        
        if is_hero:
            return self.game.hero_stats.can_upgrade_skill(skill_id)
        else:
            if comp is None:
                return False
            return comp.can_upgrade_skill(skill_id)
    
    def upgrade_skill(self, skill_id: str) -> bool:
        """Upgrade a skill for the focused entity."""
        is_hero, comp, _ = self.get_focused_entity()
        
        if is_hero:
            success = self.game.hero_stats.upgrade_skill(skill_id)
            if success:
                # Sync stats to player entity
                if self.game.player is not None:
                    self.game.apply_hero_stats_to_player(full_heal=False)
            return success
        else:
            if comp is None:
                return False
            success = comp.upgrade_skill(skill_id)
            if success:
                # Recalculate companion stats
                try:
                    template = get_companion(comp.template_id)
                    from systems.party import recalc_companion_stats_for_level
                    recalc_companion_stats_for_level(comp, template)
                except Exception:
                    pass
            return success
    
    def update(self, dt: float) -> None:
        """Update visual state (cursor blink, etc.). Called from game loop."""
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible
    
    def reset_selection(self) -> None:
        """Reset selection when opening screen."""
        self.selected_skill_id = None
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.zoom = 1.0
    
    def world_to_screen(self, wx: float, wy: float, screen_w: int, screen_h: int) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        sx = int(screen_w / 2 + (wx + self.camera_x) * self.zoom)
        sy = int(screen_h / 2 + (wy + self.camera_y) * self.zoom)
        return sx, sy
    
    def screen_to_world(self, sx: int, sy: int, screen_w: int, screen_h: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        wx = (sx - screen_w / 2) / self.zoom - self.camera_x
        wy = (sy - screen_h / 2) / self.zoom - self.camera_y
        return wx, wy
    
    def get_node_at_screen_pos(self, sx: int, sy: int, screen_w: int, screen_h: int) -> Optional[str]:
        """Get skill ID of node at screen position, or None."""
        if not self.tree_layout:
            return None
        
        wx, wy = self.screen_to_world(sx, sy, screen_w, screen_h)
        
        for skill_id, node in self.tree_layout.nodes.items():
            dx = wx - node.x
            dy = wy - node.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= self.NODE_RADIUS:
                return skill_id
        
        return None
    
    def draw_content(self, screen: pygame.Surface, w: int, h: int) -> None:
        """Draw the skill allocation interface content (without header/footer)."""
        # Get focused entity info
        is_hero, comp, display_name = self.get_focused_entity()
        skill_points = self.get_skill_points()
        
        # Character name and skill points
        char_text = self.font.render(f"Character: {display_name}", True, (220, 220, 200))
        screen.blit(char_text, (40, 80))
        
        points_text = self.font.render(f"Available Skill Points: {skill_points}", True, (230, 210, 120))
        screen.blit(points_text, (40, 110))
        
        # Get unlocked skills and tree layout
        unlocked_skills = self.get_unlocked_skills()
        
        if not unlocked_skills or not self.tree_layout:
            # No skills unlocked
            no_skills = self.font.render("No skills unlocked yet.", True, (180, 180, 180))
            screen.blit(no_skills, (w // 2 - no_skills.get_width() // 2, h // 2))
            
            hint = self.font_small.render("Skills are unlocked via perks or starting class.", True, (150, 150, 150))
            screen.blit(hint, (w // 2 - hint.get_width() // 2, h // 2 + 30))
        else:
            # Auto-select first skill if none selected
            if not self.selected_skill_id and unlocked_skills:
                self.selected_skill_id = unlocked_skills[0]
            
            # Update node ranks in tree layout
            for skill_id in unlocked_skills:
                if skill_id in self.tree_layout.nodes:
                    self.tree_layout.nodes[skill_id].rank = self.get_skill_rank(skill_id)
            
            # Draw visual skill tree
            self._draw_skill_tree(screen, w, h, skill_points)
            
            # Draw skill details panel on the right
            if self.selected_skill_id:
                self._draw_skill_details(screen, w, h, self.selected_skill_id, skill_points)
    
    def _draw_skill_tree(self, screen: pygame.Surface, w: int, h: int, skill_points: int) -> None:
        """Draw the visual skill tree."""
        if not self.tree_layout:
            return
        
        # Draw branch labels at the top
        branch_positions: Dict[str, float] = {}
        for branch_name, skill_ids in self.tree_layout.branches.items():
            if skill_ids:
                # Find average X position of skills in this branch
                x_positions = [self.tree_layout.nodes[sid].x for sid in skill_ids if sid in self.tree_layout.nodes]
                if x_positions:
                    avg_x = sum(x_positions) / len(x_positions)
                    branch_positions[branch_name] = avg_x
        
        # Draw branch labels
        for branch_name, avg_x in branch_positions.items():
            sx, sy = self.world_to_screen(avg_x, -250, w, h)  # Above the tree
            if 0 <= sx <= w:
                branch_color = BRANCH_COLORS.get(branch_name, (180, 180, 180))
                branch_label = self.font_small.render(branch_name.upper(), True, branch_color)
                screen.blit(branch_label, (sx - branch_label.get_width() // 2, sy))
        
        # Draw connections first (behind nodes)
        for from_id, to_id in self.tree_layout.connections:
            if from_id in self.tree_layout.nodes and to_id in self.tree_layout.nodes:
                from_node = self.tree_layout.nodes[from_id]
                to_node = self.tree_layout.nodes[to_id]
                
                sx1, sy1 = self.world_to_screen(from_node.x, from_node.y, w, h)
                sx2, sy2 = self.world_to_screen(to_node.x, to_node.y, w, h)
                
                # Only draw if both nodes are on screen
                if (0 <= sx1 <= w and 0 <= sy1 <= h) or (0 <= sx2 <= w and 0 <= sy2 <= h):
                    pygame.draw.line(screen, (100, 100, 100), (sx1, sy1), (sx2, sy2), 2)
        
        # Draw nodes
        for skill_id, node in self.tree_layout.nodes.items():
            sx, sy = self.world_to_screen(node.x, node.y, w, h)
            
            # Skip if off-screen
            if sx < -self.NODE_RADIUS or sx > w + self.NODE_RADIUS:
                continue
            if sy < -self.NODE_RADIUS or sy > h + self.NODE_RADIUS:
                continue
            
            # Get branch color
            branch_color = BRANCH_COLORS.get(node.branch, (180, 180, 180))
            
            # Determine node state
            is_selected = (skill_id == self.selected_skill_id)
            can_upgrade = self.can_upgrade_skill(skill_id)
            is_maxed = node.rank >= node.skill.max_rank
            
            # Node border color
            if is_selected:
                border_color = (255, 255, 100)
                border_width = 3
            elif can_upgrade:
                border_color = (200, 255, 200)
                border_width = 2
            elif is_maxed:
                border_color = (200, 200, 255)
                border_width = 2
            else:
                border_color = (150, 150, 150)
                border_width = 1
            
            # Draw node circle
            radius = int(self.NODE_RADIUS * self.zoom)
            pygame.draw.circle(screen, branch_color, (sx, sy), radius)
            pygame.draw.circle(screen, border_color, (sx, sy), radius, border_width)
            
            # Draw rank indicator (smaller circle inside)
            if node.rank > 0:
                rank_radius = int(radius * 0.6)
                rank_color = (255, 255, 200) if node.rank >= node.skill.max_rank else (200, 200, 255)
                pygame.draw.circle(screen, rank_color, (sx, sy), rank_radius)
                
                # Draw rank number
                rank_text = self.font_small.render(str(node.rank), True, (0, 0, 0))
                screen.blit(rank_text, (sx - rank_text.get_width() // 2, sy - rank_text.get_height() // 2))
            
            # Draw skill name below node
            name_surf = self.font_small.render(node.skill.name[:12], True, (220, 220, 220))
            screen.blit(name_surf, (sx - name_surf.get_width() // 2, sy + radius + 5))
    
    def _draw_skill_details(self, screen: pygame.Surface, w: int, h: int, skill_id: str, skill_points: int) -> None:
        """Draw skill details panel."""
        try:
            skill = get_skill(skill_id)
            rank = self.get_skill_rank(skill_id)
            next_rank = rank + 1
            
            # Details panel on the right
            detail_x = w - 350
            detail_y = 160
            
            # Panel background
            panel_rect = pygame.Rect(detail_x - 10, detail_y - 10, 340, h - detail_y - 20)
            pygame.draw.rect(screen, (30, 30, 35), panel_rect)
            pygame.draw.rect(screen, (80, 80, 90), panel_rect, 2)
            
            detail_title = self.font.render("Skill Details:", True, (220, 220, 180))
            screen.blit(detail_title, (detail_x, detail_y))
            detail_y += 30
            
            # Name
            name_surf = self.font.render(skill.name, True, (240, 240, 220))
            screen.blit(name_surf, (detail_x, detail_y))
            detail_y += 28
            
            # Description
            desc_lines = []
            desc = skill.description
            words = desc.split()
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surf = self.font_small.render(test_line, True, (200, 200, 200))
                if test_surf.get_width() > 320:
                    if current_line:
                        desc_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                desc_lines.append(current_line)
            
            for line in desc_lines:
                desc_surf = self.font_small.render(line, True, (200, 200, 200))
                screen.blit(desc_surf, (detail_x, detail_y))
                detail_y += 20
            
            detail_y += 10
            
            # Current stats
            current_power = calculate_skill_power_at_rank(skill.base_power, rank, skill_id)
            current_cooldown = calculate_skill_cooldown_at_rank(skill.cooldown, rank, skill_id)
            current_stamina = calculate_skill_cost_at_rank(skill.stamina_cost, rank, skill_id)
            current_mana = calculate_skill_cost_at_rank(skill.mana_cost, rank, skill_id)
            current_aoe_radius = calculate_skill_aoe_radius_at_rank(skill.aoe_radius, rank, skill_id)
            
            # Get status effect info if applicable
            status_duration = None
            status_strength = None
            dot_damage = None
            if skill.make_target_status:
                try:
                    sample_status = skill.make_target_status()
                    status_duration = calculate_skill_status_duration_at_rank(sample_status.duration, rank, skill_id)
                    if sample_status.outgoing_mult != 1.0:
                        status_strength = calculate_skill_status_strength_at_rank(sample_status.outgoing_mult, rank, skill_id)
                    elif sample_status.incoming_mult != 1.0:
                        status_strength = calculate_skill_status_strength_at_rank(sample_status.incoming_mult, rank, skill_id)
                    if sample_status.flat_damage_each_turn > 0:
                        dot_damage = calculate_skill_dot_damage_at_rank(sample_status.flat_damage_each_turn, rank, skill_id)
                except:
                    pass
            elif skill.make_self_status:
                try:
                    sample_status = skill.make_self_status()
                    status_duration = calculate_skill_status_duration_at_rank(sample_status.duration, rank, skill_id)
                    if sample_status.outgoing_mult != 1.0:
                        status_strength = calculate_skill_status_strength_at_rank(sample_status.outgoing_mult, rank, skill_id)
                    elif sample_status.incoming_mult != 1.0:
                        status_strength = calculate_skill_status_strength_at_rank(sample_status.incoming_mult, rank, skill_id)
                    if sample_status.flat_damage_each_turn > 0:
                        dot_damage = calculate_skill_dot_damage_at_rank(sample_status.flat_damage_each_turn, rank, skill_id)
                except:
                    pass
            
            stats_title = self.font_small.render("Current Stats:", True, (190, 190, 190))
            screen.blit(stats_title, (detail_x, detail_y))
            detail_y += 22
            
            stats_lines = []
            if skill.base_power > 0:
                stats_lines.append(f"Power: {current_power:.2f}x")
            if current_cooldown > 0:
                stats_lines.append(f"Cooldown: {current_cooldown} turns")
            if current_stamina > 0:
                stats_lines.append(f"Stamina Cost: {current_stamina}")
            if current_mana > 0:
                stats_lines.append(f"Mana Cost: {current_mana}")
            if current_aoe_radius > 0:
                stats_lines.append(f"AoE Radius: {current_aoe_radius}")
            if status_duration is not None:
                stats_lines.append(f"Status Duration: {status_duration} turns")
            if status_strength is not None:
                if status_strength < 1.0:
                    stats_lines.append(f"Damage Reduction: {int((1.0 - status_strength) * 100)}%")
                elif status_strength > 1.0:
                    stats_lines.append(f"Damage Multiplier: {status_strength:.2f}x")
            if dot_damage is not None and dot_damage > 0:
                stats_lines.append(f"DoT Damage: {dot_damage} per turn")
            
            for stat_line in stats_lines:
                stat_surf = self.font_small.render(stat_line, True, (180, 180, 180))
                screen.blit(stat_surf, (detail_x + 20, detail_y))
                detail_y += 20
            
            # Next rank preview
            if rank < skill.max_rank:
                detail_y += 10
                cost = get_skill_rank_cost(next_rank)
                can_afford = skill_points >= cost
                
                next_power = calculate_skill_power_at_rank(skill.base_power, next_rank, skill_id)
                next_cooldown = calculate_skill_cooldown_at_rank(skill.cooldown, next_rank, skill_id)
                next_stamina = calculate_skill_cost_at_rank(skill.stamina_cost, next_rank, skill_id)
                next_mana = calculate_skill_cost_at_rank(skill.mana_cost, next_rank, skill_id)
                next_aoe_radius = calculate_skill_aoe_radius_at_rank(skill.aoe_radius, next_rank, skill_id)
                
                # Get next rank status effect info
                next_status_duration = None
                next_status_strength = None
                next_dot_damage = None
                if skill.make_target_status:
                    try:
                        sample_status = skill.make_target_status()
                        next_status_duration = calculate_skill_status_duration_at_rank(sample_status.duration, next_rank, skill_id)
                        if sample_status.outgoing_mult != 1.0:
                            next_status_strength = calculate_skill_status_strength_at_rank(sample_status.outgoing_mult, next_rank, skill_id)
                        elif sample_status.incoming_mult != 1.0:
                            next_status_strength = calculate_skill_status_strength_at_rank(sample_status.incoming_mult, next_rank, skill_id)
                        if sample_status.flat_damage_each_turn > 0:
                            next_dot_damage = calculate_skill_dot_damage_at_rank(sample_status.flat_damage_each_turn, next_rank, skill_id)
                    except:
                        pass
                elif skill.make_self_status:
                    try:
                        sample_status = skill.make_self_status()
                        next_status_duration = calculate_skill_status_duration_at_rank(sample_status.duration, next_rank, skill_id)
                        if sample_status.outgoing_mult != 1.0:
                            next_status_strength = calculate_skill_status_strength_at_rank(sample_status.outgoing_mult, next_rank, skill_id)
                        elif sample_status.incoming_mult != 1.0:
                            next_status_strength = calculate_skill_status_strength_at_rank(sample_status.incoming_mult, next_rank, skill_id)
                        if sample_status.flat_damage_each_turn > 0:
                            next_dot_damage = calculate_skill_dot_damage_at_rank(sample_status.flat_damage_each_turn, next_rank, skill_id)
                    except:
                        pass
                
                preview_title = self.font_small.render(f"Next Rank ({next_rank}):", True, (200, 200, 180))
                screen.blit(preview_title, (detail_x, detail_y))
                detail_y += 22
                
                preview_lines = []
                if skill.base_power > 0:
                    power_change = next_power - current_power
                    preview_lines.append(f"Power: {next_power:.2f}x ({'+' if power_change >= 0 else ''}{power_change:.2f})")
                if next_cooldown != current_cooldown:
                    preview_lines.append(f"Cooldown: {next_cooldown} turns ({current_cooldown - next_cooldown:+d})")
                if next_stamina != current_stamina:
                    preview_lines.append(f"Stamina Cost: {next_stamina} ({current_stamina - next_stamina:+d})")
                if next_mana != current_mana:
                    preview_lines.append(f"Mana Cost: {next_mana} ({current_mana - next_mana:+d})")
                if next_aoe_radius != current_aoe_radius:
                    preview_lines.append(f"AoE Radius: {next_aoe_radius} ({next_aoe_radius - current_aoe_radius:+d})")
                if next_status_duration is not None and next_status_duration != status_duration:
                    preview_lines.append(f"Status Duration: {next_status_duration} turns ({next_status_duration - status_duration:+d})")
                if next_status_strength is not None and next_status_strength != status_strength:
                    if next_status_strength < 1.0:
                        current_reduction = int((1.0 - status_strength) * 100) if status_strength else 0
                        next_reduction = int((1.0 - next_status_strength) * 100)
                        preview_lines.append(f"Damage Reduction: {next_reduction}% ({next_reduction - current_reduction:+d}%)")
                    elif next_status_strength > 1.0:
                        preview_lines.append(f"Damage Multiplier: {next_status_strength:.2f}x ({next_status_strength - status_strength:+.2f})")
                if next_dot_damage is not None and next_dot_damage != dot_damage:
                    preview_lines.append(f"DoT Damage: {next_dot_damage} per turn ({next_dot_damage - dot_damage:+d})")
                
                for preview_line in preview_lines:
                    preview_surf = self.font_small.render(preview_line, True, (180, 220, 180))
                    screen.blit(preview_surf, (detail_x + 20, detail_y))
                    detail_y += 20
                
                # Upgrade button hint
                detail_y += 10
                if can_afford:
                    upgrade_hint = self.font_small.render(f"Cost: {cost} skill points | Press Enter/Space to upgrade", True, (200, 255, 200))
                else:
                    upgrade_hint = self.font_small.render(f"Cost: {cost} skill points | Not enough points", True, (200, 150, 150))
                screen.blit(upgrade_hint, (detail_x, detail_y))
            else:
                detail_y += 10
                maxed_hint = self.font_small.render("Skill is at maximum rank!", True, (200, 200, 200))
                screen.blit(maxed_hint, (detail_x, detail_y))
        except KeyError:
            pass

