"""
Quest screen module for viewing and accepting quests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

import pygame

from ui.screen_components import draw_screen_header, draw_screen_footer
from ui.screen_utils import safe_getattr

if TYPE_CHECKING:
    from engine.core.game import Game


def _wrap_text(text: str, font, max_width: int) -> List[str]:
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_surf = font.render(word + " ", True, (255, 255, 255))
        word_width = word_surf.get_width()
        
        if current_width + word_width > max_width and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width
        else:
            current_line.append(word)
            current_width += word_width
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines if lines else [text]


def draw_quest_fullscreen(game: "Game") -> None:
    """Full-screen quest view for viewing and accepting quests."""
    screen = game.screen
    ui_font = game.ui_font
    w, h = screen.get_size()
    
    # Draw gradient background
    from ui.screen_components import draw_gradient_background
    from ui.screen_constants import COLOR_GRADIENT_START, COLOR_GRADIENT_END
    draw_gradient_background(
        screen,
        0, 0, w, h,
        COLOR_GRADIENT_START,
        COLOR_GRADIENT_END,
        vertical=True
    )
    
    # Get available screens for tabs (keep consistent across screens)
    available_screens = ["inventory", "character", "skills", "quests"]
    if safe_getattr(game, "show_shop", False):
        available_screens.append("shop")
    if safe_getattr(game, "show_recruitment", False):
        available_screens.append("recruitment")
    
    # Draw header with tabs
    draw_screen_header(screen, ui_font, "Quests", "quests", available_screens, w)
    
    # Get elder ID and quests - if elder_id is None, show all quests
    elder_id = getattr(game, "current_elder_id", None)
    
    from systems.quests import Quest, QuestStatus
    
    available_quests: list[Quest] = [
        q for q in getattr(game, "available_quests", {}).values()
        if q.status == QuestStatus.AVAILABLE and (elder_id is None or q.quest_giver_id == elder_id)
    ]
    
    active_quests: list[Quest] = [
        q for q in getattr(game, "active_quests", {}).values()
        if q.status == QuestStatus.ACTIVE and (elder_id is None or q.quest_giver_id == elder_id)
    ]
    
    completed_quests: list[Quest] = [
        q for q in getattr(game, "active_quests", {}).values()
        if q.status == QuestStatus.COMPLETED and (elder_id is None or q.quest_giver_id == elder_id)
    ]
    
    # Determine which tab we're on
    quest_tab = getattr(game, "quest_tab", "available")
    
    # Tab selection UI
    tab_y = 70
    tab_x = 40
    tab_width = 150
    tabs = [
        ("available", f"Available ({len(available_quests)})"),
        ("active", f"Active ({len(active_quests)})"),
        ("completed", f"Completed ({len(completed_quests)})"),
    ]
    
    for tab_name, tab_label in tabs:
        tab_color = (220, 220, 180) if quest_tab == tab_name else (160, 160, 160)
        tab_surf = ui_font.render(tab_label, True, tab_color)
        screen.blit(tab_surf, (tab_x, tab_y))
        tab_x += tab_width
    
    # Get active list based on tab
    if quest_tab == "available":
        active_list = available_quests
        action_text = "Accept"
    elif quest_tab == "active":
        active_list = active_quests
        action_text = "View"
    elif quest_tab == "completed":
        active_list = completed_quests
        action_text = "Turn In"
    else:
        active_list = available_quests
        action_text = "Accept"
    
    # Left column: Quest list
    left_x = 40
    y = 110
    
    title = ui_font.render(f"{quest_tab.title()} Quests:", True, (220, 220, 180))
    screen.blit(title, (left_x, y))
    y += 28
    
    cursor = int(getattr(game, "quest_cursor", 0))
    
    if not active_list:
        msg = ui_font.render(f"No {quest_tab} quests.", True, (190, 190, 190))
        screen.blit(msg, (left_x, y))
    else:
        max_quests = len(active_list)
        line_height = 32
        if max_quests > 0:
            cursor = max(0, min(cursor, max_quests - 1))
        
        # Show quests with scrolling
        visible_start = max(0, cursor - 8)
        visible_end = min(max_quests, cursor + 10)
        visible_quests = active_list[visible_start:visible_end]
        
        for i, quest in enumerate(visible_quests):
            actual_index = visible_start + i
            
            if actual_index == cursor:
                # Highlight selected quest
                bg = pygame.Surface((w // 2 - 80, line_height), pygame.SRCALPHA)
                bg.fill((60, 60, 90, 210))
                screen.blit(bg, (left_x, y - 2))
                label_color = (255, 255, 200)
            else:
                label_color = (230, 230, 230)
            
            # Quest title
            label = f"{actual_index + 1}) {quest.title}"
            label_surf = ui_font.render(label, True, label_color)
            screen.blit(label_surf, (left_x + 20, y))
            y += line_height
    
    # Right column: Quest details
    if 0 <= cursor < len(active_list):
        info_x = w // 2 + 40
        info_y = 110
        
        selected_quest = active_list[cursor]
        
        info_title = ui_font.render("Quest Details:", True, (220, 220, 180))
        screen.blit(info_title, (info_x, info_y))
        info_y += 26
        
        # Title
        title_surf = ui_font.render(selected_quest.title, True, (235, 235, 220))
        screen.blit(title_surf, (info_x, info_y))
        info_y += 28
        
        # Description
        desc_lines = _wrap_text(selected_quest.description, ui_font, w // 2 - 80)
        for line in desc_lines:
            desc_surf = ui_font.render(line, True, (200, 200, 200))
            screen.blit(desc_surf, (info_x, info_y))
            info_y += 22
        
        info_y += 10
        
        # Objectives
        obj_title = ui_font.render("Objectives:", True, (220, 220, 180))
        screen.blit(obj_title, (info_x, info_y))
        info_y += 24
        
        for obj in selected_quest.objectives:
            progress_str = f"{obj.current_count}/{obj.target_count}"
            if obj.is_complete():
                obj_color = (150, 255, 150)  # Green for complete
                status = "✓"
            else:
                obj_color = (200, 200, 200)
                status = "○"
            
            obj_line = f"  {status} {obj.description} ({progress_str})"
            obj_surf = ui_font.render(obj_line, True, obj_color)
            screen.blit(obj_surf, (info_x, info_y))
            info_y += 22
        
        info_y += 10
        
        # Rewards
        reward_title = ui_font.render("Rewards:", True, (220, 220, 180))
        screen.blit(reward_title, (info_x, info_y))
        info_y += 24
        
        rewards = []
        if selected_quest.rewards.gold > 0:
            rewards.append(f"Gold: {selected_quest.rewards.gold}")
        if selected_quest.rewards.xp > 0:
            rewards.append(f"XP: {selected_quest.rewards.xp}")
        if selected_quest.rewards.items:
            for item_id in selected_quest.rewards.items:
                try:
                    from systems.inventory import get_item_def
                    item_def = get_item_def(item_id)
                    if item_def:
                        rewards.append(f"Item: {item_def.name}")
                except Exception:
                    rewards.append(f"Item: {item_id}")
        
        if rewards:
            for reward_str in rewards:
                reward_surf = ui_font.render(f"  • {reward_str}", True, (230, 210, 120))
                screen.blit(reward_surf, (info_x, info_y))
                info_y += 22
        else:
            no_reward = ui_font.render("  No rewards", True, (160, 160, 160))
            screen.blit(no_reward, (info_x, info_y))
            info_y += 22
        
        # Action hint
        info_y += 20
        if quest_tab == "available":
            action_hint = ui_font.render(f"Press Enter/Space to {action_text.lower()} this quest", True, (180, 220, 180))
        elif quest_tab == "completed":
            action_hint = ui_font.render(f"Press Enter/Space to {action_text.lower()} this quest", True, (220, 220, 150))
        else:
            action_hint = ui_font.render("Quest in progress", True, (200, 200, 200))
        screen.blit(action_hint, (info_x, info_y))
    
    # Footer hints
    hints = [
        f"Up/Down: move • Enter/Space: {action_text.lower()} • 1–9: quick select",
        "TAB: switch screen (Inventory/Character/Skills/etc.) • Shift+TAB: switch quest tab (Available/Active/Completed) • I/C/T/J: jump to screen • ESC: close"
    ]
    draw_screen_footer(screen, ui_font, hints, w, h)

