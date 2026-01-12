import random
import math
from typing import Optional, List, Tuple, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from world.overworld.map import OverworldMap
    from world.overworld.config import OverworldConfig
    from world.poi.base import PointOfInterest
    from world.time.time_system import TimeSystem

from settings import COLOR_BG, TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from world.mapgen import generate_floor
from world.game_map import GameMap
from world.entities import Player, Enemy, Merchant
from ..battle import BattleScene
from ..controllers.input import create_default_input_manager

from ..controllers.exploration import ExplorationController
from ..utils.cheats import handle_cheat_key
from systems.input import InputAction
from ..managers.hero_manager import (
    init_hero_for_class,
    apply_hero_stats_to_player,
    grant_xp_to_companions,
    gain_xp_from_event,
)
from ..managers.message_log import MessageLog
from ..managers.floor_manager import FloorManager
from ..managers.battle_orchestrator import BattleOrchestrator
from ..managers.camera_manager import CameraManager
from ..managers.ui_screen_manager import UIScreenManager
from ..managers.equipment_manager import EquipmentManager
from systems.progression import HeroStats

from systems import perks as perk_system
from systems.inventory import Inventory, get_item_def
from systems.loot import roll_battle_loot
from systems.party import CompanionState

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
from ..scenes.perk_selection_scene import PerkSelectionScene
from ui.skill_screen import SkillScreenCore
from ..managers.floor_spawning import spawn_all_entities_for_floor
try:
    from telemetry.logger import telemetry
except Exception:  # telemetry must never break the game
    telemetry = None


from settings import FOV_RADIUS_TILES

class GameMode:
    OVERWORLD = "overworld"
    EXPLORATION = "exploration"
    BATTLE = "battle"


class Game:
    """
    Core game object.

    Modes:
    - "exploration": dungeon movement, floors, enemies on the map
    - "battle": zoomed turn-based fight handled by BattleScene
    """
    
    @property
    def floor(self) -> int:
        """Current floor number (convenience property for FloorManager)."""
        return self.floor_manager.floor
    
    @floor.setter
    def floor(self, value: int) -> None:
        """Set current floor number."""
        self.floor_manager.floor = value
    
    @property
    def floors(self) -> dict[int, GameMap]:
        """Dictionary of generated floors (convenience property for FloorManager)."""
        return self.floor_manager.floors
    
    @property
    def awaiting_floor_start(self) -> bool:
        """Whether we're waiting for the player to make the first move on a floor."""
        return self.floor_manager.awaiting_floor_start
    
    @awaiting_floor_start.setter
    def awaiting_floor_start(self, value: bool) -> None:
        """Set whether we're awaiting floor start."""
        self.floor_manager.awaiting_floor_start = value
    
    @property
    def camera_x(self) -> float:
        """Camera X position (convenience property for CameraManager)."""
        return self.camera_manager.camera_x
    
    @camera_x.setter
    def camera_x(self, value: float) -> None:
        """Set camera X position."""
        self.camera_manager.camera_x = value
    
    @property
    def camera_y(self) -> float:
        """Camera Y position (convenience property for CameraManager)."""
        return self.camera_manager.camera_y
    
    @camera_y.setter
    def camera_y(self, value: float) -> None:
        """Set camera Y position."""
        self.camera_manager.camera_y = value
    
    @property
    def zoom_levels(self) -> List[float]:
        """Zoom levels for exploration camera (convenience property)."""
        return self.camera_manager.zoom_levels
    
    @property
    def zoom_index(self) -> int:
        """Current zoom level index (convenience property)."""
        return self.camera_manager.zoom_index
    
    @zoom_index.setter
    def zoom_index(self, value: int) -> None:
        """Set current zoom level index."""
        self.camera_manager.zoom_index = value
    
    @property
    def overworld_zoom_levels(self) -> List[float]:
        """Zoom levels for overworld camera (convenience property)."""
        return self.camera_manager.overworld_zoom_levels
    
    @property
    def overworld_zoom_index(self) -> int:
        """Current overworld zoom level index (convenience property)."""
        return self.camera_manager.overworld_zoom_index
    
    @overworld_zoom_index.setter
    def overworld_zoom_index(self, value: int) -> None:
        """Set current overworld zoom level index."""
        self.camera_manager.overworld_zoom_index = value
    
    # UI Screen Manager properties (for backward compatibility)
    @property
    def show_inventory(self) -> bool:
        """Whether inventory overlay is visible."""
        return self.ui_screen_manager.show_inventory
    
    @show_inventory.setter
    def show_inventory(self, value: bool) -> None:
        """Set inventory overlay visibility."""
        self.ui_screen_manager.show_inventory = value
    
    @property
    def show_character_sheet(self) -> bool:
        """Whether character sheet overlay is visible."""
        return self.ui_screen_manager.show_character_sheet
    
    @show_character_sheet.setter
    def show_character_sheet(self, value: bool) -> None:
        """Set character sheet overlay visibility."""
        self.ui_screen_manager.show_character_sheet = value
    
    @property
    def show_skill_screen(self) -> bool:
        """Whether skill screen overlay is visible."""
        return self.ui_screen_manager.show_skill_screen
    
    @show_skill_screen.setter
    def show_skill_screen(self, value: bool) -> None:
        """Set skill screen overlay visibility."""
        self.ui_screen_manager.show_skill_screen = value
    
    @property
    def show_battle_log(self) -> bool:
        """Whether battle log overlay is visible."""
        return self.ui_screen_manager.show_battle_log
    
    @show_battle_log.setter
    def show_battle_log(self, value: bool) -> None:
        """Set battle log overlay visibility."""
        self.ui_screen_manager.show_battle_log = value
    
    @property
    def show_exploration_log(self) -> bool:
        """Whether exploration log overlay is visible."""
        return self.ui_screen_manager.show_exploration_log
    
    @show_exploration_log.setter
    def show_exploration_log(self, value: bool) -> None:
        """Set exploration log overlay visibility."""
        self.ui_screen_manager.show_exploration_log = value
    
    @property
    def character_sheet_focus_index(self) -> int:
        """Index of character focused in character sheet (0=hero, 1+=companions)."""
        return self.ui_screen_manager.character_sheet_focus_index
    
    @character_sheet_focus_index.setter
    def character_sheet_focus_index(self, value: int) -> None:
        """Set character sheet focus index."""
        self.ui_screen_manager.character_sheet_focus_index = value
    
    @property
    def inventory_focus_index(self) -> int:
        """Index of character focused in inventory (0=hero, 1+=companions)."""
        return self.ui_screen_manager.inventory_focus_index
    
    @inventory_focus_index.setter
    def inventory_focus_index(self, value: int) -> None:
        """Set inventory focus index."""
        self.ui_screen_manager.inventory_focus_index = value
    
    @property
    def skill_screen_focus_index(self) -> int:
        """Focus index for skill screen."""
        return self.ui_screen_manager.skill_screen_focus_index
    
    @skill_screen_focus_index.setter
    def skill_screen_focus_index(self, value: int) -> None:
        """Set skill screen focus index."""
        self.ui_screen_manager.skill_screen_focus_index = value
    
    @property
    def inventory_scroll_offset(self) -> int:
        """Scroll offset for inventory list."""
        return self.ui_screen_manager.inventory_scroll_offset
    
    @inventory_scroll_offset.setter
    def inventory_scroll_offset(self, value: int) -> None:
        """Set inventory scroll offset."""
        self.ui_screen_manager.inventory_scroll_offset = value
    
    @property
    def inventory_cursor(self) -> int:
        """Cursor position for item selection in inventory."""
        return self.ui_screen_manager.inventory_cursor
    
    @inventory_cursor.setter
    def inventory_cursor(self, value: int) -> None:
        """Set inventory cursor position."""
        self.ui_screen_manager.inventory_cursor = value

    def __init__(self, screen: pygame.Surface, hero_class_id: str = "warrior", hero_background_id: Optional[str] = None, overworld_config: Optional["OverworldConfig"] = None) -> None:
        self.screen = screen

        # Logical input manager (actions -> keys/buttons).
        # For Phase 1 this is wired but not yet *used* by game logic.
        self.input_manager = create_default_input_manager()


        # Hero progression for this run (will be set in _init_hero_for_class)
        self.hero_stats = HeroStats()

        # Inventory & equipment (also set in _init_hero_for_class)
        self.inventory: Inventory = Inventory()
        # Note: show_inventory managed by ui_screen_manager (see property below)

        # Consumable items live in the same inventory list but have slot
        # "consumable". All gameplay effects are driven by systems.consumables.

        # Party / companions: runtime CompanionState objects
        self.party: List[CompanionState] = []

        # Floor management
        self.floor_manager = FloorManager(starting_floor=1)

        # Active map and player
        self.current_map: Optional[GameMap] = None
        self.player: Optional[Player] = None

        # UI scaling - calculate based on screen size
        screen_w, screen_h = self.screen.get_size()
        from ui.ui_scaling import get_ui_scale, get_scaled_font
        self.ui_scale = get_ui_scale(screen_w, screen_h)
        
        # Simple UI font (scaled)
        self.ui_font = get_scaled_font("consolas", 20, self.ui_scale)

        # --- Last battle log (for viewing in exploration) ---
        self.last_battle_log: List[str] = []
        # Note: UI state managed by ui_screen_manager (see properties below)
        
        # --- Recruitment screen overlay ---
        self.show_recruitment: bool = False
        self.recruitment_cursor: int = 0
        self.available_companions: list = []

        # Inventory list paging / scrolling
        self.inventory_page_size: int = 20  # More items visible in fullscreen
        # Note: inventory_scroll_offset, inventory_cursor managed by ui_screen_manager
        
        # Inventory enhancements: filtering, sorting, search
        from ui.inventory_enhancements import FilterMode, SortMode
        self.inventory_filter: FilterMode = FilterMode.ALL
        self.inventory_sort: SortMode = SortMode.DEFAULT
        self.inventory_search: str = ""
        
        # Tooltip system
        from ui.tooltip import Tooltip
        self.tooltip = Tooltip()
        
        # Initialize sprite system (with fallback to color-based rendering)
        from ..sprites.init_sprites import init_game_sprites
        try:
            init_game_sprites()
        except Exception as e:
            print(f"Warning: Sprite system initialization failed: {e}")
            print("Falling back to color-based rendering.")

        # Note: show_exploration_log managed by ui_screen_manager (see property below)

        # Inventory / character sheet / shop / skill screen / recruitment overlays as screen objects.
        self.inventory_screen = InventoryScreen()
        self.character_sheet_screen = CharacterSheetScreen()
        self.shop_screen = ShopScreen()
        self.skill_screen = SkillScreenCore(self)
        self.skill_screen_wrapper = SkillScreen()
        from ui.village.recruitment_screen import RecruitmentScreen
        self.recruitment_screen = RecruitmentScreen()
        from ui.village.quest_screen import QuestScreen
        self.quest_screen = QuestScreen()

        # Currently active full-screen UI overlay (if any).
        # Used for perk choices, inventory, character sheet, shop, etc.
        self.active_screen: Optional[BaseScreen] = None

        # Mode handling
        self.mode: str = GameMode.OVERWORLD  # Start in overworld mode
        self.battle_scene: Optional[BattleScene] = None
        
        # Overworld system
        self.overworld_map: Optional["OverworldMap"] = None
        self.current_poi: Optional["PointOfInterest"] = None
        self.time_system: Optional["TimeSystem"] = None
        
        # Confirmation dialog state
        self.pending_overworld_confirmation: bool = False
        self.confirmation_message: str = ""
        self.confirmation_action: Optional[callable] = None

        # XP from the current battle (set when we start it)
        self.pending_battle_xp: int = 0

        # Exploration message history + backing store for last_message
        self.message_log = MessageLog(max_size=60)

        # Short grace window after battles where enemies don't auto-engage
        self.post_battle_grace: float = 0.0

        # Floor intro pause: enemies wait until the player makes the first move
        self.awaiting_floor_start: bool = True

        # Camera & zoom management
        self.camera_manager = CameraManager(screen)
        
        # UI screen and overlay management
        self.ui_screen_manager = UIScreenManager()

        # Debug flags
        self.debug_reveal_map: bool = False
        
        # Debug console
        try:
            from ..utils.debug_console import DebugConsole
            self.debug_console = DebugConsole(screen)
            # Register with error handler
            from ..utils.error_handler import set_debug_console
            set_debug_console(self.debug_console)
        except Exception:
            # If debug console fails to initialize, continue without it
            self.debug_console = None

        # Display mode
        self.fullscreen: bool = False

        # Reload flag for in-game loading (set by load handler, checked by main loop)
        self._reload_slot: Optional[int] = None

        # Pause menu state
        self.paused: bool = False
        self._return_to_main_menu: bool = False
        self._quit_game: bool = False

        # Initialize hero stats, perks, items and gold for the chosen class
        init_hero_for_class(self, hero_class_id, hero_background_id=hero_background_id)

        # Give the hero a small starting stock of basic consumables so the
        # new system is visible from the first floor.
        self._init_starting_consumables()

        # Exploration controller (handles map movement & interactions)
        self.exploration = ExplorationController(self)
        
        # Overworld controller (handles overworld movement & interactions)
        from ..controllers.overworld import OverworldController
        self.overworld = OverworldController(self)
        
        # Initialize overworld system (use provided config if available)
        self._init_overworld(overworld_config)

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
    
    def _init_overworld(self, overworld_config: Optional["OverworldConfig"] = None) -> None:
        """Initialize the overworld map and time system."""
        try:
            print("Initializing overworld system...")
            from world.overworld import OverworldConfig, WorldGenerator
            from world.time import TimeSystem
            
            # Load overworld configuration (use provided config or load from file)
            print("Loading overworld config...")
            if overworld_config is not None:
                config = overworld_config
                print(f"Using provided config: {config.world_width}x{config.world_height}, density={config.poi_density}")
                
                # Set zoom index from config
                if hasattr(config, "default_zoom_index"):
                    self.overworld_zoom_index = config.default_zoom_index
                    # Clamp to valid range
                    self.overworld_zoom_index = max(0, min(self.overworld_zoom_index, len(self.overworld_zoom_levels) - 1))
            else:
                config = OverworldConfig.load()
                print(f"Config loaded from file: {config.world_width}x{config.world_height}, density={config.poi_density}")
                
                # Set zoom index from config if available
                if hasattr(config, "default_zoom_index"):
                    self.overworld_zoom_index = config.default_zoom_index
                    self.overworld_zoom_index = max(0, min(self.overworld_zoom_index, len(self.overworld_zoom_levels) - 1))
            
            # Generate overworld
            print("Generating world...")
            generator = WorldGenerator(config)
            self.overworld_map = generator.generate()
            
            # Initialize time system
            self.time_system = TimeSystem()
            
            # Discover POIs near starting location (within sight radius)
            # Use the same config we used for generation
            start_x, start_y = self.overworld_map.get_player_position()
            nearby_pois = self.overworld_map.get_pois_in_range(start_x, start_y, radius=config.sight_radius)
            for poi in nearby_pois:
                poi.discover()
            
            # Initialize roaming parties
            if self.overworld_map.party_manager is not None:
                player_level = getattr(self.hero_stats, "level", 1) if hasattr(self, "hero_stats") else 1
                print(f"Initializing parties at player position ({start_x}, {start_y}), level {player_level}")
                self.overworld_map.party_manager.initial_spawn(
                    count=30,  # Increased initial party count
                    player_level=player_level,
                    player_position=(start_x, start_y),
                )
                all_parties = self.overworld_map.party_manager.get_all_parties()
                print(f"Total parties after initialization: {len(all_parties)}")
                if len(all_parties) == 0:
                    print("WARNING: No parties spawned! Check spawn logic.")
            
            print(f"Overworld initialized! Found {len(nearby_pois)} nearby POIs")
            
        except Exception as e:
            print("=" * 80)
            print(f"CRITICAL ERROR initializing overworld: {e}")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            print("=" * 80)
            # Fallback: create a minimal overworld or handle error gracefully
            self.overworld_map = None
            self.time_system = None
            print("Overworld initialization failed - game may not work correctly")
            print("Please check the error message above and report it if this persists.")

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
    
    def enter_overworld_mode(self) -> None:
        """Switch to overworld mode."""
        prev = getattr(self, "mode", None)
        self.mode = GameMode.OVERWORLD
        self.active_screen = None
        if telemetry is not None:
            telemetry.log("mode_change", frm=prev, to=self.mode)
    
    def enter_poi(self, poi: "PointOfInterest") -> None:
        """
        Enter a Point of Interest.
        
        Args:
            poi: The POI to enter
        """
        if poi.can_enter(self):
            poi.enter(self)
    
    def exit_poi(self) -> None:
        """Exit the current POI and return to overworld."""
        if self.current_poi is not None:
            self.current_poi.exit(self)

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
        self.ui_screen_manager.toggle_inventory_overlay(self)

    def equip_item_for_inventory_focus(self, item_id: str) -> None:
        """
        Equip the given item on whichever character the inventory overlay
        is currently focusing on.

        - Focus index 0: hero (uses self.inventory.equip).
        - Focus index 1..N: companions in self.party order (uses their
          per-companion equipment + stat recomputation).
        """
        self.last_message = EquipmentManager.equip_item_for_character(
            game=self,
            item_id=item_id,
            focus_index=self.inventory_focus_index,
        )

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
        return self.ui_screen_manager.get_available_screens(self)
    
    def switch_to_screen(self, screen_name: str) -> None:
        """Switch to a different full-screen UI."""
        self.ui_screen_manager.switch_to_screen(self, screen_name)
    
    def cycle_to_next_screen(self, direction: int = 1) -> None:
        """Cycle to next/previous available screen. direction: 1 for next, -1 for previous."""
        self.ui_screen_manager.cycle_to_next_screen(self, direction)

    def toggle_character_sheet_overlay(self) -> None:
        """Toggle character sheet overlay and manage its active screen."""
        self.ui_screen_manager.toggle_character_sheet_overlay(self)

    def toggle_skill_screen(self) -> None:
        """Toggle skill screen overlay and manage its active screen."""
        self.ui_screen_manager.toggle_skill_screen(self)
    
    def toggle_quest_screen(self) -> None:
        """Toggle quest screen overlay and manage its active screen."""
        self.ui_screen_manager.toggle_quest_screen(self)

    def toggle_battle_log_overlay(self) -> None:
        """Toggle last battle log overlay ONLY if we actually have one."""
        self.ui_screen_manager.toggle_battle_log_overlay(self)

    def toggle_exploration_log_overlay(self) -> None:
        """Toggle the exploration log overlay showing recent messages in exploration mode."""
        self.ui_screen_manager.toggle_exploration_log_overlay(self)

    def is_overlay_open(self) -> bool:
        """Return True if a major overlay (inventory, character sheet, skill screen) is open."""
        return self.ui_screen_manager.is_overlay_open()

    def cycle_character_sheet_focus(self, direction: int) -> None:
        """Cycle which character the character sheet is focusing on."""
        self.ui_screen_manager.cycle_character_sheet_focus(self, direction)

    def cycle_inventory_focus(self, direction: int) -> None:
        """Cycle which character the inventory overlay is focusing on."""
        self.ui_screen_manager.cycle_inventory_focus(self, direction)

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
        self.camera_manager.update_fov(
            player=self.player,
            current_map=self.current_map,
            debug_reveal_map=getattr(self, "debug_reveal_map", False),
        )

    # ------------------------------------------------------------------
    # Camera / zoom helpers
    # ------------------------------------------------------------------

    @property
    def zoom(self) -> float:
        """Current zoom scale for the exploration camera."""
        return self.camera_manager.zoom
    
    @property
    def overworld_zoom(self) -> float:
        """Current zoom scale for the overworld map."""
        return self.camera_manager.overworld_zoom
    
    def _center_camera_on_player(self) -> None:
        """Center the camera around the player in world space before clamping."""
        self.camera_manager.center_camera_on_player(self.player, self.current_map)

    def _clamp_camera_to_map(self) -> None:
        """Clamp the camera so it never shows outside the current map."""
        self.camera_manager.clamp_camera_to_map(self.current_map)

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

        # Get or generate the floor using FloorManager
        game_map, newly_created = self.floor_manager.get_or_generate_floor(floor_index)

        # From now on self.current_map is a GameMap, not a tuple
        self.current_map = game_map

        # Spawn enemies / events / chests / merchants only once per floor
        if newly_created:
            spawn_all_entities_for_floor(self, game_map, floor_index)

        # Calculate spawn position using FloorManager
        spawn_x, spawn_y = self.floor_manager.calculate_spawn_position(
            game_map, from_direction, player_width, player_height
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

        # Check if we're trying to go up from floor 1 (return to overworld)
        if delta < 0 and self.floor == 1:
            # Going up from first floor - confirm return to overworld
            self.pending_overworld_confirmation = True
            self.confirmation_message = "Return to the overworld? (Y/N)"
            self.confirmation_action = lambda: self._return_to_overworld_from_dungeon()
            return

        # Check if we're trying to go down from the last floor (return to overworld)
        if delta > 0 and self.current_poi is not None:
            # Check if this is a dungeon POI with floor_count
            from world.poi.types import DungeonPOI
            if isinstance(self.current_poi, DungeonPOI):
                if self.floor == self.current_poi.floor_count:
                    # On the last floor, going down means return to overworld
                    self.pending_overworld_confirmation = True
                    self.confirmation_message = "Return to the overworld? (Y/N)"
                    self.confirmation_action = lambda: self._return_to_overworld_from_dungeon()
                    return

        # Calculate new floor using FloorManager
        new_floor = self.floor_manager.change_floor(delta)
        if new_floor <= 0:
            self.last_message = "You cannot go any higher."
            return

        # Change floor and spawn appropriately on the new floor
        self.floor = new_floor
        self.load_floor(self.floor, from_direction=direction)
        self.last_message = f"You travel to floor {self.floor}."
    
    def _return_to_overworld_from_dungeon(self) -> None:
        """Return to overworld from the dungeon."""
        if self.current_poi is not None:
            self.exit_poi()
            self.last_message = "You return to the overworld."
        else:
            # Fallback if no POI (shouldn't happen, but be safe)
            self.enter_overworld_mode()
            self.last_message = "You return to the overworld."

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

        # Build encounter group using BattleOrchestrator
        encounter_enemies = BattleOrchestrator.build_encounter_group(
            trigger_enemy=enemy,
            game_map=self.current_map,
            player=self.player,
            max_group_size=6,
            radius=TILE_SIZE * 5,
        )

        # Remove all encounter enemies from the map so they can't be re-used
        for e in encounter_enemies:
            try:
                self.current_map.entities.remove(e)
            except ValueError:
                pass

        # Calculate XP for this encounter using BattleOrchestrator
        self.pending_battle_xp = BattleOrchestrator.calculate_encounter_xp(encounter_enemies)

        if telemetry is not None:
            telemetry.log(
                "battle_start",
                floor=getattr(self, "floor", None),
                enemy_count=len(encounter_enemies),
                xp_total=int(self.pending_battle_xp),
            )

        # Create battle scene with the entire group + current party.
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
        return BattleOrchestrator.calculate_battle_rewards(
            floor=self.floor,
            hero_stats=self.hero_stats,
            inventory=self.inventory,
        )

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
        from ..scenes.pause_menu import PauseMenuScene, OptionsMenuScene
        from ..scenes.save_menu import SaveMenuScene
        from ..utils.save_system import save_game, load_game
        
        # Draw current game state first (so it's visible behind pause overlay)
        if self.mode == GameMode.OVERWORLD:
            self.draw_overworld()
        elif self.mode == GameMode.EXPLORATION:
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
            from ..scenes.resolution_menu import ResolutionMenuScene
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
        
        # Update tooltip system
        tooltip = getattr(self, "tooltip", None)
        if tooltip:
            mouse_pos = pygame.mouse.get_pos()
            tooltip.update(dt, mouse_pos, tooltip.hover_target)
        
        if self.mode == GameMode.OVERWORLD:
            # Overworld updates
            if hasattr(self, "overworld"):
                self.overworld.update(dt)
            
            # Update tooltip (but don't set hover target - overworld HUD handles it)
            if hasattr(self, "tooltip") and self.tooltip:
                mouse_pos = pygame.mouse.get_pos()
                # Only update mouse position, hover detection is done in draw
                self.tooltip.mouse_pos = mouse_pos
        
        elif self.mode == GameMode.EXPLORATION:
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
        
        # Debug console toggle (F12 or ~)
        if event.type == pygame.KEYDOWN and (event.key == pygame.K_F12 or event.key == pygame.K_BACKQUOTE):
            if self.debug_console:
                self.debug_console.toggle()
            return
        
        # Global save/load game
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F5:
                # Quick save to slot 1
                from ..utils.save_system import save_game
                if save_game(self, slot=1):
                    self.add_message("Game saved to slot 1!")
                else:
                    self.add_message("Failed to save game.")
                return
            elif event.key == pygame.K_F6:
                # Open save menu
                from ..scenes.save_menu import SaveMenuScene
                from ..utils.save_system import save_game
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
                from ..scenes.save_menu import SaveMenuScene
                from ..utils.save_system import load_game, list_saves
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

        # Confirmation dialog handling (has priority when active)
        if self.pending_overworld_confirmation:
            if event.type == pygame.KEYDOWN:
                input_manager = getattr(self, "input_manager", None)
                if input_manager is not None:
                    if input_manager.event_matches_action(InputAction.CONFIRM, event):
                        # Y or Enter - confirm
                        if self.confirmation_action is not None:
                            self.confirmation_action()
                        self.pending_overworld_confirmation = False
                        self.confirmation_message = ""
                        self.confirmation_action = None
                        return
                    elif input_manager.event_matches_action(InputAction.CANCEL, event):
                        # N or Escape - cancel
                        self.pending_overworld_confirmation = False
                        self.confirmation_message = ""
                        self.confirmation_action = None
                        self.last_message = "Stay in the dungeon."
                        return
                else:
                    # Fallback: raw key handling
                    if event.key == pygame.K_y or event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # Y or Enter - confirm
                        if self.confirmation_action is not None:
                            self.confirmation_action()
                        self.pending_overworld_confirmation = False
                        self.confirmation_message = ""
                        self.confirmation_action = None
                        return
                    elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                        # N or Escape - cancel
                        self.pending_overworld_confirmation = False
                        self.confirmation_message = ""
                        self.confirmation_action = None
                        self.last_message = "Stay in the dungeon."
                        return
            # Don't process other events while confirmation is pending
            return
        
        # Debug console input handling (has priority when visible)
        if self.debug_console and self.debug_console.is_visible():
            if self.debug_console.handle_event(event, game=self):
                return  # Event consumed by debug console
        
        # Mode-specific handling.
        if self.mode == GameMode.OVERWORLD:
            # Handle mouse wheel for zoom
            if event.type == pygame.MOUSEWHEEL and hasattr(self, "overworld"):
                self.overworld.handle_mouse_wheel(event)
                return
            
            # If a modal screen is active, route input to it
            if getattr(self, "active_screen", None) is not None:
                self.active_screen.handle_event(self, event)
            elif hasattr(self, "overworld"):
                self.overworld.handle_event(event)
        
        elif self.mode == GameMode.EXPLORATION:
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
        if self.mode == GameMode.OVERWORLD:
            self.draw_overworld()
        elif self.mode == GameMode.EXPLORATION:
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
        
        # Debug console (drawn on top of everything, needs clock from main loop)
        # Note: Clock is passed via a temporary attribute set in main loop
        if self.debug_console and hasattr(self, '_debug_clock'):
            self.debug_console.draw(game=self, clock=self._debug_clock)
        
        # Draw confirmation dialog if pending (always on top)
        if self.pending_overworld_confirmation:
            self._draw_confirmation_dialog()

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

    def draw_overworld(self) -> None:
        """Draw the overworld map."""
        from ui.overworld import draw_overworld
        draw_overworld(self)
    
    def draw_battle(self) -> None:
        if self.battle_scene is None:
            return

        self.screen.fill(COLOR_BG)
        # Pass the Game instance so the battle scene can read input bindings
        self.battle_scene.draw(self.screen, self)
        
        # Debug console (drawn on top of everything)
        if self.debug_console:
            self.debug_console.draw(game=self, clock=None)  # Clock passed from main loop
        # Note: Don't call pygame.display.flip() here - the main draw() method handles flipping
        # after all overlays are drawn to prevent flickering
    
    def _draw_confirmation_dialog(self) -> None:
        """Draw the confirmation dialog overlay."""
        screen = self.screen
        screen_w, screen_h = screen.get_size()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark overlay with transparency
        screen.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_width = 500
        dialog_height = 220
        dialog_x = (screen_w - dialog_width) // 2
        dialog_y = (screen_h - dialog_height) // 2
        
        # Draw dialog background
        dialog_bg = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(screen, (40, 40, 60), dialog_bg)
        pygame.draw.rect(screen, (255, 255, 255), dialog_bg, 2)
        
        # Draw message text
        font = self.ui_font
        font_title = pygame.font.SysFont("consolas", 24)
        
        # Title
        title_text = font_title.render("Confirmation", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 40))
        screen.blit(title_text, title_rect)
        
        # Message
        message_text = font.render(self.confirmation_message, True, (255, 255, 255))
        message_rect = message_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 100))
        screen.blit(message_text, message_rect)
        
        # Instructions
        instruction_text = font.render("Press Y/Enter to confirm, N/Escape to cancel", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 160))
        screen.blit(instruction_text, instruction_rect)
        
        # Additional hint about controls
        hint_text = font.render("Use E on stairs to go down, Q to go up", True, (150, 150, 150))
        hint_rect = hint_text.get_rect(center=(dialog_x + dialog_width // 2, dialog_y + 180))
        screen.blit(hint_text, hint_rect)

