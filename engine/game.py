# engine/game.py

import random
from typing import Optional, List

import pygame

from settings import COLOR_BG, TILE_SIZE
from world.mapgen import generate_floor
from world.game_map import GameMap
from world.entities import Player, Enemy
from .battle_scene import BattleScene
from .exploration import ExplorationController
from .cheats import handle_cheat_key
from systems.progression import HeroStats
from systems import perks as perk_system
from systems.inventory import Inventory, get_item_def
from systems.loot import roll_battle_loot, roll_chest_loot
from ui.hud import (
    draw_exploration_ui,
    draw_perk_choice_overlay,
    draw_inventory_overlay,
)

# How far the player can see in tiles. Feel free to tweak.
FOV_RADIUS_TILES = 12


class GameMode:
    EXPLORATION = "exploration"
    BATTLE = "battle"
    PERK_CHOICE = "perk_choice"


class Game:
    """
    Core game object.

    Modes:
    - "exploration": dungeon movement, floors, enemies on the map
    - "battle": zoomed turn-based fight handled by BattleScene
    - "perk_choice": level-up perk choice overlay after a battle
    """

    def __init__(self, screen: pygame.Surface, hero_class_id: str = "warrior") -> None:
        self.screen = screen

        # Hero progression for this run (will be set in _init_hero_for_class)
        self.hero_stats = HeroStats()

        # Inventory & equipment (also set in _init_hero_for_class)
        self.inventory: Inventory = Inventory()
        self.show_inventory: bool = False

        # Floor index
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

        # --- Pending perk choices (level-up) ---
        self.pending_perk_choices: List[perk_system.Perk] = []

        # Mode handling
        self.mode: str = GameMode.EXPLORATION
        self.battle_scene: Optional[BattleScene] = None

        # XP from the current battle (set when we start it)
        self.pending_battle_xp: int = 0

        # Simple log string for XP / level up / heal / reward messages
        self.last_message: str = ""

        # Short grace window after battles where enemies don't auto-engage
        self.post_battle_grace: float = 0.0

        # Floor intro pause: enemies wait until the player makes the first move
        self.awaiting_floor_start: bool = True

        # Debug flags
        self.debug_reveal_map: bool = False

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
        """Switch back to exploration mode."""
        self.mode = GameMode.EXPLORATION

    def enter_battle_mode(self) -> None:
        """Switch into battle mode (BattleScene must already be created)."""
        self.mode = GameMode.BATTLE

    def enter_perk_choice_mode(self) -> None:
        """Switch into level-up perk choice overlay mode."""
        self.mode = GameMode.PERK_CHOICE

    def toggle_inventory_overlay(self) -> None:
        """
        Toggle inventory overlay. When opened, it hides other overlays
        that shouldn't overlap with it.
        """
        self.show_inventory = not self.show_inventory
        if self.show_inventory:
            # Inventory takes focus; hide character sheet & battle log
            self.show_character_sheet = False
            self.show_battle_log = False

    def toggle_character_sheet_overlay(self) -> None:
        """
        Toggle character sheet overlay. When opened, hide the battle log
        to avoid stacking overlays.
        """
        self.show_character_sheet = not self.show_character_sheet
        if self.show_character_sheet:
            self.show_battle_log = False

    def toggle_battle_log_overlay(self) -> None:
        """
        Toggle last battle log overlay ONLY if we actually have one.
        If there is no log, keep it off.
        """
        if not self.last_battle_log:
            self.show_battle_log = False
            return
        self.show_battle_log = not self.show_battle_log

    def is_overlay_open(self) -> bool:
        """
        Return True if a major overlay (inventory, character sheet) is open.
        Used to pause exploration updates.
        """
        return self.show_inventory or self.show_character_sheet

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

    def apply_hero_stats_to_player(self, full_heal: bool = False) -> None:
        """
        Sync hero meta stats (HeroStats) to the in-world Player entity.

        Applies:
        - max hp
        - attack / defense
        - crit / dodge chance
        - status resistance
        - move speed

        It’s defensive about attribute names so future HeroStats tweaks
        don’t instantly crash the game.
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

        # ---- Move speed ----
        move_speed = getattr(hs, "move_speed",
                             getattr(hs, "speed",
                                     getattr(self.player, "speed", 200.0)))
        self.player.speed = move_speed

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

        # Spawn enemies / chests only once per floor
        if newly_created:
            self.spawn_enemies_for_floor(game_map, floor_index)
            self.spawn_chests_for_floor(game_map, floor_index)

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
        Spawn enemies on this floor.

        Room-aware logic:
        - Never spawn in the 'start' room.
        - Prefer lair rooms for extra density.
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

        # Simple scaling: more enemies as floors go deeper, capped
        base_desired = 2 + floor_index
        desired = min(6, max(2, base_desired))

        chosen_tiles: List[tuple[int, int]] = []
        remaining = desired

        # Fill roughly half from lair rooms (if any)
        if lair_tiles and remaining > 0:
            lair_target = min(len(lair_tiles), max(1, remaining // 2))
            chosen_tiles.extend(lair_tiles[:lair_target])
            remaining -= lair_target

        # Fill most of the remainder from normal rooms
        if room_tiles and remaining > 0:
            room_target = min(len(room_tiles), remaining)
            chosen_tiles.extend(room_tiles[:room_target])
            remaining -= room_target

        # Whatever is left comes from corridors
        if corridor_tiles and remaining > 0:
            corr_target = min(len(corridor_tiles), remaining)
            chosen_tiles.extend(corridor_tiles[:corr_target])
            remaining -= corr_target

        # Actually spawn enemies at the chosen tiles
        for tx, ty in chosen_tiles:
            ex, ey = game_map.center_entity_on_tile(tx, ty, enemy_width, enemy_height)
            enemy = Enemy(
                x=ex,
                y=ey,
                width=enemy_width,
                height=enemy_height,
                # Slightly slower chase speed for nicer exploration feel
                speed=70.0,
            )

            # Basic combat stats that BattleScene will use
            max_hp = 10 + floor_index * 2
            setattr(enemy, "max_hp", max_hp)
            setattr(enemy, "hp", max_hp)
            setattr(enemy, "attack_power", 3 + floor_index // 2)

            # Small defense scaling per floor
            setattr(enemy, "defense", floor_index // 2)

            # XP reward for defeating this enemy
            setattr(enemy, "xp_reward", 5 + floor_index * 2)

            # Enemy type (for UI & group names)
            enemy_type = self._choose_enemy_type_for_floor(floor_index)
            setattr(enemy, "enemy_type", enemy_type)

            # Enemies block movement in exploration
            setattr(enemy, "blocks_movement", True)

            game_map.entities.append(enemy)

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

        # We still want 0–2 chests total, but if a treasure room exists,
        # there's a good chance at least one chest goes there.
        max_chests = min(2, len(treasure_tiles) + len(other_tiles))
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

    # ------------------------------------------------------------------
    # Chest helpers (currently unused – kept for future reuse)
    # ------------------------------------------------------------------

    def _find_chest_near_player(self, max_distance_px: int = TILE_SIZE // 2):
        """
        Return a chest entity near/under the player, or None.
        """
        from world.entities import Chest  # avoid circular import

        if self.current_map is None or self.player is None:
            return None

        px, py = self.player.rect.center
        max_dist_sq = max_distance_px * max_distance_px

        for entity in getattr(self.current_map, "entities", []):
            if not isinstance(entity, Chest):
                continue
            cx, cy = entity.rect.center
            dx = cx - px
            dy = cy - py
            if dx * dx + dy * dy <= max_dist_sq:
                return entity

        return None

    def try_open_chest(self) -> None:
        """
        Legacy chest opener – kept for now.
        ExplorationController.try_open_chest is the one actually used.
        """
        if self.current_map is None or self.player is None or self.inventory is None:
            return

        chest = self._find_chest_near_player(max_distance_px=TILE_SIZE // 2)
        if chest is None:
            self.last_message = "There is nothing here to open."
            return

        if getattr(chest, "opened", False):
            self.last_message = "The chest is empty."
            return

        chest.opened = True

        item_id = roll_chest_loot(self.floor)

        min_gold = 5 + self.floor
        max_gold = 10 + self.floor * 2
        gold_amount = random.randint(min_gold, max_gold)
        gained_gold = 0
        if hasattr(self.hero_stats, "add_gold"):
            gained_gold = self.hero_stats.add_gold(gold_amount)

        if item_id is None:
            if gained_gold > 0:
                self.last_message = f"You open the chest and find {gained_gold} gold."
            else:
                self.last_message = "The chest is empty."
            return

        self.inventory.add_item(item_id)

        item_def = get_item_def(item_id)
        item_name = item_def.name if item_def is not None else item_id

        if gained_gold > 0:
            self.last_message = (
                f"You open the chest and find: {item_name} and {gained_gold} gold."
            )
        else:
            self.last_message = f"You open the chest and find: {item_name}."

        if self.player is not None:
            self.apply_hero_stats_to_player(full_heal=False)

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
        self.pending_perk_choices = []

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

        # 4) Create battle scene with the entire group
        self.battle_scene = BattleScene(self.player, encounter_enemies, self.ui_font)
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
        self.last_message = ""
        self.pending_battle_xp = 0
        self.post_battle_grace = 0.0
        self.last_battle_log = []
        self.show_battle_log = False
        self.show_character_sheet = False
        self.pending_perk_choices = []

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

        NEW: on level-up, generate perk choices and enter 'perk_choice' mode.
        """
        if self.battle_scene is None:
            return
        if not self.battle_scene.finished:
            return

        status = self.battle_scene.status
        xp_reward = self.pending_battle_xp
        self.pending_battle_xp = 0

        # Keep a copy of the combat log so we can display it in exploration
        if self.battle_scene.combat_log:
            self.last_battle_log = list(self.battle_scene.combat_log)
        else:
            self.last_battle_log = []

        if status == "victory":
            messages: list[str] = []

            # 1) XP + level ups
            leveled_up = False
            if xp_reward > 0:
                old_level = self.hero_stats.level
                messages.extend(self.hero_stats.grant_xp(xp_reward))
                new_level = self.hero_stats.level
                leveled_up = new_level > old_level

                # On level-up, prepare perk choices (if any)
                if leveled_up:
                    self.pending_perk_choices = perk_system.pick_perk_choices(
                        self.hero_stats, max_choices=3
                    )

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

                # Ensure player stats are synced after any reward changes
                self.apply_hero_stats_to_player(full_heal=False)

            # 4) Possible item loot
            loot_item_id = roll_battle_loot(self.floor)
            if loot_item_id is not None and self.inventory is not None:
                # Add item to inventory
                self.inventory.add_item(loot_item_id)

                # Look up a nice display name if we can
                item_def = get_item_def(loot_item_id)
                item_name = item_def.name if item_def is not None else loot_item_id

                messages.append(f"You find: {item_name}.")

                # Re-sync stats in case gear bonuses matter later
                if self.player is not None:
                    self.apply_hero_stats_to_player(full_heal=False)

            if messages:
                self.last_message = " ".join(messages)

            # Grace window after the battle to avoid immediate re-engage
            self.post_battle_grace = 1.5

            # If we have perk choices, go into perk_choice mode; otherwise, back to exploration
            if self.pending_perk_choices:
                self.enter_perk_choice_mode()
            else:
                self.enter_exploration_mode()

        elif status == "defeat":
            # Restart whole run
            self.restart_run()

    # ------------------------------------------------------------------
    # Enemy AI (legacy in-Game version – ExplorationController has the
    # current logic; this is kept for potential reuse)
    # ------------------------------------------------------------------

    def update_enemy_exploration(self, enemy: Enemy, dt: float) -> None:
        """
        Very simple chase AI in exploration mode.
        Enemies won't chase or start new battles during post-battle grace.
        """
        if self.player is None or self.current_map is None:
            return

        if self.post_battle_grace > 0.0:
            return

        dx = self.player.rect.centerx - enemy.rect.centerx
        dy = self.player.rect.centery - enemy.rect.centery
        dist_sq = dx * dx + dy * dy

        chase_range = (TILE_SIZE * 6) ** 2  # chase if within ~6 tiles

        if dist_sq > chase_range:
            return  # idle

        direction = pygame.Vector2(dx, dy)
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()

        move_vector = direction * enemy.speed * dt
        new_x = enemy.x + move_vector.x
        new_y = enemy.y + move_vector.y

        new_rect = pygame.Rect(
            int(new_x),
            int(new_y),
            enemy.width,
            enemy.height,
        )

        if not self.current_map.rect_can_move_to(new_rect):
            return

        for other in self.current_map.entities:
            if other is enemy:
                continue
            if getattr(other, "blocks_movement", False) and other.rect.colliderect(
                new_rect
            ):
                return

        if self.player.rect.colliderect(new_rect):
            if self.post_battle_grace <= 0.0:
                self.start_battle(enemy)
            return

        enemy.move_to(new_x, new_y)

    # ------------------------------------------------------------------
    # Legacy exploration input / update (replaced by ExplorationController)
    # ------------------------------------------------------------------

    def handle_event_exploration(self, event: pygame.event.Event) -> None:
        """Old exploration handler (not used anymore)."""
        pass

    def update_exploration(self, dt: float) -> None:
        """Old exploration updater (not used anymore)."""
        pass

    # ------------------------------------------------------------------
    # Perk choice overlay
    # ------------------------------------------------------------------

    def handle_event_perk_choice(self, event: pygame.event.Event) -> None:
        """
        Handle input while the perk choice overlay is open.
        1 / 2 / 3 choose a perk. ESC cancels (no perk).
        """
        if event.type != pygame.KEYDOWN:
            return

        # Escape: skip (no perk)
        if event.key == pygame.K_ESCAPE:
            self.pending_perk_choices = []
            self.enter_exploration_mode()
            return

        idx = None
        if event.key in (pygame.K_1, pygame.K_KP1):
            idx = 0
        elif event.key in (pygame.K_2, pygame.K_KP2):
            idx = 1
        elif event.key in (pygame.K_3, pygame.K_KP3):
            idx = 2

        if idx is None:
            return

        if idx >= len(self.pending_perk_choices):
            return

        chosen = self.pending_perk_choices[idx]

        # Apply perk
        chosen.apply(self.hero_stats)

        # Register as learned
        if not hasattr(self.hero_stats, "perks"):
            self.hero_stats.perks = []
        if chosen.id not in self.hero_stats.perks:
            self.hero_stats.perks.append(chosen.id)

        # Re-sync stats
        if self.player is not None:
            self.apply_hero_stats_to_player(full_heal=False)

        # Show a concise message about what we picked
        self.last_message = f"You choose perk: {chosen.name}. {chosen.description}"

        # Clear choices and go back to exploration
        self.pending_perk_choices = []
        self.enter_exploration_mode()

    # ------------------------------------------------------------------
    # Main loop: update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.mode == GameMode.EXPLORATION:
            if self.post_battle_grace > 0.0:
                self.post_battle_grace = max(0.0, self.post_battle_grace - dt)

            # Exploration is handled by the controller...
            self.exploration.update(dt)
            # ...and after movement, we always refresh FOV around the player.
            self.update_fov()

        elif self.mode == GameMode.BATTLE:
            if self.battle_scene is not None:
                self.battle_scene.update(dt)
                self._check_battle_finished()
        elif self.mode == GameMode.PERK_CHOICE:
            # No world updates while choosing a perk
            pass

    # ------------------------------------------------------------------
    # Main loop: event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Dispatch events based on current game mode.
        Global debug / cheat keys are processed first.
        """
        # Cheats: handle global debug keys, consume the event if needed
        if handle_cheat_key(self, event):
            return

        if self.mode == GameMode.EXPLORATION:
            self.exploration.handle_event(event)
        elif self.mode == GameMode.BATTLE:
            if self.battle_scene is not None:
                self.battle_scene.handle_event(event)
                self._check_battle_finished()
        elif self.mode == GameMode.PERK_CHOICE:
            self.handle_event_perk_choice(event)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self) -> None:
        if self.mode == GameMode.EXPLORATION:
            self.draw_exploration()
        elif self.mode == GameMode.BATTLE:
            self.draw_battle()
        elif self.mode == GameMode.PERK_CHOICE:
            # Show the world + UI, then overlay the perk choice
            self.draw_exploration()
            draw_perk_choice_overlay(self)

    def draw_exploration(self) -> None:
        assert self.current_map is not None
        assert self.player is not None

        self.screen.fill(COLOR_BG)

        # Map tiles
        self.current_map.draw(self.screen)

        # Non-player entities (enemies, chests, props…) – only if visible
        for entity in getattr(self.current_map, "entities", []):
            cx, cy = entity.rect.center
            tx, ty = self.current_map.world_to_tile(cx, cy)
            if (tx, ty) not in self.current_map.visible:
                continue
            entity.draw(self.screen)

        # Draw the player on top of everything else
        self.player.draw(self.screen)

        # HUD + overlays
        draw_exploration_ui(self)

        pygame.display.flip()

    def draw_battle(self) -> None:
        if self.battle_scene is None:
            return

        self.screen.fill(COLOR_BG)
        self.battle_scene.draw(self.screen)

        # Optional inventory / character overlays even during battle
        if self.show_inventory and self.inventory is not None:
            draw_inventory_overlay(self, self.inventory)
        elif self.show_character_sheet:
            draw_exploration_ui(self)

        pygame.display.flip()
