"""
Equipment management system.

Handles equipping items for heroes and companions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from systems.inventory import get_item_def
from systems.party import CompanionState, get_companion, recalc_companion_stats_for_level
from systems.stats import apply_hero_stats_to_player

if TYPE_CHECKING:
    from ..core.game import Game


class EquipmentManager:
    """
    Manages equipment for heroes and companions.
    
    Responsibilities:
    - Equip items for hero or companions
    - Handle equipment slot validation
    - Recalculate stats after equipment changes
    """
    
    @staticmethod
    def equip_item_for_character(
        game: "Game",
        item_id: str,
        focus_index: int,
    ) -> str:
        """
        Equip an item for a character (hero or companion) based on focus index.
        
        Args:
            game: Game instance
            item_id: ID of the item to equip
            focus_index: 0 for hero, 1+ for companions in party order
        
        Returns:
            Message string describing what happened
        """
        # Ensure we actually have an inventory and the item is known in it
        if game.inventory is None:
            return "You are not carrying anything."
        
        if item_id not in game.inventory.items:
            return "You do not own that item."
        
        party_list = getattr(game, "party", None) or []
        
        # If focus is 0 or there are no companions, fall back to hero equip
        if focus_index <= 0 or not party_list:
            msg = game.inventory.equip(item_id)
            # Re-apply hero stats so the new gear takes effect
            if game.player is not None:
                apply_hero_stats_to_player(game, full_heal=False)
            return msg
        
        comp_idx = focus_index - 1
        if comp_idx < 0 or comp_idx >= len(party_list):
            # Defensive fallback: just treat as hero equip
            msg = game.inventory.equip(item_id)
            if game.player is not None:
                apply_hero_stats_to_player(game, full_heal=False)
            return msg
        
        comp_state = party_list[comp_idx]
        if not isinstance(comp_state, CompanionState):
            # Shouldn't happen, but don't crash the game if it does
            msg = game.inventory.equip(item_id)
            if game.player is not None:
                apply_hero_stats_to_player(game, full_heal=False)
            return msg
        
        # Lazy-init equipped map if needed
        if not hasattr(comp_state, "equipped") or comp_state.equipped is None:
            comp_state.equipped = {
                "weapon": None,
                "armor": None,
                "trinket": None,
            }
        
        item_def = get_item_def(item_id)
        if item_def is None:
            return "That item cannot be equipped."
        
        slot = getattr(item_def, "slot", None)
        if not slot:
            return f"{item_def.name} cannot be equipped."
        
        # For now we only support the same core slots as the hero
        if slot not in ("weapon", "armor", "trinket"):
            return f"{item_def.name} cannot be equipped by companions."
        
        old_item_id = comp_state.equipped.get(slot)
        comp_state.equipped[slot] = item_id
        
        # Recalculate this companion's stats with the new gear
        template_id = getattr(comp_state, "template_id", None)
        comp_template = None
        if template_id:
            try:
                comp_template = get_companion(template_id)
            except KeyError:
                comp_template = None
        
        if comp_template is not None:
            recalc_companion_stats_for_level(comp_state, comp_template)
        
        # Build a nice message
        # Name priority: explicit override -> template name -> generic label
        display_name = getattr(comp_state, "name_override", None)
        if not display_name and comp_template is not None:
            display_name = comp_template.name
        if not display_name:
            display_name = "Companion"
        
        if old_item_id and old_item_id != item_id:
            old_def = get_item_def(old_item_id)
            if old_def is not None:
                return f"{display_name} swaps {old_def.name} for {item_def.name}."
        
        return f"{display_name} equips {item_def.name}."

