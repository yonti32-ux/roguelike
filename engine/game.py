import random
import math
from typing import Optional, List

import pygame

from settings import COLOR_BG, TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from world.mapgen import generate_floor
from world.game_map import GameMap
from world.entities import Player, Enemy, Merchant
from .battle_scene import BattleScene
from .input import create_default_input_manager

from .exploration import ExplorationController
from .cheats import handle_cheat_key
from systems.progression import HeroStats
from systems.party import (
    CompanionState,
    default_party_states_for_class,
    get_companion,
    init_companion_stats,
    recalc_companion_stats_for_level,
)

from systems import perks as perk_system
from systems.inventory import Inventory, get_item_def
from systems.loot import roll_battle_loot
from systems.enemies import (
    choose_archetype_for_floor,
    compute_scaled_stats,
    choose_pack_for_floor,
    get_archetype,
)

from ui.hud import (
    draw_exploration_ui,
    draw_inventory_overlay,
)
from ui.screens import (
    BaseScreen,
    InventoryScreen,
    CharacterSheetScreen,
    ShopScreen,
)
from .perk_selection_scene import PerkSelectionScene

from systems.events import EVENTS  # registry of map events
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

        # Party / companions: runtime CompanionState objects
        self.party: List[CompanionState] = []

        # Floor index (current dungeon depth)
        self.floor: int = 1

        # Active map and player
        self.current_map: Optional[GameMap] = None
        self.player: Optional[Player] = None

        # Store generated floors so layouts/enemies persist
        self.floors: dict[int, GameMap] = {}

        # Simple UI font
        self.ui_font = pygame.font.SysFont("consolas", 20)

        # --- Last battle log (for viewing in exploration) ---
        self.last_battle_log: List[str] = []
        self.show_battle_log: bool = False

        # --- Character sheet overlay ---
        self.show_character_sheet: bool = False

        # Which character the sheet is currently focusing:
        # 0 = hero, 1..N = companions in self.party order.
        self.character_sheet_focus_index: int = 0

        # Which character the inventory overlay is currently focusing:
        # 0 = hero, 1..N = companions in self.party order.
        self.inventory_focus_index: int = 0

        # Inventory list paging / scrolling
        self.inventory_page_size: int = 20  # More items visible in fullscreen
        self.inventory_scroll_offset: int = 0

        # --- Exploration log overlay (multi-line message history) ---
        self.show_exploration_log: bool = False

        # Inventory / character sheet / shop overlays as screen objects.
        self.inventory_screen = InventoryScreen()
        self.character_sheet_screen = CharacterSheetScreen()
        self.shop_screen = ShopScreen()

        # Currently active full-screen UI overlay (if any).
        # Used for perk choices, inventory, character sheet, shop, etc.
        self.active_screen: Optional[BaseScreen] = None

        # Mode handling
        self.mode: str = GameMode.EXPLORATION
        self.battle_scene: Optional[BattleScene] = None

        # XP from the current battle (set when we start it)
        self.pending_battle_xp: int = 0

        # Exploration message history + backing store for last_message
        self.exploration_log: List[str] = []
        self.exploration_log_max: int = 60
        self._last_message: str = ""

        # Short grace window after battles where enemies don't auto-engage
        self.post_battle_grace: float = 0.0

        # Floor intro pause: enemies wait until the player makes the first move
        self.awaiting_floor_start: bool = True

        # Camera & zoom (exploration view)
        self.camera_x: float = 0.0
        self.camera_y: float = 0.0
        self.zoom_levels = [0.75, 1.0, 1.25]
        self.zoom_index: int = 1  # start at 1.0x

        # Debug flags
        self.debug_reveal_map: bool = False

        # Display mode
        self.fullscreen: bool = False

        # Initialize hero stats, perks, items and gold for the chosen class
        self._init_hero_for_class(hero_class_id)

        # Exploration controller (handles map movement & interactions)
        self.exploration = ExplorationController(self)

        # Load initial floor
        self.load_floor(self.floor, from_direction=None)

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
                self.apply_hero_stats_to_player(full_heal=False)
            return

        comp_idx = focus_index - 1
        if comp_idx < 0 or comp_idx >= len(party_list):
            # Defensive fallback: just treat as hero equip.
            msg = self.inventory.equip(item_id)
            self.last_message = msg
            if self.player is not None:
                self.apply_hero_stats_to_player(full_heal=False)
            return

        comp_state = party_list[comp_idx]
        if not isinstance(comp_state, CompanionState):
            # Shouldn't happen, but don't crash the game if it does.
            msg = self.inventory.equip(item_id)
            self.last_message = msg
            if self.player is not None:
                self.apply_hero_stats_to_player(full_heal=False)
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

    def get_available_screens(self) -> List[str]:
        """Get list of available screen names (shop only if vendor nearby)."""
        screens = ["inventory", "character"]
        if getattr(self, "show_shop", False):
            screens.append("shop")
        return screens
    
    def switch_to_screen(self, screen_name: str) -> None:
        """Switch to a different full-screen UI."""
        # Close all screen flags
        self.show_inventory = False
        self.show_character_sheet = False
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
        Return True if a major overlay (inventory, character sheet) is open.
        Used to pause exploration updates.
        """
        return self.show_inventory or self.show_character_sheet

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
        """
        Latest message shown in the bottom exploration band.
        Also mirrors the final line added to the exploration log.
        """
        return getattr(self, "_last_message", "")

    @last_message.setter
    def last_message(self, value: str) -> None:
        """
        Set the latest message and append it to the exploration log.

        - Accepts any value, coerced to string.
        - Supports multi-line strings; each non-empty line becomes
          a distinct log entry.
        - The final line becomes the visible bottom-band message.
        """
        # Normalise to string
        if value is None:
            raw = ""
        else:
            raw = str(value)

        # Normalise newlines and split into lines
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]

        # Always update the backing field; empty means "no message"
        if not lines:
            self._last_message = ""
            return

        # Ensure log structures exist
        if not hasattr(self, "exploration_log"):
            self.exploration_log = []
        if not hasattr(self, "exploration_log_max"):
            self.exploration_log_max = 60

        # Append lines to history
        self.exploration_log.extend(lines)

        # Clamp log size
        max_len = max(1, int(self.exploration_log_max))
        if len(self.exploration_log) > max_len:
            self.exploration_log = self.exploration_log[-max_len:]

        # Visible "last message" is the final line
        self._last_message = lines[-1]

    def add_message(self, value: str) -> None:
        """
        Backwards-compatible helper for adding exploration messages.

        - Wraps setting `last_message` so older code that used `add_message`
          continues to work.
        - Supports multi-line strings just like assigning to `last_message`
          directly (each non-empty line becomes its own log entry).
        """
        self.last_message = value

    # ------------------------------------------------------------------
    # Hero stats helpers
    # ------------------------------------------------------------------

    def _init_hero_for_class(self, hero_class_id: str) -> None:
        from systems.classes import all_classes  # local import to avoid cycles

        class_def = None
        for cls in all_classes():
            if cls.id == hero_class_id:
                class_def = cls
                break
        if class_def is None:
            raise ValueError(f"Unknown hero class: {hero_class_id}")

        # Fresh hero stats
        self.hero_stats = HeroStats()
        self.hero_stats.apply_class(class_def)
        # Remember which class this hero is using for restarts / UI
        self.hero_stats.hero_class_id = class_def.id

        # Fresh inventory and starting items
        self.inventory = Inventory()
        for item_id in class_def.starting_items:
            self.inventory.add_item(item_id)

        # Auto-equip one item per slot if available
        for slot in ("weapon", "armor", "trinket"):
            for item_id in list(self.inventory.items):
                item_def = get_item_def(item_id)
                if item_def is not None and item_def.slot == slot:
                    self.inventory.equip(item_id)
                    break

        # Initialize party as runtime CompanionState objects.
        self.party = default_party_states_for_class(
            class_def.id,
            hero_level=self.hero_stats.level,
        )

        # Initialise each companion's stats based on its template and level.
        for comp_state in self.party:
            if not isinstance(comp_state, CompanionState):
                continue
            try:
                template = get_companion(comp_state.template_id)
            except Exception:
                continue
            init_companion_stats(comp_state, template)

    def apply_hero_stats_to_player(self, full_heal: bool = False) -> None:
        """
        Sync hero meta stats (HeroStats) to the in-world Player entity.

        Applies:
        - max hp
        - attack / defense
        - crit / dodge chance
        - status resistance
        - move speed
        """
        if self.player is None or self.hero_stats is None:
            return

        hs = self.hero_stats
        base = getattr(hs, "base_stats", None)

        # ---- Max HP ----
        max_hp = getattr(hs, "max_hp", None)
        if max_hp is None and base is not None:
            max_hp = getattr(base, "max_hp", getattr(base, "hp", None))
        if max_hp is None:
            max_hp = getattr(self.player, "max_hp", 10)
        self.player.max_hp = max_hp
        if full_heal:
            self.player.hp = max_hp

        # ---- Attack / Attack Power ----
        attack_val = getattr(hs, "attack_power", None)
        if attack_val is None:
            attack_val = getattr(hs, "attack", None)
        if attack_val is None and base is not None:
            attack_val = getattr(base, "attack", getattr(base, "atk", None))
        if attack_val is None:
            attack_val = getattr(self.player, "attack", 1)

        # keep both names in sync so exploration & battle use same value
        self.player.attack = attack_val
        self.player.attack_power = attack_val

        # ---- Defense ----
        defense_val = getattr(hs, "defense", None)
        if defense_val is None and base is not None:
            defense_val = getattr(base, "defense", getattr(base, "def_", None))
        if defense_val is None:
            defense_val = getattr(self.player, "defense", 0)
        self.player.defense = defense_val

        # ---- Derived stats ----
        self.player.crit_chance = getattr(hs, "crit_chance",
                                          getattr(hs, "crit", 0.0))
        self.player.dodge_chance = getattr(hs, "dodge_chance",
                                           getattr(hs, "dodge", 0.0))
        self.player.status_resist = getattr(hs, "status_resist", 0.0)

        # --- New: resource pools from HeroStats (max stamina / mana) ---
        # HeroStats already exposes max_stamina / max_mana properties.
        max_sta = max(0, int(getattr(hs, "max_stamina", 0)))
        max_mana = max(0, int(getattr(hs, "max_mana", 0)))

        self.player.max_stamina = max_sta
        self.player.max_mana = max_mana
        # ---- Move speed ----
        move_speed = getattr(hs, "move_speed",
                             getattr(hs, "speed",
                                     getattr(self.player, "speed", 200.0)))
        self.player.speed = move_speed

        # Mirror learned perks onto the Player entity so BattleScene can
        # grant skills based on perks.
        perks_list = getattr(hs, "perks", None)
        if perks_list is not None:
            setattr(self.player, "perks", list(perks_list))

    def _sync_companions_to_hero_progression(self) -> None:
        """
        Keep companions in lockstep with the hero's level/xp for now.

        Later we can give companions their own independent progression.
        """
        if not getattr(self, "party", None):
            return

        hero_level = getattr(self.hero_stats, "level", 1)
        hero_xp = getattr(self.hero_stats, "xp", 0)

        for comp_state in self.party:
            # Be defensive in case of legacy data
            if not hasattr(comp_state, "level"):
                continue
            comp_state.level = hero_level
            comp_state.xp = hero_xp

    def _grant_xp_to_companions(self, amount: int, leveled_indices: Optional[List[int]] = None) -> List[str]:
        """
        Grant XP to all recruited companions and recalc their stats.

        This keeps companion progression independent from the hero: they share
        XP gains, but track their own levels.

        Args:
            amount: XP amount to grant
            leveled_indices: Optional list to append indices of companions that leveled up

        Returns a list of log strings about companion level-ups.
        """
        party_list = getattr(self, "party", None) or []
        amount = int(amount)

        if amount <= 0 or not party_list:
            return []

        messages: List[str] = []

        for idx, comp_state in enumerate(party_list):
            # Only handle real CompanionState objects
            if not isinstance(comp_state, CompanionState):
                continue

            # Skip companions that aren't recruited or shouldn't scale with hero XP.
            # If the attributes don't exist yet, we treat them as True so old saves still work.
            if not getattr(comp_state, "recruited", True):
                continue
            if not getattr(comp_state, "scales_with_hero", True):
                continue

            grant = getattr(comp_state, "grant_xp", None)
            if not callable(grant):
                continue

            old_level = getattr(comp_state, "level", 1)
            old_max_hp = getattr(comp_state, "max_hp", 0)
            # CompanionState normally uses attack_power; fall back to attack if needed.
            old_attack = getattr(comp_state, "attack_power", getattr(comp_state, "attack", 0))

            try:
                levels_gained = grant(amount)
            except Exception:
                # Don't let one weird companion break rewards.
                continue

            # No actual level up? Skip.
            new_level = getattr(comp_state, "level", old_level)
            if levels_gained <= 0 or new_level <= old_level:
                continue

            # Track that this companion leveled up
            if leveled_indices is not None:
                leveled_indices.append(idx)

            # Recompute stats from template + level + perks
            template = None
            try:
                template = get_companion(comp_state.template_id)
            except Exception:
                pass
            if template is None:
                continue

            recalc_companion_stats_for_level(comp_state, template)

            # Note: Perk selection is handled after all level-ups via run_perk_selection()

            # Compose a quick summary line with stat gains
            new_max_hp = getattr(comp_state, "max_hp", old_max_hp)
            new_attack = getattr(comp_state, "attack_power", getattr(comp_state, "attack", old_attack))

            delta_hp = new_max_hp - old_max_hp
            delta_attack = new_attack - old_attack

            # Figure out a nice display name for logging
            display_name = getattr(comp_state, "name_override", None)
            if not display_name:
                display_name = getattr(comp_state, "name", None)
            if not display_name:
                # Fall back to the companion template name if available
                try:
                    template_for_name = get_companion(comp_state.template_id)
                except Exception:
                    template_for_name = None
                if template_for_name is not None:
                    display_name = getattr(template_for_name, "name", None)
            if not display_name:
                display_name = f"Companion {idx + 1}"

            parts: List[str] = [f"{display_name} reaches level {comp_state.level}"]

            bonuses: List[str] = []
            if delta_hp > 0:
                bonuses.append(f"+{delta_hp} HP")
            if delta_attack > 0:
                bonuses.append(f"+{delta_attack} ATK")

            if bonuses:
                parts.append("(" + ", ".join(bonuses) + ")")

            messages.append(" ".join(parts))

        return messages

    def gain_xp_from_event(self, amount: int) -> None:
        """Grant XP from a map event, showing messages + perk selection scene."""
        if amount <= 0:
            return

        old_level = self.hero_stats.level
        messages = self.hero_stats.grant_xp(amount)
        for msg in messages:
            self.add_message(msg)

        new_level = self.hero_stats.level
        hero_leveled_up = new_level > old_level
        
        # Track perk selection entries
        perk_entries: List[tuple[str, Optional[int]]] = []
        if hero_leveled_up:
            perk_entries.append(("hero", None))

        # Companions share the same XP amount, but track their own levels
        # Track which companions leveled up
        leveled_companions: List[int] = []
        companion_msgs = self._grant_xp_to_companions(amount, leveled_companions)
        for msg in companion_msgs:
            self.add_message(msg)
        
        # Add leveled companions to perk entries
        for idx in leveled_companions:
            perk_entries.append(("companion", idx))

        # On level-up from an event, full-heal the hero immediately.
        if hero_leveled_up and self.player is not None:
            self.apply_hero_stats_to_player(full_heal=False)
            self.player.hp = self.hero_stats.max_hp
            self.add_message("You feel completely renewed!")

        # Run perk selection scene if anyone leveled up
        if perk_entries:
            self.run_perk_selection(perk_entries)

        return messages

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
            self.spawn_enemies_for_floor(game_map, floor_index)
            self.spawn_events_for_floor(game_map, floor_index)
            self.spawn_chests_for_floor(game_map, floor_index)
            self.spawn_merchants_for_floor(game_map, floor_index)

            # Debug/testing: always ensure at least one merchant on floor 3
            self._ensure_debug_merchant_on_floor_three(game_map, floor_index)

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
        self.apply_hero_stats_to_player(full_heal=True)
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

    def _choose_enemy_type_for_floor(self, floor_index: int) -> str:
        """
        Very simple enemy naming based on floor depth.
        Used only for the battle UI group label.
        """
        if floor_index <= 2:
            pool = ["Goblin", "Bandit", "Cultist"]
        elif floor_index <= 4:
            pool = ["Ghoul", "Orc Raider", "Dark Acolyte"]
        else:
            pool = ["Dread Knight", "Voidspawn", "Elite Cultist"]

        return random.choice(pool)

    def spawn_enemies_for_floor(self, game_map: GameMap, floor_index: int) -> None:
        """
        Spawn enemies on this floor, using room-aware logic, enemy archetypes,
        and *packs* (themed groups that spawn together).

        Room-aware logic:
        - Never spawn in the 'start' room.
        - Prefer lair rooms for extra density / heavier packs.
        - Fill remaining quota from other rooms and corridors.
        - Keep a safe radius around the main spawn.
        """
        enemy_width = 24
        enemy_height = 24

        up = game_map.up_stairs
        down = game_map.down_stairs

        # Safe radius (in tiles) around the main spawn (usually up stairs)
        safe_radius_tiles = 3
        if up is not None:
            safe_cx, safe_cy = up
        else:
            safe_cx = game_map.width // 2
            safe_cy = game_map.height // 2

        lair_tiles: List[tuple[int, int]] = []
        room_tiles: List[tuple[int, int]] = []
        corridor_tiles: List[tuple[int, int]] = []

        for ty in range(game_map.height):
            for tx in range(game_map.width):
                if not game_map.is_walkable_tile(tx, ty):
                    continue
                if up is not None and (tx, ty) == up:
                    continue
                if down is not None and (tx, ty) == down:
                    continue

                # Keep a small safe bubble around spawn
                dx = tx - safe_cx
                dy = ty - safe_cy
                if dx * dx + dy * dy <= safe_radius_tiles * safe_radius_tiles:
                    continue

                room = game_map.get_room_at(tx, ty) if hasattr(game_map, "get_room_at") else None
                if room is None:
                    # Corridors / junctions
                    corridor_tiles.append((tx, ty))
                else:
                    tag = getattr(room, "tag", "generic")
                    if tag == "start":
                        # Extra safety: don't spawn in the start room at all
                        continue
                    elif tag == "lair":
                        lair_tiles.append((tx, ty))
                    else:
                        room_tiles.append((tx, ty))

        if not (lair_tiles or room_tiles or corridor_tiles):
            return

        random.shuffle(lair_tiles)
        random.shuffle(room_tiles)
        random.shuffle(corridor_tiles)

        # --- Decide roughly how many enemies we want on this floor ---------
        base_desired = 2 + floor_index

        screen_w, screen_h = self.screen.get_size()
        base_tiles_x = screen_w // TILE_SIZE
        base_tiles_y = screen_h // TILE_SIZE
        base_area = max(1, base_tiles_x * base_tiles_y)

        floor_area = game_map.width * game_map.height
        area_ratio = floor_area / base_area
        area_factor = math.sqrt(area_ratio) if area_ratio > 0 else 1.0
        # Keep in a reasonable band so things don't get absurd
        area_factor = max(0.75, min(area_factor, 1.8))

        target_enemies = int(round(base_desired * area_factor))
        # Soft clamp overall difficulty
        target_enemies = min(10, max(2, target_enemies))

        # We'll spawn enemies in *packs*. Each pack is usually 2–3 enemies.
        approx_pack_size = 2.2
        desired_packs = max(1, int(round(target_enemies / approx_pack_size)))

        all_candidate_tiles = lair_tiles + room_tiles + corridor_tiles
        if not all_candidate_tiles:
            return

        desired_packs = min(desired_packs, len(all_candidate_tiles))

        chosen_anchors: List[tuple[int, int]] = []
        remaining_packs = desired_packs

        # Fill roughly half of the pack anchors from lair rooms (if any)
        if lair_tiles and remaining_packs > 0:
            lair_target = min(len(lair_tiles), max(1, remaining_packs // 2))
            chosen_anchors.extend(lair_tiles[:lair_target])
            remaining_packs -= lair_target

        # Then normal rooms
        if room_tiles and remaining_packs > 0:
            room_target = min(len(room_tiles), remaining_packs)
            chosen_anchors.extend(room_tiles[:room_target])
            remaining_packs -= room_target

        # Whatever anchors remain come from corridors
        if corridor_tiles and remaining_packs > 0:
            corr_target = min(len(corridor_tiles), remaining_packs)
            chosen_anchors.extend(corridor_tiles[:corr_target])
            remaining_packs -= corr_target

        if not chosen_anchors:
            return

        # Track which tiles already have an enemy so packs don't overlap
        occupied_enemy_tiles: set[tuple[int, int]] = set()
        spawned_total = 0
        # Hard cap so big floors don't turn into bullet hell
        max_total_enemies = min(target_enemies + 3, 12)

        def can_use_tile(tx: int, ty: int) -> bool:
            if (tx, ty) in occupied_enemy_tiles:
                return False
            if up is not None and (tx, ty) == up:
                return False
            if down is not None and (tx, ty) == down:
                return False
            if not game_map.is_walkable_tile(tx, ty):
                return False
            dx_ = tx - safe_cx
            dy_ = ty - safe_cy
            if dx_ * dx_ + dy_ * dy_ <= safe_radius_tiles * safe_radius_tiles:
                return False
            return True

        for anchor_tx, anchor_ty in chosen_anchors:
            if spawned_total >= max_total_enemies:
                break

            room = game_map.get_room_at(anchor_tx, anchor_ty) if hasattr(game_map, "get_room_at") else None
            room_tag = getattr(room, "tag", "generic") if room is not None else None

            # --- Pick a pack template for this anchor ----------------------
            try:
                pack = choose_pack_for_floor(floor_index, room_tag=room_tag)
                member_arch_ids = list(pack.member_arch_ids)
            except Exception:
                # Very defensive fallback: just pick a single archetype
                arch = choose_archetype_for_floor(floor_index, room_tag=room_tag)
                member_arch_ids = [arch.id]

            # Candidate spawn tiles: anchor + its 8 neighbors (3×3 cluster)
            candidate_tiles: List[tuple[int, int]] = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    tx = anchor_tx + dx
                    ty = anchor_ty + dy
                    if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                        candidate_tiles.append((tx, ty))
            random.shuffle(candidate_tiles)

            for arch_id in member_arch_ids:
                if spawned_total >= max_total_enemies:
                    break

                # Find a nearby free tile for this pack member
                spawn_tx: Optional[int] = None
                spawn_ty: Optional[int] = None
                for tx, ty in candidate_tiles:
                    if can_use_tile(tx, ty):
                        spawn_tx, spawn_ty = tx, ty
                        break

                if spawn_tx is None or spawn_ty is None:
                    # No more room around this anchor
                    continue

                # Look up archetype; if missing, fall back to generic floor-based choice
                try:
                    arch = get_archetype(arch_id)
                except KeyError:
                    arch = choose_archetype_for_floor(floor_index, room_tag=room_tag)

                max_hp, attack_power, defense, xp_reward = compute_scaled_stats(arch, floor_index)

                ex, ey = game_map.center_entity_on_tile(spawn_tx, spawn_ty, enemy_width, enemy_height)
                enemy = Enemy(
                    x=ex,
                    y=ey,
                    width=enemy_width,
                    height=enemy_height,
                    # Slightly slower chase speed for nicer exploration feel
                    speed=70.0,
                )

                # Basic combat stats that BattleScene will use
                setattr(enemy, "max_hp", max_hp)
                setattr(enemy, "hp", max_hp)
                setattr(enemy, "attack_power", attack_power)
                setattr(enemy, "defense", defense)

                # XP reward and metadata
                setattr(enemy, "xp_reward", xp_reward)
                setattr(enemy, "enemy_type", arch.name)
                setattr(enemy, "archetype_id", arch.id)
                setattr(enemy, "ai_profile", arch.ai_profile)

                # Enemies block movement in exploration
                setattr(enemy, "blocks_movement", True)

                game_map.entities.append(enemy)
                occupied_enemy_tiles.add((spawn_tx, spawn_ty))
                spawned_total += 1

    def spawn_events_for_floor(self, game_map: GameMap, floor_index: int) -> None:
        """
        Spawn a few interactive event nodes (shrines, lore stones, caches).

        Room-aware logic:
        - Prefer tiles inside rooms tagged 'event'.
        - Otherwise, use generic rooms.
        - Avoid stairs, existing entities, and the spawn-safe radius.
        """
        from world.entities import EventNode  # local to avoid circulars

        if not getattr(game_map, "rooms", None):
            return

        up = game_map.up_stairs
        down = game_map.down_stairs

        # Safe radius around main spawn (usually up stairs)
        safe_radius_tiles = 3
        if up is not None:
            safe_cx, safe_cy = up
        else:
            safe_cx = game_map.width // 2
            safe_cy = game_map.height // 2

        # Tiles already occupied by entities
        occupied_tiles: set[tuple[int, int]] = set()
        for entity in getattr(game_map, "entities", []):
            if not hasattr(entity, "rect"):
                continue
            cx, cy = entity.rect.center
            tx, ty = game_map.world_to_tile(cx, cy)
            occupied_tiles.add((tx, ty))

        event_room_tiles: list[tuple[int, int]] = []
        other_room_tiles: list[tuple[int, int]] = []

        for ty in range(game_map.height):
            for tx in range(game_map.width):
                if not game_map.is_walkable_tile(tx, ty):
                    continue
                if up is not None and (tx, ty) == up:
                    continue
                if down is not None and (tx, ty) == down:
                    continue
                if (tx, ty) in occupied_tiles:
                    continue

                dx = tx - safe_cx
                dy = ty - safe_cy
                if dx * dx + dy * dy <= safe_radius_tiles * safe_radius_tiles:
                    continue

                room = game_map.get_room_at(tx, ty)
                if room is None:
                    continue  # no corridor events for now

                tag = getattr(room, "tag", "generic")
                if tag == "start":
                    continue
                if tag == "event":
                    event_room_tiles.append((tx, ty))
                else:
                    other_room_tiles.append((tx, ty))

        if not event_room_tiles and not other_room_tiles:
            return

        # 0–2 events per floor, but if we have event rooms we try for at least 1
        max_events = min(2, len(event_room_tiles) + len(other_room_tiles))
        if max_events <= 0:
            return

        min_events = 1 if event_room_tiles else 0
        event_count = random.randint(min_events, max_events)
        if event_count <= 0:
            return

        chosen_tiles: list[tuple[int, int]] = []
        remaining = event_count

        random.shuffle(event_room_tiles)
        random.shuffle(other_room_tiles)

        # First event in an 'event' room if possible
        if event_room_tiles and remaining > 0:
            chosen_tiles.append(event_room_tiles.pop(0))
            remaining -= 1

        # Remaining events in any room tiles
        pool = event_room_tiles + other_room_tiles
        random.shuffle(pool)
        chosen_tiles.extend(pool[:remaining])

        # Choose which event types are available
        available_event_ids = list(EVENTS.keys())
        if not available_event_ids:
            return

        half_tile = TILE_SIZE // 2

        for tx, ty in chosen_tiles:
            event_id = random.choice(available_event_ids)
            ex, ey = game_map.center_entity_on_tile(tx, ty, half_tile, half_tile)
            node = EventNode(
                x=ex,
                y=ey,
                width=half_tile,
                height=half_tile,
                event_id=event_id,
            )
            game_map.entities.append(node)

    def spawn_chests_for_floor(self, game_map: GameMap, floor_index: int) -> None:
        """
        Spawn a few treasure chests on walkable tiles.

        Room-aware logic:
        - Avoid stairs and the spawn-safe radius.
        - Prefer placing at least one chest in a 'treasure' room if available.
        - Other chests go into generic rooms / corridors.
        """
        from world.entities import Chest  # local import to avoid circular

        chest_width = TILE_SIZE // 2
        chest_height = TILE_SIZE // 2

        up = game_map.up_stairs
        down = game_map.down_stairs

        # Safe radius (in tiles) around main spawn (usually up stairs)
        safe_radius_tiles = 3
        if up is not None:
            safe_cx, safe_cy = up
        else:
            safe_cx = game_map.width // 2
            safe_cy = game_map.height // 2

        # Tiles already occupied by entities (so we don't stack with enemies)
        occupied_tiles: set[tuple[int, int]] = set()
        for entity in getattr(game_map, "entities", []):
            if not hasattr(entity, "rect"):
                continue
            cx, cy = entity.rect.center
            tx, ty = game_map.world_to_tile(cx, cy)
            occupied_tiles.add((tx, ty))

        treasure_tiles: List[tuple[int, int]] = []
        other_tiles: List[tuple[int, int]] = []

        for ty in range(game_map.height):
            for tx in range(game_map.width):
                if not game_map.is_walkable_tile(tx, ty):
                    continue
                if up is not None and (tx, ty) == up:
                    continue
                if down is not None and (tx, ty) == down:
                    continue
                if (tx, ty) in occupied_tiles:
                    continue

                dx = tx - safe_cx
                dy = ty - safe_cy
                if dx * dx + dy * dy <= safe_radius_tiles * safe_radius_tiles:
                    continue

                room = game_map.get_room_at(tx, ty) if hasattr(game_map, "get_room_at") else None
                if room is not None:
                    tag = getattr(room, "tag", "generic")
                    if tag == "start":
                        # No loot cluttering the start room
                        continue
                    if tag == "treasure":
                        treasure_tiles.append((tx, ty))
                        continue

                # Default bucket for generic rooms / corridors
                other_tiles.append((tx, ty))

        if not treasure_tiles and not other_tiles:
            return

        random.shuffle(treasure_tiles)
        random.shuffle(other_tiles)

        # Scale chest count with floor size:
        # 0–2 on normal floors, up to 3 on big ones.
        screen_w, screen_h = self.screen.get_size()
        base_tiles_x = screen_w // TILE_SIZE
        base_tiles_y = screen_h // TILE_SIZE
        base_area = max(1, base_tiles_x * base_tiles_y)

        floor_area = game_map.width * game_map.height
        area_ratio = floor_area / base_area
        area_factor = math.sqrt(area_ratio) if area_ratio > 0 else 1.0
        area_factor = max(0.75, min(area_factor, 1.8))

        raw_max = 2 + (1 if area_factor > 1.3 else 0)
        max_chests = min(raw_max, len(treasure_tiles) + len(other_tiles))
        if max_chests <= 0:
            return

        # If we have treasure tiles, try for at least 1 chest (1..max_chests).
        # If not, 0..max_chests like before.
        min_chests = 1 if treasure_tiles else 0
        chest_count = random.randint(min_chests, max_chests)

        if chest_count <= 0:
            return

        chosen_spots: List[tuple[int, int]] = []
        remaining = chest_count

        # First chest in treasure room if possible
        if treasure_tiles and remaining > 0:
            chosen_spots.append(treasure_tiles[0])
            remaining -= 1

        # Remaining chests go into other tiles first, then spare treasure tiles
        pool: List[tuple[int, int]] = other_tiles + treasure_tiles[1:]
        random.shuffle(pool)

        for tx, ty in pool:
            if remaining <= 0:
                break
            chosen_spots.append((tx, ty))
            remaining -= 1

        for tx, ty in chosen_spots:
            x, y = game_map.center_entity_on_tile(tx, ty, chest_width, chest_height)
            chest = Chest(x=x, y=y, width=chest_width, height=chest_height)
            # Chests do not block movement
            setattr(chest, "blocks_movement", False)
            game_map.entities.append(chest)

    def spawn_merchants_for_floor(self, game_map: GameMap, floor_index: int) -> None:
        """
        Spawn one stationary merchant in each 'shop' room, if any exist.

        Merchants:
        - Stand roughly at the room's tile centre.
        - Block movement (you walk around them).
        """
        from world.entities import Merchant  # local import to avoid circulars

        # If we don't have room metadata, we can't place shopkeepers
        if not getattr(game_map, "rooms", None):
            return

        up = game_map.up_stairs
        down = game_map.down_stairs

        # Tiles already occupied by entities (enemies, chests, events...)
        occupied_tiles: set[tuple[int, int]] = set()
        for entity in getattr(game_map, "entities", []):
            if not hasattr(entity, "rect"):
                continue
            cx, cy = entity.rect.center
            tx, ty = game_map.world_to_tile(cx, cy)
            occupied_tiles.add((tx, ty))

        # Collect all walkable tiles for each distinct shop room
        room_tiles: dict[object, list[tuple[int, int]]] = {}

        for ty in range(game_map.height):
            for tx in range(game_map.width):
                if not game_map.is_walkable_tile(tx, ty):
                    continue
                if up is not None and (tx, ty) == up:
                    continue
                if down is not None and (tx, ty) == down:
                    continue
                if (tx, ty) in occupied_tiles:
                    continue

                if not hasattr(game_map, "get_room_at"):
                    continue
                room = game_map.get_room_at(tx, ty)
                if room is None:
                    continue
                if getattr(room, "tag", "") != "shop":
                    continue

                room_tiles.setdefault(room, []).append((tx, ty))

        if not room_tiles:
            return

        merchant_w = TILE_SIZE // 2
        merchant_h = TILE_SIZE // 2

        for room, tiles in room_tiles.items():
            if not tiles:
                continue

            # Try to place merchant near the "centre" of the room's tiles
            avg_tx = sum(t[0] for t in tiles) // len(tiles)
            avg_ty = sum(t[1] for t in tiles) // len(tiles)

            candidate_tiles = [(avg_tx, avg_ty)] + tiles
            chosen_tx: Optional[int] = None
            chosen_ty: Optional[int] = None

            for tx, ty in candidate_tiles:
                if (tx, ty) in occupied_tiles:
                    continue
                chosen_tx, chosen_ty = tx, ty
                break

            if chosen_tx is None or chosen_ty is None:
                continue

            mx, my = game_map.center_entity_on_tile(
                chosen_tx,
                chosen_ty,
                merchant_w,
                merchant_h,
            )
            merchant = Merchant(
                x=mx,
                y=my,
                width=merchant_w,
                height=merchant_h,
            )
            # Merchants block movement
            merchant.blocks_movement = True

            game_map.entities.append(merchant)
            occupied_tiles.add((chosen_tx, chosen_ty))

    def _ensure_debug_merchant_on_floor_three(
        self,
        game_map: GameMap,
        floor_index: int,
    ) -> None:
        """
        Debug / testing helper:

        On floor 3, if no Merchant was spawned (e.g. no 'shop' room on that
        seed), force-spawn a single Merchant on the DOWN stairs tile.

        This guarantees a merchant for testing without affecting other floors.
        """
        if floor_index != 3:
            return

        # If there's already at least one merchant, do nothing
        for entity in getattr(game_map, "entities", []):
            if isinstance(entity, Merchant):
                return

        # Choose the down-stairs tile if possible; otherwise fall back
        if game_map.down_stairs is not None:
            tx, ty = game_map.down_stairs
        else:
            tx = game_map.width // 2
            ty = game_map.height // 2

        merchant_w = TILE_SIZE // 2
        merchant_h = TILE_SIZE // 2

        mx, my = game_map.center_entity_on_tile(
            tx,
            ty,
            merchant_w,
            merchant_h,
        )

        merchant = Merchant(
            x=mx,
            y=my,
            width=merchant_w,
            height=merchant_h,
        )
        merchant.blocks_movement = True

        game_map.entities.append(merchant)

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
        self.exploration_log = []
        self._last_message = ""
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
        self._init_hero_for_class(current_class)

        self.load_floor(self.floor, from_direction=None)

    def roll_battle_reward(self) -> List[str]:
        """
        Roll gold (or other simple rewards) after a battle.
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
                companion_msgs = self._grant_xp_to_companions(xp_reward, leveled_companions)
                if companion_msgs:
                    messages.extend(companion_msgs)
                
                # Add leveled companions to perk entries
                for idx in leveled_companions:
                    perk_entries.append(("companion", idx))

            # 2) Sync stats onto player and apply baseline healing
            if self.player is not None:
                self.apply_hero_stats_to_player(full_heal=False)

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
    # Main loop: update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
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
        # Cheats: handle global debug keys, consume the event if needed.
        if handle_cheat_key(self, event):
            return

        # Global fullscreen toggle.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
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

        # Draw an active overlay screen on top (inventory, character sheet, etc.).
        if getattr(self, "active_screen", None) is not None:
            self.active_screen.draw(self)

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

        pygame.display.flip()

