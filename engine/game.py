import random
import math
from typing import Optional, List, Tuple

import pygame

from settings import COLOR_BG, TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from world.mapgen import generate_floor
from world.game_map import GameMap
from world.entities import Player, Enemy, Merchant
from .battle_scene import BattleScene
from .input import create_default_input_manager

from .exploration import ExplorationController
from .cheats import handle_cheat_key
from .hero_manager import (
    init_hero_for_class,
    apply_hero_stats_to_player,
    grant_xp_to_companions,
    gain_xp_from_event,
)
from .message_log import MessageLog
from systems.progression import HeroStats

from systems import perks as perk_system
from systems.inventory import Inventory, get_item_def
from systems.loot import roll_battle_loot
from systems.party import CompanionState, get_companion, recalc_companion_stats_for_level

from ui.hud_exploration import (
    draw_exploration_ui,
)
from ui.screens import (
    BaseScreen,
    InventoryScreen,
    CharacterSheetScreen,
    ShopScreen,
    SkillScreen,
)
from .perk_selection_scene import PerkSelectionScene
from ui.skill_screen import SkillScreenCore
from .floor_spawning import spawn_all_entities_for_floor
try:
    from telemetry.logger import telemetry
except Exception:  # telemetry must never break the game
    telemetry = None


# How far the player can see in tiles. Feel free to tweak.
FOV_RADIUS_TILES = 12


class GameMode:
    EXPLORATION = "exploration"
    BATTLE = "battle"


class Game:
    """
    Core game object.

    Modes:
    - "exploration": dungeon movement, floors, enemies on the map
    - "battle": zoomed turn-based fight handled by BattleScene
    """

    def __init__(self, screen: pygame.Surface, hero_class_id: str = "warrior") -> None:
        self.screen = screen

        # Logical input manager (actions -> keys/buttons).
        # For Phase 1 this is wired but not yet *used* by game logic.
        self.input_manager = create_default_input_manager()


        # Hero progression for this run (will be set in _init_hero_for_class)
        self.hero_stats = HeroStats()

        # Inventory & equipment (also set in _init_hero_for_class)
        self.inventory: Inventory = Inventory()
        self.show_inventory: bool = False

        # Consumable items live in the same inventory list but have slot
        # "consumable". All gameplay effects are driven by systems.consumables.

        # Party / companions: runtime CompanionState objects
        self.party: List[CompanionState] = []

        # Floor index (current dungeon depth)
        self.floor: int = 1

        # Active map and player
        self.current_map: Optional[GameMap] = None
        self.player: Optional[Player] = None

        # Store generated floors so layouts/enemies persist
        self.floors: dict[int, GameMap] = {}

        # UI scaling - calculate based on screen size
        screen_w, screen_h = self.screen.get_size()
        from ui.ui_scaling import get_ui_scale, get_scaled_font
        self.ui_scale = get_ui_scale(screen_w, screen_h)
        
        # Simple UI font (scaled)
        self.ui_font = get_scaled_font("consolas", 20, self.ui_scale)

        # --- Last battle log (for viewing in exploration) ---
        self.last_battle_log: List[str] = []
        self.show_battle_log: bool = False

        # --- Character sheet overlay ---
        self.show_character_sheet: bool = False

        # --- Skill screen overlay ---
        self.show_skill_screen: bool = False
        self.skill_screen_focus_index: int = 0

        # Which character the sheet is currently focusing:
        # 0 = hero, 1..N = companions in self.party order.
        self.character_sheet_focus_index: int = 0

        # Which character the inventory overlay is currently focusing:
        # 0 = hero, 1..N = companions in self.party order.
        self.inventory_focus_index: int = 0

        # Inventory list paging / scrolling
        self.inventory_page_size: int = 20  # More items visible in fullscreen
        self.inventory_scroll_offset: int = 0
        self.inventory_cursor: int = 0  # Cursor position for item selection

        # --- Exploration log overlay (multi-line message history) ---
        self.show_exploration_log: bool = False

        # Inventory / character sheet / shop / skill screen overlays as screen objects.
        self.inventory_screen = InventoryScreen()
        self.character_sheet_screen = CharacterSheetScreen()
        self.shop_screen = ShopScreen()
        self.skill_screen = SkillScreenCore(self)
        self.skill_screen_wrapper = SkillScreen()

        # Currently active full-screen UI overlay (if any).
        # Used for perk choices, inventory, character sheet, shop, etc.
        self.active_screen: Optional[BaseScreen] = None

        # Mode handling
        self.mode: str = GameMode.EXPLORATION
        self.battle_scene: Optional[BattleScene] = None

        # XP from the current battle (set when we start it)
        self.pending_battle_xp: int = 0

        # Exploration message history + backing store for last_message
        self.message_log = MessageLog(max_size=60)

        # Short grace window after battles where enemies don't auto-engage
        self.post_battle_grace: float = 0.0

        # Floor intro pause: enemies wait until the player makes the first move
        self.awaiting_floor_start: bool = True

        # Camera & zoom (exploration view)
        # Calculate default zoom based on screen size
        # More aggressive zoom scaling to make maps fill the screen better
        resolution_scale = min(screen_w / WINDOW_WIDTH, screen_h / WINDOW_HEIGHT)
        if resolution_scale > 1.0:
            # At higher resolutions, scale zoom more aggressively to keep game world visible
            # Use 0.7 multiplier instead of 0.5 for more zoom
            default_zoom = min(1.0 + (resolution_scale - 1.0) * 0.7, 3.0)  # Increased cap to 3.0x
        else:
            default_zoom = max(resolution_scale, 0.5)
        
        # Set zoom levels around the default (wider range for more zoom options)
        self.zoom_levels = [
            default_zoom * 0.7,   # More zoomed out option
            default_zoom,          # Default
            default_zoom * 1.4     # More zoomed in option
        ]
        self.zoom_index: int = 1  # start at default zoom
        
        self.camera_x: float = 0.0
        self.camera_y: float = 0.0

        # Debug flags
        self.debug_reveal_map: bool = False

        # Display mode
        self.fullscreen: bool = False

        # Reload flag for in-game loading (set by load handler, checked by main loop)
        self._reload_slot: Optional[int] = None

        # Pause menu state
        self.paused: bool = False
        self._return_to_main_menu: bool = False
        self._quit_game: bool = False

        # Initialize hero stats, perks, items and gold for the chosen class
        init_hero_for_class(self, hero_class_id)

        # Give the hero a small starting stock of basic consumables so the
        # new system is visible from the first floor.
        self._init_starting_consumables()

        # Exploration controller (handles map movement & interactions)
        self.exploration = ExplorationController(self)

        # Load initial floor
        self.load_floor(self.floor, from_direction=None)

    def _init_starting_consumables(self) -> None:
        """
        Grant a small starter pack of consumables for a fresh run.

        This is intentionally conservative; later we can move this logic
        into hero_manager/init_hero_for_class for per-class tuning.
        """
        if not hasattr(self, "inventory") or self.inventory is None:
            return

        starter_ids = [
            "small_health_potion",
            "small_health_potion",
            "stamina_draught",
        ]
        for cid in starter_ids:
            # Consumables are not randomized.
            self.inventory.add_item(cid, randomized=False)

    # ------------------------------------------------------------------
    # Mode & overlay helpers
    # ------------------------------------------------------------------

    def enter_exploration_mode(self) -> None:
        """Switch back to exploration mode and clear any active screen."""
        prev = getattr(self, "mode", None)
        self.mode = GameMode.EXPLORATION
        self.active_screen = None
        if telemetry is not None:
            telemetry.log("mode_change", frm=prev, to=self.mode)

    def enter_battle_mode(self) -> None:
        """Switch into battle mode (BattleScene must already be created)."""
        prev = getattr(self, "mode", None)
        self.mode = GameMode.BATTLE
        self.active_screen = None
        if telemetry is not None:
            telemetry.log("mode_change", frm=prev, to=self.mode)

    def run_perk_selection(self, entries: List[tuple[str, Optional[int]]]) -> None:
        """
        Run the perk selection scene (blocking).
        
        Args:
            entries: List of (owner, companion_index) tuples to enqueue.
                    owner is "hero" or "companion", companion_index is None for hero.
        
        The scene will handle its own queue and run until all selections are done.
        """
        if not entries:
            return
        
        scene = PerkSelectionScene(self)
        for owner, comp_idx in entries:
            scene.enqueue(owner, comp_idx)
        
        # Run the scene (blocking)
        scene.run()

    def toggle_inventory_overlay(self) -> None:
        """Toggle inventory overlay and manage its active screen."""
        self.show_inventory = not self.show_inventory

        if self.show_inventory:
            # Inventory takes focus; hide character sheet & logs.
            self.show_character_sheet = False
            self.show_battle_log = False
            if hasattr(self, "show_exploration_log"):
                self.show_exploration_log = False
            # When opening the inventory, default focus is the hero and reset scroll.
            self.inventory_focus_index = 0
            self.inventory_scroll_offset = 0
            self.inventory_cursor = 0
            self.inventory_cursor = 0
            # Route input to the inventory screen while it's open.
            if hasattr(self, "inventory_screen"):
                self.active_screen = self.inventory_screen
        else:
            # Closing the inventory: if it owned the focus, clear active_screen.
            if getattr(self, "active_screen", None) is getattr(self, "inventory_screen", None):
                self.active_screen = None

    def equip_item_for_inventory_focus(self, item_id: str) -> None:
        """
        Equip the given item on whichever character the inventory overlay
        is currently focusing on.

        - Focus index 0: hero (uses self.inventory.equip).
        - Focus index 1..N: companions in self.party order (uses their
          per-companion equipment + stat recomputation).
        """
        # Ensure we actually have an inventory and the item is known in it.
        if self.inventory is None:
            self.last_message = "You are not carrying anything."
            return

        if item_id not in self.inventory.items:
            # Being strict here makes it easier to debug item flow.
            self.last_message = "You do not own that item."
            return

        focus_index = int(getattr(self, "inventory_focus_index", 0))
        party_list = getattr(self, "party", None) or []

        # If focus is 0 or there are no companions, fall back to hero equip.
        if focus_index <= 0 or not party_list:
            msg = self.inventory.equip(item_id)
            self.last_message = msg
            # Re-apply hero stats so the new gear takes effect.
            if self.player is not None:
                apply_hero_stats_to_player(self, full_heal=False)
            return

        comp_idx = focus_index - 1
        if comp_idx < 0 or comp_idx >= len(party_list):
            # Defensive fallback: just treat as hero equip.
            msg = self.inventory.equip(item_id)
            self.last_message = msg
            if self.player is not None:
                apply_hero_stats_to_player(self, full_heal=False)
            return

        comp_state = party_list[comp_idx]
        if not isinstance(comp_state, CompanionState):
            # Shouldn't happen, but don't crash the game if it does.
            msg = self.inventory.equip(item_id)
            self.last_message = msg
            if self.player is not None:
                apply_hero_stats_to_player(self, full_heal=False)
            return

        # Lazy-init equipped map if needed.
        if not hasattr(comp_state, "equipped") or comp_state.equipped is None:
            comp_state.equipped = {
                "weapon": None,
                "armor": None,
                "trinket": None,
            }

        item_def = get_item_def(item_id)
        if item_def is None:
            self.last_message = "That item cannot be equipped."
            return

        slot = getattr(item_def, "slot", None)
        if not slot:
            self.last_message = f"{item_def.name} cannot be equipped."
            return

        # For now we only support the same core slots as the hero.
        if slot not in ("weapon", "armor", "trinket"):
            self.last_message = f"{item_def.name} cannot be equipped by companions."
            return

        old_item_id = comp_state.equipped.get(slot)
        comp_state.equipped[slot] = item_id

        # Recalculate this companion's stats with the new gear.
        template_id = getattr(comp_state, "template_id", None)
        comp_template = None
        if template_id:
            try:
                comp_template = get_companion(template_id)
            except KeyError:
                comp_template = None

        if comp_template is not None:
            recalc_companion_stats_for_level(comp_state, comp_template)

        # Build a nice message.
        # Name priority: explicit override -> template name -> generic label.
        display_name = getattr(comp_state, "name_override", None)
        if not display_name and comp_template is not None:
            display_name = comp_template.name
        if not display_name:
            display_name = "Companion"

        if old_item_id and old_item_id != item_id:
            old_def = get_item_def(old_item_id)
            if old_def is not None:
                self.last_message = f"{display_name} swaps {old_def.name} for {item_def.name}."
                return

        self.last_message = f"{display_name} equips {item_def.name}."

    def use_consumable_from_inventory(self, item_id: str) -> None:
        """
        Use a consumable item selected from the inventory overlay.

        Behaviour:
        - In exploration: applies to the hero entity.
        - In battle: applies to the currently active player-side unit
          and consumes that unit's turn.
        """
        from systems.consumables import get_consumable, apply_consumable_to_entity, apply_consumable_in_battle

        # Verify we actually own this item.
        if self.inventory is None or item_id not in self.inventory.items:
            self.last_message = "You do not have that consumable."
            return

        consumable = get_consumable(item_id)
        if consumable is None:
            self.last_message = "You are not sure how to use that."
            return

        # Exploration context: apply to hero entity only.
        if self.mode == GameMode.EXPLORATION:
            if self.player is None:
                self.last_message = "You have no body to use that on."
                return

            hero_max_hp = getattr(self.hero_stats, "max_hp", None)
            msg, _ = apply_consumable_to_entity(
                entity=self.player,
                hero_max_hp=hero_max_hp,
                consumable=consumable,
            )
            self.last_message = msg
            # Remove one copy from backpack.
            self.inventory.remove_one(item_id)
            return

        # Battle context: apply to the active player unit.
        if self.mode == GameMode.BATTLE and self.battle_scene is not None:
            unit = self.battle_scene._active_unit()
            # Only allow player-side units to use consumables.
            if unit.side != "player":
                self.last_message = "Enemies fumble with the bottle, confused."
                return

            battle_msg = apply_consumable_in_battle(
                game=self,
                battle_scene=self.battle_scene,
                user_unit=unit,
                consumable=consumable,
            )
            # Log into both battle log and exploration-style last message.
            self.battle_scene._log(battle_msg)
            self.last_message = battle_msg

            # Remove one copy from backpack.
            self.inventory.remove_one(item_id)

            # Using a consumable consumes the unit's turn.
            self.battle_scene._next_turn()

    def get_available_screens(self) -> List[str]:
        """Get list of available screen names (shop only if vendor nearby)."""
        screens = ["inventory", "character", "skills"]
        if getattr(self, "show_shop", False):
            screens.append("shop")
        return screens
    
    def switch_to_screen(self, screen_name: str) -> None:
        """Switch to a different full-screen UI."""
        # Close all screen flags
        self.show_inventory = False
        self.show_character_sheet = False
        self.show_skill_screen = False
        self.show_battle_log = False
        if hasattr(self, "show_exploration_log"):
            self.show_exploration_log = False
        
        # Open the requested screen
        if screen_name == "inventory":
            self.show_inventory = True
            self.inventory_focus_index = 0
            self.inventory_scroll_offset = 0
            self.active_screen = self.inventory_screen
        elif screen_name == "character":
            self.show_character_sheet = True
            self.character_sheet_focus_index = 0
            self.active_screen = self.character_sheet_screen
        elif screen_name == "skills":
            self.show_skill_screen = True
            self.skill_screen_focus_index = 0
            if hasattr(self.skill_screen, "focus_index"):
                self.skill_screen.focus_index = 0
            if hasattr(self.skill_screen, "reset_selection"):
                self.skill_screen.reset_selection()
            self.active_screen = self.skill_screen_wrapper
        elif screen_name == "shop" and getattr(self, "show_shop", False):
            # Shop is already open (show_shop is True), just set active screen
            self.active_screen = self.shop_screen
        else:
            # Invalid screen, clear active
            self.active_screen = None
    
    def cycle_to_next_screen(self, direction: int = 1) -> None:
        """Cycle to next/previous available screen. direction: 1 for next, -1 for previous."""
        available = self.get_available_screens()
        if not available:
            return
        
        # Determine current screen
        current = None
        if self.show_inventory:
            current = "inventory"
        elif self.show_character_sheet:
            current = "character"
        elif self.show_skill_screen:
            current = "skills"
        elif getattr(self, "show_shop", False) and getattr(self, "active_screen", None) is self.shop_screen:
            current = "shop"
        
        if current is None:
            # No screen open, open first available
            self.switch_to_screen(available[0])
            return
        
        # Find current index and cycle
        try:
            current_idx = available.index(current)
            next_idx = (current_idx + direction) % len(available)
            self.switch_to_screen(available[next_idx])
        except ValueError:
            # Current screen not in available list, open first
            self.switch_to_screen(available[0])

    def toggle_character_sheet_overlay(self) -> None:
        """Toggle character sheet overlay and manage its active screen."""
        self.show_character_sheet = not self.show_character_sheet

        if self.show_character_sheet:
            # Whenever we open the sheet, default focus back to the hero.
            self.character_sheet_focus_index = 0
            self.show_battle_log = False
            if hasattr(self, "show_exploration_log"):
                self.show_exploration_log = False
            # Route input to the character sheet screen while it's open.
            if hasattr(self, "character_sheet_screen"):
                self.active_screen = self.character_sheet_screen
        else:
            # Closing the sheet: if it owned the focus, clear active_screen.
            if getattr(self, "active_screen", None) is getattr(self, "character_sheet_screen", None):
                self.active_screen = None

    def toggle_skill_screen(self) -> None:
        """Toggle skill screen overlay and manage its active screen."""
        if self.show_skill_screen:
            # Closing the skill screen
            self.show_skill_screen = False
            if getattr(self, "active_screen", None) is self.skill_screen_wrapper:
                self.active_screen = None
        else:
            # Opening the skill screen - use switch_to_screen for consistency
            self.switch_to_screen("skills")

    def toggle_battle_log_overlay(self) -> None:
        """
        Toggle last battle log overlay ONLY if we actually have one.
        If there is no log, keep it off.
        """
        if not self.last_battle_log:
            self.show_battle_log = False
            return
        self.show_battle_log = not self.show_battle_log
        if self.show_battle_log and hasattr(self, "show_exploration_log"):
            # Don't stack both log overlays at once
            self.show_exploration_log = False

    def toggle_exploration_log_overlay(self) -> None:
        """
        Toggle the exploration log overlay showing recent messages
        in exploration mode.
        """
        if not hasattr(self, "show_exploration_log"):
            self.show_exploration_log = False

        self.show_exploration_log = not self.show_exploration_log
        if self.show_exploration_log:
            # Hide battle log when opening exploration log
            self.show_battle_log = False

    def is_overlay_open(self) -> bool:
        """
        Return True if a major overlay (inventory, character sheet, skill screen) is open.
        Used to pause exploration updates.
        """
        return self.show_inventory or self.show_character_sheet or self.show_skill_screen

    def cycle_character_sheet_focus(self, direction: int) -> None:
        """
        Cycle which character the character sheet is focusing on.

        0 = hero, 1..N = companions in self.party order.
        direction: +1 (next) or -1 (previous).
        """
        if not hasattr(self, "character_sheet_focus_index"):
            self.character_sheet_focus_index = 0

        party_list = getattr(self, "party", None) or []
        total_slots = 1 + len(party_list)  # hero + companions
        if total_slots <= 1:
            # Only the hero exists
            self.character_sheet_focus_index = 0
            return

        cur = int(getattr(self, "character_sheet_focus_index", 0))
        cur = cur % total_slots

        direction = 1 if direction > 0 else -1
        new_index = (cur + direction) % total_slots
        self.character_sheet_focus_index = new_index

    def cycle_inventory_focus(self, direction: int) -> None:
        """
        Cycle which character the inventory overlay is focusing on.

        0 = hero, 1..N = companions in self.party order.
        """
        # Make sure the index exists.
        if not hasattr(self, "inventory_focus_index"):
            self.inventory_focus_index = 0

        party_list = getattr(self, "party", None) or []
        total_slots = 1 + len(party_list)
        if total_slots <= 1:
            self.inventory_focus_index = 0
            return

        current = int(getattr(self, "inventory_focus_index", 0)) % total_slots
        # Normalise direction to -1 / +1 so weird values still work.
        step = -1 if direction < 0 else 1
        self.inventory_focus_index = (current + step) % total_slots

    # ------------------------------------------------------------------
    # Message log helpers (exploration history)
    # ------------------------------------------------------------------

    @property
    def last_message(self) -> str:
        """Latest message shown in the bottom exploration band."""
        return self.message_log.last_message

    @last_message.setter
    def last_message(self, value: str) -> None:
        """Set the latest message and append it to the exploration log."""
        self.message_log.last_message = value

    @property
    def exploration_log(self) -> List[str]:
        """Access to the exploration message history."""
        return self.message_log.exploration_log

    # Optional per-entry colors to be used by the HUD when rendering.
    # If colors are missing or shorter than the log, the UI will fall
    # back to its default text colors.
    @property
    def exploration_log_colors(self) -> List[Optional[Tuple[int, int, int]]]:
        return getattr(self.message_log, "exploration_log_colors", [None] * len(self.message_log.exploration_log))

    @property
    def exploration_log_max(self) -> int:
        """Maximum size of the exploration log."""
        return self.message_log.exploration_log_max

    @property
    def last_message_color(self) -> Optional[Tuple[int, int, int]]:
        """Color associated with the latest message, if any."""
        return getattr(self.message_log, "last_message_color", None)

    def add_message(self, value: str) -> None:
        """Backwards-compatible helper for adding exploration messages."""
        self.message_log.add_message(value)

    def add_message_colored(
        self,
        value: str,
        color: Optional[Tuple[int, int, int]],
    ) -> None:
        """
        Add a new exploration message with an optional explicit color.

        Used primarily for highlighting item finds by rarity; falls back
        to a plain message if the underlying log doesn't support colors.
        """
        if hasattr(self.message_log, "add_entry"):
            # New API with color support
            self.message_log.add_entry(value, color)
        else:
            # Fallback for older logs – ignore color
            self.message_log.add_message(value)

    # ------------------------------------------------------------------
    # Hero stats helpers (delegated to hero_manager module)
    # ------------------------------------------------------------------

    def apply_hero_stats_to_player(self, full_heal: bool = False) -> None:
        """Sync hero meta stats (HeroStats) to the in-world Player entity."""
        apply_hero_stats_to_player(self, full_heal)

    def gain_xp_from_event(self, amount: int) -> List[str]:
        """Grant XP from a map event, showing messages + perk selection scene."""
        return gain_xp_from_event(self, amount)

    def update_fov(self) -> None:
        """Recompute the map's FOV around the player."""
        if self.current_map is None:
            return

        # Debug: reveal entire map if enabled
        if getattr(self, "debug_reveal_map", False):
            all_coords = {
                (x, y)
                for y in range(self.current_map.height)
                for x in range(self.current_map.width)
            }
            self.current_map.visible = set(all_coords)
            self.current_map.explored = set(all_coords)
            return

        if self.player is None:
            return

        px, py = self.player.rect.center
        tx, ty = self.current_map.world_to_tile(px, py)
        self.current_map.compute_fov(tx, ty, radius=FOV_RADIUS_TILES)

    # ------------------------------------------------------------------
    # Camera / zoom helpers
    # ------------------------------------------------------------------

    @property
    def zoom(self) -> float:
        """Current zoom scale for the exploration camera."""
        levels = getattr(self, "zoom_levels", None)
        if not levels:
            return 1.0
        idx = max(0, min(self.zoom_index, len(levels) - 1))
        return float(levels[idx])

    def _center_camera_on_player(self) -> None:
        """Center the camera around the player in world space before clamping."""
        if self.player is None or self.current_map is None:
            return

        zoom = self.zoom
        if zoom <= 0:
            zoom = 1.0

        screen_w, screen_h = self.screen.get_size()
        view_w = screen_w / zoom
        view_h = screen_h / zoom

        px, py = self.player.rect.center
        self.camera_x = px - view_w / 2
        self.camera_y = py - view_h / 2

    def _clamp_camera_to_map(self) -> None:
        """Clamp the camera so it never shows outside the current map."""
        if self.current_map is None:
            return

        zoom = self.zoom
        if zoom <= 0:
            zoom = 1.0

        screen_w, screen_h = self.screen.get_size()
        view_w = screen_w / zoom
        view_h = screen_h / zoom

        world_w = self.current_map.width * TILE_SIZE
        world_h = self.current_map.height * TILE_SIZE

        max_x = max(0.0, world_w - view_w)
        max_y = max(0.0, world_h - view_h)

        self.camera_x = max(0.0, min(self.camera_x, max_x))
        self.camera_y = max(0.0, min(self.camera_y, max_y))

    def toggle_fullscreen(self) -> None:
        """
        Toggle between windowed and fullscreen display.

        - Windowed: uses WINDOW_WIDTH / WINDOW_HEIGHT from settings.
        - Fullscreen: uses the current desktop resolution.
        """
        # Decide target mode
        if not getattr(self, "fullscreen", False):
            info = pygame.display.Info()
            width, height = info.current_w, info.current_h
            new_screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
            self.fullscreen = True
        else:
            new_screen = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT)
            )
            self.fullscreen = False

        # Update the game's screen reference
        self.screen = new_screen
        
        # Recalculate UI scale for new screen size
        screen_w, screen_h = self.screen.get_size()
        from ui.ui_scaling import get_ui_scale, get_scaled_font
        self.ui_scale = get_ui_scale(screen_w, screen_h)
        
        # Recreate UI font with new scale
        self.ui_font = get_scaled_font("consolas", 20, self.ui_scale)

        # Re-center / clamp camera to fit the new viewport
        self._center_camera_on_player()
        self._clamp_camera_to_map()

    # ------------------------------------------------------------------
    # Floor / map management
    # ------------------------------------------------------------------

    def load_floor(self, floor_index: int, from_direction: Optional[str]) -> None:
        """
        Load a floor, generating it if needed.

        from_direction:
            None   -> starting game / default
            "down" -> we came from floor_index - 1 via DOWN stairs
            "up"   -> we came from floor_index + 1 via UP stairs
        """
        player_width = 24
        player_height = 24

        # Try to reuse an existing GameMap instance for this floor
        game_map = self.floors.get(floor_index)
        newly_created = False

        if game_map is None:
            # Generate raw tiles + stair positions + high-level rooms
            tiles, up_tx, up_ty, down_tx, down_ty, rooms = generate_floor(floor_index)

            # Wrap them in a GameMap object
            game_map = GameMap(
                tiles,
                up_stairs=(up_tx, up_ty),
                down_stairs=(down_tx, down_ty),
                entities=None,
                rooms=rooms,
            )
            self.floors[floor_index] = game_map
            newly_created = True

        # From now on self.current_map is a GameMap, not a tuple
        self.current_map = game_map

        # Spawn enemies / events / chests / merchants only once per floor
        if newly_created:
            spawn_all_entities_for_floor(self, game_map, floor_index)

        # Decide spawn position based on stair direction
        if from_direction == "down" and game_map.up_stairs is not None:
            spawn_x, spawn_y = game_map.center_entity_on_tile(
                game_map.up_stairs[0],
                game_map.up_stairs[1],
                player_width,
                player_height,
            )
        elif from_direction == "up" and game_map.down_stairs is not None:
            spawn_x, spawn_y = game_map.center_entity_on_tile(
                game_map.down_stairs[0],
                game_map.down_stairs[1],
                player_width,
                player_height,
            )
        else:
            # Starting game or fallback: up stairs if they exist, else center
            if game_map.up_stairs is not None:
                spawn_x, spawn_y = game_map.center_entity_on_tile(
                    game_map.up_stairs[0],
                    game_map.up_stairs[1],
                    player_width,
                    player_height,
                )
            else:
                center_tx = game_map.width // 2
                center_ty = game_map.height // 2
                spawn_x, spawn_y = game_map.center_entity_on_tile(
                    center_tx,
                    center_ty,
                    player_width,
                    player_height,
                )

        # (Re)create the Player on this floor
        self.player = Player(
            x=spawn_x,
            y=spawn_y,
            width=player_width,
            height=player_height,
        )

        # Apply hero stats (full heal on floor entry)
        apply_hero_stats_to_player(self, full_heal=True)
        # Reset the camera around the player for this floor
        self._center_camera_on_player()
        self._clamp_camera_to_map()
        # Floor starts paused until the player actually moves
        self.awaiting_floor_start = True

        # Initial FOV on this floor (centered on player spawn)
        self.update_fov()

    def try_change_floor(self, delta: int) -> None:
        """
        Attempt to change floors via stairs up/down based on delta:
        - +1: go down stairs
        - -1: go up stairs
        """
        if self.current_map is None or self.player is None:
            return

        game_map = self.current_map

        # Decide which stairs we're using on THIS floor
        if delta > 0:
            stairs_tile = game_map.down_stairs
            direction = "down"
        else:
            stairs_tile = game_map.up_stairs
            direction = "up"

        if stairs_tile is None:
            self.last_message = "There are no stairs here."
            return

        # Get the player's current tile coordinates
        px, py = self.player.rect.center
        player_tx, player_ty = game_map.world_to_tile(px, py)

        # Must actually stand on the stairs tile
        if (player_tx, player_ty) != stairs_tile:
            self.last_message = "You need to stand on the stairs to travel."
            return

        new_floor = self.floor + delta
        if new_floor <= 0:
            self.last_message = "You cannot go any higher."
            return

        # Change floor and spawn appropriately on the new floor
        self.floor = new_floor
        self.load_floor(self.floor, from_direction=direction)
        self.last_message = f"You travel to floor {self.floor}."

    # ------------------------------------------------------------------
    # Battle handling
    # ------------------------------------------------------------------

    def start_battle(self, enemy: Enemy) -> None:
        """
        Switch from exploration to battle mode.

        Instead of fighting a single enemy, we collect a small group of nearby
        enemies into one encounter and fight them together.
        """
        if (
            self.mode != GameMode.EXPLORATION
            or self.current_map is None
            or self.player is None
        ):
            return

        # As soon as we start a new battle, hide any previous overlays
        self.show_battle_log = False
        self.show_character_sheet = False

        # 1) Build encounter group around the player
        group: List[Enemy] = []

        # Always include the enemy that triggered the battle
        if enemy in self.current_map.entities:
            group.append(enemy)

        # Add other nearby enemies within a radius
        radius = TILE_SIZE * 4
        px, py = self.player.rect.center

        for entity in list(self.current_map.entities):
            if not isinstance(entity, Enemy):
                continue
            if entity is enemy:
                continue
            ex, ey = entity.rect.center
            dx = ex - px
            dy = ey - py
            if dx * dx + dy * dy <= radius * radius:
                group.append(entity)

        # Limit how many can join a single battle (for sanity)
        max_group_size = 3
        encounter_enemies = group[:max_group_size]

        # 2) Remove all encounter enemies from the map so they can't be re-used
        for e in encounter_enemies:
            try:
                self.current_map.entities.remove(e)
            except ValueError:
                pass

        # 3) Remember XP for this encounter (sum of all enemies in the group)
        xp_total = 0
        for e in encounter_enemies:
            xp_total += int(getattr(e, "xp_reward", 5))
        self.pending_battle_xp = xp_total

        if telemetry is not None:
            telemetry.log(
                "battle_start",
                floor=getattr(self, "floor", None),
                enemy_count=len(encounter_enemies),
                xp_total=int(xp_total),
            )


        # 4) Create battle scene with the entire group + current party.
        # Pass runtime CompanionState objects directly; BattleScene knows how
        # to use their own stats (HP / ATK / DEF / skill_power).
        party_list = getattr(self, "party", None) or []
        companions_for_battle = list(party_list) if party_list else None

        self.battle_scene = BattleScene(
            self.player,
            encounter_enemies,
            self.ui_font,
            companions=companions_for_battle,
            game=self,  # Pass game reference for inventory access
        )
        self.enter_battle_mode()

    def restart_run(self) -> None:
        """
        Reset everything back to floor 1.

        We keep the current hero class but reset stats, gold, and inventory
        to that class's starting values.
        """
        # Remember current class (default to warrior if something went wrong)
        current_class = getattr(self.hero_stats, "hero_class_id", "warrior")

        # Clear current run state
        self.floors.clear()
        self.current_map = None
        self.player = None
        self.battle_scene = None
        self.enter_exploration_mode()

        # Reset logs and overlays
        self.message_log.clear()
        self.pending_battle_xp = 0
        self.post_battle_grace = 0.0
        self.last_battle_log = []
        self.show_battle_log = False
        self.show_exploration_log = False
        self.show_character_sheet = False

        # Perk selection is now handled by PerkSelectionScene (no cleanup needed here)

        # Reset floor back to 1
        self.floor = 1

        # Fresh hero + inventory for the same class
        init_hero_for_class(self, current_class)

        self.load_floor(self.floor, from_direction=None)

    def roll_battle_reward(self) -> List[str]:
        """
        Roll gold and items after a battle.
        Returns a list of message strings describing rewards.
        """
        messages: List[str] = []

        # --- Gold pouch ---
        # Enemies on deeper floors give more gold
        base_min_gold = 3 + self.floor
        base_max_gold = 6 + self.floor * 2

        gold_amount = random.randint(base_min_gold, base_max_gold)
        if hasattr(self.hero_stats, "add_gold"):
            gained_gold = self.hero_stats.add_gold(gold_amount)
        else:
            gained_gold = gold_amount

        if gained_gold > 0:
            messages.append(f"You pick up a pouch of {gained_gold} gold.")

        # --- Item drop ---
        # Roll for item loot (25-50% chance based on floor)
        if self.inventory is not None:
            item_id = roll_battle_loot(self.floor)
            if item_id is not None:
                # Add item to inventory (with randomization enabled)
                self.inventory.add_item(item_id, randomized=True)
                # Store floor index for randomization context
                if not hasattr(self.inventory, "_current_floor"):
                    self.inventory._current_floor = self.floor
                else:
                    self.inventory._current_floor = self.floor
                
                # Get item name for message
                from systems.inventory import get_item_def
                item_def = get_item_def(item_id)
                item_name = item_def.name if item_def is not None else item_id
                messages.append(f"You find {item_name} among the remains.")

        return messages

    def _check_battle_finished(self) -> None:
        """
        See if the active battle scene is finished and act accordingly.
        Award XP / healing / small rewards on victory; restart on defeat.

        On level-up, generate perk choices and enter 'perk_choice' mode.
        """
        if self.battle_scene is None:
            return
        if not self.battle_scene.finished:
            return

        status = self.battle_scene.status
        xp_reward = self.pending_battle_xp
        self.pending_battle_xp = 0
        if telemetry is not None:
            telemetry.log(
                "battle_end",
                status=status,
                xp_reward=int(xp_reward),
                floor=getattr(self, "floor", None),
            )


        # Keep a copy of the combat log so we can display it in exploration
        if self.battle_scene.combat_log:
            self.last_battle_log = list(self.battle_scene.combat_log)
        else:
            self.last_battle_log = []

        if status == "victory":
            messages: list[str] = []

            # 1) XP + level ups
            leveled_up = False
            perk_entries: List[tuple[str, Optional[int]]] = []
            
            if xp_reward > 0:
                old_level = self.hero_stats.level
                messages.extend(self.hero_stats.grant_xp(xp_reward))

                new_level = self.hero_stats.level
                leveled_up = new_level > old_level
                if leveled_up:
                    perk_entries.append(("hero", None))

                # Companions gain the same XP amount independently.
                leveled_companions: List[int] = []
                companion_msgs = grant_xp_to_companions(self, xp_reward, leveled_companions)
                if companion_msgs:
                    messages.extend(companion_msgs)
                
                # Add leveled companions to perk entries
                for idx in leveled_companions:
                    perk_entries.append(("companion", idx))

            # 2) Sync stats onto player and apply baseline healing
            if self.player is not None:
                apply_hero_stats_to_player(self, full_heal=False)

                if leveled_up:
                    # Full heal when leveling up
                    self.player.hp = self.hero_stats.max_hp
                    messages.append("You feel completely renewed.")
                else:
                    # Small heal after each won fight
                    heal = max(1, int(self.hero_stats.max_hp * 0.25))
                    new_hp = min(self.hero_stats.max_hp, self.player.hp + heal)
                    actual_heal = new_hp - self.player.hp
                    self.player.hp = new_hp
                    if actual_heal > 0:
                        messages.append(f"You recover {actual_heal} HP after the fight.")

                # 3) Roll simple rewards (like gold)
                reward_msgs = self.roll_battle_reward()
                messages.extend(reward_msgs)

            # 4) Go back to exploration
            self.enter_exploration_mode()
            self.battle_scene = None

            # 5) Log messages into exploration log
            for msg in messages:
                self.add_message(msg)

            # 6) Run perk selection scene if anyone leveled up
            if perk_entries:
                self.run_perk_selection(perk_entries)

        elif status == "defeat":
            # Simple defeat handling: message + restart.
            self.add_message("You were defeated. The dungeon claims another hero...")
            self.restart_run()
            self.enter_exploration_mode()
            self.battle_scene = None

    # ------------------------------------------------------------------
    # Pause menu handling
    # ------------------------------------------------------------------

    def _handle_pause_menu(self) -> None:
        """Open pause menu and handle user selection."""
        from engine.pause_menu import PauseMenuScene, OptionsMenuScene
        from engine.save_menu import SaveMenuScene
        from engine.save_system import save_game, load_game
        
        # Draw current game state first (so it's visible behind pause overlay)
        if self.mode == GameMode.EXPLORATION:
            self.draw_exploration()
        elif self.mode == GameMode.BATTLE:
            self.draw_battle()
        pygame.display.flip()
        
        self.paused = True
        pause_menu = PauseMenuScene(self.screen)
        choice = pause_menu.run()
        self.paused = False
        
        if choice is None or choice == "resume":
            return
        
        elif choice == "save":
            # Open save menu
            save_menu = SaveMenuScene(self.screen, mode="save")
            selected_slot = save_menu.run()
            if selected_slot is not None:
                if save_game(self, slot=selected_slot):
                    self.add_message(f"Game saved to slot {selected_slot}!")
                else:
                    self.add_message("Failed to save game.")
        
        elif choice == "load":
            # Open load menu
            load_menu = SaveMenuScene(self.screen, mode="load")
            selected_slot = load_menu.run()
            if selected_slot is not None:
                # Set reload flag for main loop
                self._reload_slot = selected_slot
                self.add_message(f"Loading game from slot {selected_slot}...")
        
        elif choice == "options":
            # Show options/controls screen
            from engine.resolution_menu import ResolutionMenuScene
            options_menu = OptionsMenuScene(self.screen)
            sub_choice = options_menu.run()
            
            if sub_choice == "resolution":
                # Open resolution menu
                res_menu = ResolutionMenuScene(self.screen)
                result = res_menu.run()
                if result is not None:
                    width, height, match_desktop = result
                    self.add_message(f"Resolution set to {width}x{height}. Restart to apply.")
        
        elif choice == "main_menu":
            # Signal to return to main menu (set a flag for main loop)
            self._return_to_main_menu = True
        
        elif choice == "quit":
            # Signal to quit (set a flag for main loop)
            self._quit_game = True

    # ------------------------------------------------------------------
    # Main loop: update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        # Don't update game logic when paused
        if self.paused:
            return
        
        if self.mode == GameMode.EXPLORATION:
            if self.post_battle_grace > 0.0:
                self.post_battle_grace = max(0.0, self.post_battle_grace - dt)

            # If a major overlay (inventory / character sheet) is open,
            # pause exploration updates so the world doesn't move behind the UI.
            if self.is_overlay_open():
                return

            # Exploration is handled by the controller...
            self.exploration.update(dt)
            # ...and after movement, we always refresh FOV around the player.
            self.update_fov()
            # Update exploration camera to follow the player and stay in-bounds.
            self._center_camera_on_player()
            self._clamp_camera_to_map()

        elif self.mode == GameMode.BATTLE:
            if self.battle_scene is not None:
                self.battle_scene.update(dt)
                self._check_battle_finished()

    # ------------------------------------------------------------------
    # Main loop: event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Dispatch events based on current game mode.
        Global debug / cheat keys are processed first.
        """
        # Pause menu (ESC) - check before other handlers
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Don't pause if we're in a modal screen (let it handle ESC)
            if getattr(self, "active_screen", None) is not None:
                # Let the active screen handle ESC (it will close itself)
                pass
            else:
                # Toggle pause menu
                self._handle_pause_menu()
                return
        
        # If paused, only handle resume/unpause
        if self.paused:
            return
        
        # Cheats: handle global debug keys, consume the event if needed.
        if handle_cheat_key(self, event):
            return

        # Global fullscreen toggle.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return
        
        # Global save/load game
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F5:
                # Quick save to slot 1
                from engine.save_system import save_game
                if save_game(self, slot=1):
                    self.add_message("Game saved to slot 1!")
                else:
                    self.add_message("Failed to save game.")
                return
            elif event.key == pygame.K_F6:
                # Open save menu
                from engine.save_menu import SaveMenuScene
                from engine.save_system import save_game
                save_menu = SaveMenuScene(self.screen, mode="save")
                selected_slot = save_menu.run()
                if selected_slot is not None:
                    if save_game(self, slot=selected_slot):
                        self.add_message(f"Game saved to slot {selected_slot}!")
                    else:
                        self.add_message("Failed to save game.")
                return
            elif event.key == pygame.K_F7:
                # Open load menu
                from engine.save_menu import SaveMenuScene
                from engine.save_system import load_game, list_saves
                load_menu = SaveMenuScene(self.screen, mode="load")
                selected_slot = load_menu.run()
                if selected_slot is not None:
                    # Check if save exists
                    saves = list_saves()
                    if selected_slot in saves:
                        # Set reload flag - main loop will handle the actual reload
                        self._reload_slot = selected_slot
                        self.add_message(f"Loading game from slot {selected_slot}...")
                    else:
                        self.add_message("No save found in that slot.")
                return

        # Mode-specific handling.
        if self.mode == GameMode.EXPLORATION:
            # If a modal screen is active (inventory, character sheet, etc.),
            # route input to it instead of the exploration controller.
            if getattr(self, "active_screen", None) is not None:
                self.active_screen.handle_event(self, event)
            else:
                self.exploration.handle_event(event)


        elif self.mode == GameMode.BATTLE:
            # In battle mode, a modal screen (inventory, character sheet, etc.)
            # also takes input priority.
            if getattr(self, "active_screen", None) is not None:
                self.active_screen.handle_event(self, event)
            elif self.battle_scene is not None:
                # Pass the Game so the battle scene can read logical input actions.
                self.battle_scene.handle_event(self, event)
                self._check_battle_finished()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self) -> None:
        """
        Top-level draw: render the world based on mode, then any active
        full-screen overlay (perk choice, inventory, character sheet, etc.),
        and finally flip the display once.
        """
        if self.mode == GameMode.EXPLORATION:
            self.draw_exploration()
        elif self.mode == GameMode.BATTLE:
            self.draw_battle()

        # Draw an active overlay screen on top (inventory, character sheet, skill screen, etc.).
        if getattr(self, "active_screen", None) is not None:
            self.active_screen.draw(self)
            # Update skill screen visual state (cursor blink, etc.)
            if self.active_screen is self.skill_screen_wrapper:
                from settings import FPS
                dt = 1.0 / FPS  # Approximate dt for cursor blink
                self.skill_screen.update(dt)
        
        # Draw pause overlay if paused (pause menu handles its own drawing)
        # The pause menu is drawn by _handle_pause_menu, so we don't need to draw it here

        # Flip the final composed frame to the screen.
        pygame.display.flip()

    def draw_exploration(self) -> None:
        assert self.current_map is not None
        assert self.player is not None

        self.screen.fill(COLOR_BG)

        zoom = self.zoom
        camera_x = getattr(self, "camera_x", 0.0)
        camera_y = getattr(self, "camera_y", 0.0)

        # Map tiles
        self.current_map.draw(
            self.screen,
            camera_x=camera_x,
            camera_y=camera_y,
            zoom=zoom,
        )

        # Non-player entities (enemies, chests, props…) – only if visible
        for entity in getattr(self.current_map, "entities", []):
            cx, cy = entity.rect.center
            tx, ty = self.current_map.world_to_tile(cx, cy)
            if (tx, ty) not in self.current_map.visible:
                continue
            entity.draw(
                self.screen,
                camera_x=camera_x,
                camera_y=camera_y,
                zoom=zoom,
            )

        # Draw the player on top of everything else
        self.player.draw(
            self.screen,
            camera_x=camera_x,
            camera_y=camera_y,
            zoom=zoom,
        )

        # HUD + overlays
        draw_exploration_ui(self)

    def draw_battle(self) -> None:
        if self.battle_scene is None:
            return

        self.screen.fill(COLOR_BG)
        # Pass the Game instance so the battle scene can read input bindings
        self.battle_scene.draw(self.screen, self)
        # Note: Don't call pygame.display.flip() here - the main draw() method handles flipping
        # after all overlays are drawn to prevent flickering

