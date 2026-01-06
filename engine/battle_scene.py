from collections import Counter
from typing import List, Dict, Optional, Literal

import math
import random
import pygame

from settings import (
    COLOR_PLAYER,
    COLOR_ENEMY,
    BATTLE_GRID_WIDTH,
    BATTLE_GRID_HEIGHT,
    BATTLE_CELL_SIZE,
    BATTLE_ENEMY_TIMER,
    MAX_BATTLE_ENEMIES,
    BATTLE_AI_DEFENSIVE_HP_THRESHOLD,
    BATTLE_AI_SKILL_CHANCE,
    BATTLE_AI_DEFENSIVE_SKILL_CHANCE,
    MAX_SKILL_SLOTS,
    DEFAULT_PLAYER_MAX_HP,
    DEFAULT_PLAYER_ATTACK,
    DEFAULT_PLAYER_STAMINA,
    DEFAULT_COMPANION_STAMINA,
    DEFAULT_ENEMY_STAMINA,
    DEFAULT_ENEMY_MANA,
    DEFAULT_COMPANION_HP_FACTOR,
    DEFAULT_COMPANION_ATTACK_FACTOR,
    DEFAULT_MIN_SKILL_POWER,
    BATTLE_ENEMY_START_COL_OFFSET,
    BASE_CRIT_CHANCE,
    CRIT_DAMAGE_MULTIPLIER,
    COVER_DAMAGE_REDUCTION,
    FLANKING_DAMAGE_BONUS,
    TERRAIN_SPAWN_CHANCE,
    BASE_MOVEMENT_POINTS,
    HAZARD_MOVEMENT_COST,
)
from world.entities import Player, Enemy
from systems.statuses import (
    StatusEffect,
    tick_statuses,
    has_status,
    is_stunned,
    outgoing_multiplier,
    incoming_multiplier,
)
from systems.skills import Skill, get as get_skill
from systems import perks as perk_system
from systems.party import (
    CompanionDef,
    CompanionState,
    get_companion,
    ensure_companion_stats,
    create_companion_entity,
)
from systems.enemies import get_archetype  # NEW
from systems.input import InputAction  # NEW
from systems.inventory import get_item_def  # NEW: for weapon range
from ui.hud_battle import (
    _draw_battle_unit_card,
    _draw_battle_skill_hotbar,
    _draw_battle_log_line,
)
from ui.hud_utils import (
    _draw_status_indicators,
)
from ui.combat_tutorial import draw_combat_tutorial

# Import battle types from the new types module
from engine.battle.types import (
    BattleTerrain,
    BattleUnit,
    BattleStatus,
    Side,
    TerrainType,
)
from engine.battle.renderer import BattleRenderer
from engine.battle.pathfinding import BattlePathfinding
from engine.battle.combat import BattleCombat
from engine.battle.terrain import BattleTerrainManager
from engine.battle.ai import BattleAI
from engine.config import get_config



class BattleScene:
    """
    Turn-based battle on a small abstract grid.

    - 2-player party (hero + companion) vs a small enemy group (up to 3).
    - Initiative per unit.
    - Units can:
        - Move 1 tile (WASD / arrows)
        - Basic attack adjacent enemies (SPACE)
        - Skills (Guard, Power Strike, Crippling Blow, etc.) from systems.skills
    """

    def __init__(
        self,
        player: Player,
        enemies: List[Enemy],
        font: pygame.font.Font,
        companions: Optional[List[object]] = None,
        game: Optional[object] = None,  # NEW: optional game reference for inventory access
    ) -> None:
        self.player = player
        self.font = font
        self.game = game  # Store game reference for inventory access

        # Initialize basic setup (grid, terrain, log, state)
        self._init_basic_setup()
        
        # Initialize hero unit
        hero_unit = self._init_hero_unit()
        self.player_units: List[BattleUnit] = [hero_unit]
        
        # Initialize companion unit
        self._init_companion_unit(companions)
        
        # Initialize enemy units
        self._init_enemy_units(enemies)
        
        # Initialize turn order and managers
        self._init_turn_order()
        self._init_managers()
        
        # Initialize cooldowns / statuses for first unit
        if self.turn_order:
            self._on_unit_turn_start(self.turn_order[0])

    def _init_basic_setup(self) -> None:
        """Initialize basic battle setup: grid, terrain, log, and state variables."""
        # Grid configuration (battlefield, not dungeon grid)
        # Wider battlefield; origin is centered dynamically in draw().
        self.grid_width = BATTLE_GRID_WIDTH
        self.grid_height = BATTLE_GRID_HEIGHT
        
        # Scale cell size based on screen resolution if game reference is available
        if self.game is not None and hasattr(self.game, 'screen'):
            screen_w, screen_h = self.game.screen.get_size()
            from settings import WINDOW_WIDTH, WINDOW_HEIGHT
            resolution_scale = min(screen_w / WINDOW_WIDTH, screen_h / WINDOW_HEIGHT)
            if resolution_scale > 1.0:
                # Scale battle cells more aggressively to keep battle visible
                cell_scale = min(1.0 + (resolution_scale - 1.0) * 0.6, 2.5)
            else:
                cell_scale = max(resolution_scale, 0.5)
            self.cell_size = int(BATTLE_CELL_SIZE * cell_scale)
        else:
            self.cell_size = BATTLE_CELL_SIZE
        
        self.grid_origin_x = 0
        self.grid_origin_y = 0
        
        # Terrain system: 2D grid of terrain types
        self.terrain: Dict[tuple[int, int], BattleTerrain] = {}
        
        # Initialize terrain manager
        self.terrain_manager = BattleTerrainManager(self)
        self.terrain_manager.generate_terrain()
        
        # Tutorial overlay
        self.show_tutorial: bool = False
        self.tutorial_scroll_offset: int = 0  # Scroll position for tutorial
        
        # Log history viewer
        self.show_log_history: bool = False
        
        # Movement pathfinding state
        self.movement_mode: bool = False  # True when selecting movement destination
        self.movement_path: List[tuple[int, int]] = []  # Current path preview
        self.movement_target: Optional[tuple[int, int]] = None  # Target cell for movement
        self.mouse_hover_cell: Optional[tuple[int, int]] = None  # Cell currently hovered by mouse
        self.movement_key_press_count: int = 0  # Track number of movement key presses for looping

        # --- Combat log ---
        self.log: List[str] = []
        self.max_log_lines: int = 6
        self.last_action: str = ""

        # Backwards-compatible alias for older game code
        self.combat_log = self.log

        # Targeting state (for player-controlled units)
        # When not None, contains: {"action_type": "attack"|"skill", "skill": Optional[Skill], "targets": List[BattleUnit], "target_index": int}
        self.targeting_mode: Optional[Dict] = None

        # Floating damage numbers - list of {target, damage, timer, y_offset, is_crit}
        self._floating_damage: List[Dict] = []
        
        # Hit spark effects - list of {x, y, timer}
        self._hit_sparks: List[Dict] = []
        
        # Animation timer for pulsing effects
        self.animation_time: float = 0.0

    def _init_hero_unit(self) -> BattleUnit:
        """Initialize the hero unit with skills, resources, and skill slots."""
        hero_name = getattr(self.player, "name", "Hero")
        hero_unit = BattleUnit(
            entity=self.player,
            side="player",
            gx=2,
            gy=self.grid_height // 2,
            name=hero_name,
        )

        # --- New: initialise hero resource pools from the Player entity ---
        # These values are populated in Game.apply_hero_stats_to_player.
        hero_max_stamina = int(getattr(self.player, "max_stamina", 0) or 0)
        hero_max_mana = int(getattr(self.player, "max_mana", 0) or 0)

        # Backwards-compatible safety defaults so hero can always use skills.
        if hero_max_stamina <= 0:
            hero_max_stamina = DEFAULT_PLAYER_STAMINA
        if hero_max_mana < 0:
            hero_max_mana = 0

        setattr(self.player, "max_stamina", hero_max_stamina)
        setattr(self.player, "max_mana", hero_max_mana)

        # Initialize resource pools from entity max values
        hero_unit.init_resources_from_entity()
        
        # Initialize movement points
        hero_unit.max_movement_points = BASE_MOVEMENT_POINTS
        hero_unit.current_movement_points = BASE_MOVEMENT_POINTS

        # Core hero skills – now robust against missing registry
        hero_unit.skills = {}
        try:
            guard_skill = get_skill("guard")
            if guard_skill:
                hero_unit.skills["guard"] = guard_skill
        except (KeyError, AttributeError):
            pass
        try:
            power_strike_skill = get_skill("power_strike")
            if power_strike_skill:
                hero_unit.skills["power_strike"] = power_strike_skill
                hero_unit.cooldowns["power_strike"] = 0  # ready
        except (KeyError, AttributeError):
            pass

        # Extra skills granted by perks (from systems.perks)
        hero_perk_ids = getattr(self.player, "perks", [])
        for pid in hero_perk_ids:
            try:
                perk = perk_system.get(pid)
            except KeyError:
                continue

            for skill_id in getattr(perk, "grant_skills", []):
                try:
                    hero_unit.skills[skill_id] = get_skill(skill_id)
                    # Make sure cooldown entry exists; 0 = ready
                    hero_unit.cooldowns.setdefault(skill_id, 0)
                except KeyError:
                    # Skill not registered yet – ignore silently
                    continue

        # Prefer a persisted slot layout if present on the hero entity
        # (e.g. synced from HeroStats.skill_slots). Fallback to auto layout.
        hero_slots = getattr(self.player, "skill_slots", None)
        if isinstance(hero_slots, list) and any(hero_slots):
            self._apply_persisted_slots(hero_unit, hero_slots)
        else:
            self._auto_assign_skill_slots(hero_unit)
        
        return hero_unit

    def _init_companion_unit(self, companions: Optional[List[object]]) -> None:
        """Initialize companion unit(s) from the provided companions list."""
        hero_row = self.grid_height // 2
        companion_row = max(0, hero_row - 1)
        created_any_companion = False

        if companions:
            # For now we still only use the FIRST companion in the list.
            raw_comp = companions[0]

            comp_def: Optional[CompanionDef] = None
            comp_state: Optional[CompanionState] = None

            # New path: runtime CompanionState → look up its template
            if isinstance(raw_comp, CompanionState):
                comp_state = raw_comp
                template_id = getattr(raw_comp, "template_id", None)
                if template_id is not None:
                    try:
                        comp_def = get_companion(template_id)
                    except KeyError:
                        comp_def = None

            # Legacy path: we were passed a CompanionDef directly
            if comp_def is None and isinstance(raw_comp, CompanionDef):
                comp_def = raw_comp

            if comp_def is not None:
                # Create companion entity using the helper function
                base_max_hp = getattr(self.player, "max_hp", DEFAULT_PLAYER_MAX_HP)
                base_atk = getattr(self.player, "attack_power", DEFAULT_PLAYER_ATTACK)
                base_def = int(getattr(self.player, "defense", 0))
                base_sp = float(getattr(self.player, "skill_power", 1.0))
                
                companion_entity = create_companion_entity(
                    template=comp_def,
                    state=comp_state,
                    reference_player=self.player,
                    hero_base_hp=base_max_hp,
                    hero_base_attack=base_atk,
                    hero_base_defense=base_def,
                    hero_base_skill_power=base_sp,
                )
                
                # Prefer state name_override if present, then template name,
                # then player's generic companion_name, then plain "Companion".
                companion_name = getattr(comp_state, "name_override", None) or comp_def.name
                if not companion_name:
                    companion_name = getattr(self.player, "companion_name", "Companion")

                companion_unit = BattleUnit(
                    entity=companion_entity,
                    side="player",
                    gx=2,
                    gy=companion_row,
                    name=companion_name,
                )

                # Initialize resource pools from entity max values
                companion_unit.init_resources_from_entity()

                # Skills for the companion: from template, fallback to Guard
                skills: Dict[str, Skill] = {}
                for skill_id in comp_def.skill_ids:
                    try:
                        skills[skill_id] = get_skill(skill_id)
                    except KeyError:
                        continue
                if "guard" not in skills:
                    try:
                        guard_skill = get_skill("guard")
                        if guard_skill:
                            skills["guard"] = guard_skill
                    except (KeyError, AttributeError):
                        pass

                companion_unit.skills = skills

                # --- Extra skills from this companion's own perks -------------
                # CompanionState.perks is a list of perk ids; many of those
                # perks may define grant_skills, just like the hero.
                if comp_state is not None and getattr(comp_state, "perks", None):
                    for pid in comp_state.perks:
                        try:
                            perk = perk_system.get(pid)
                        except KeyError:
                            continue

                        for skill_id in getattr(perk, "grant_skills", []):
                            try:
                                companion_unit.skills[skill_id] = get_skill(skill_id)
                                # Ensure cooldown entry exists; 0 = ready.
                                companion_unit.cooldowns.setdefault(skill_id, 0)
                            except KeyError:
                                continue

                # Use a persisted layout from CompanionState if possible,
                # otherwise fall back to an automatic layout.
                applied_from_state = False
                if comp_state is not None:
                    state_slots = getattr(comp_state, "skill_slots", None)
                    if isinstance(state_slots, list) and any(state_slots):
                        self._apply_persisted_slots(companion_unit, state_slots)
                        applied_from_state = True

                if not applied_from_state:
                    self._auto_assign_skill_slots(companion_unit)

                self.player_units.append(companion_unit)
                created_any_companion = True

        if not created_any_companion:
            # Fallback to old behaviour: one generic companion
            # Create a minimal CompanionDef for the fallback
            from dataclasses import dataclass
            @dataclass
            class _GenericCompanionDef(CompanionDef):
                pass
            
            generic_template = _GenericCompanionDef(
                id="generic",
                name="Companion",
                role="Companion",
                hp_factor=DEFAULT_COMPANION_HP_FACTOR,
                attack_factor=DEFAULT_COMPANION_ATTACK_FACTOR,
                defense_factor=1.0,
                skill_power_factor=1.0,
            )
            
            base_max_hp = getattr(self.player, "max_hp", DEFAULT_PLAYER_MAX_HP)
            base_atk = getattr(self.player, "attack_power", DEFAULT_PLAYER_ATTACK)
            
            companion = create_companion_entity(
                template=generic_template,
                state=None,  # No state for generic companion
                reference_player=self.player,
                hero_base_hp=base_max_hp,
                hero_base_attack=base_atk,
            )
            
            companion_display_name = getattr(self.player, "companion_name", "Companion")
            companion_unit = BattleUnit(
                entity=companion,
                side="player",
                gx=2,
                gy=max(0, self.grid_height // 2 - 1),
                name=companion_display_name,
            )
            # Initialize resource pools from entity max values
            companion_unit.init_resources_from_entity()
            
            # Initialize movement points
            companion_unit.max_movement_points = BASE_MOVEMENT_POINTS
            companion_unit.current_movement_points = BASE_MOVEMENT_POINTS

            try:
                companion_unit.skills = {
                    "guard": get_skill("guard"),
                }
            except KeyError:
                companion_unit.skills = {}

            # Auto-populate fallback companion hotbar as well.
            self._auto_assign_skill_slots(companion_unit)
            self.player_units.append(companion_unit)

    def _init_enemy_units(self, enemies: List[Enemy]) -> None:
        """Initialize enemy units from the provided enemies list."""
        self.enemy_units: List[BattleUnit] = []

        max_enemies = min(len(enemies), MAX_BATTLE_ENEMIES)
        grid_width = self.grid_width
        grid_height = self.grid_height

        # Enemies start a few columns in from the right edge so there's
        # real distance between the two lines.
        start_col = grid_width - BATTLE_ENEMY_START_COL_OFFSET
        start_row = max(0, grid_height // 2 - (max_enemies // 2))

        enemy_type_list: List[str] = []

        for i, enemy in enumerate(enemies[:max_enemies]):
            gx = start_col
            gy = start_row + i

            arch_id = getattr(enemy, "archetype_id", None)
            enemy_name = getattr(enemy, "enemy_type", "Enemy")

            # If we know the archetype, prefer its display name
            if arch_id is not None:
                try:
                    arch = get_archetype(arch_id)
                    enemy_name = arch.name
                except KeyError:
                    # Fallback to whatever is on the entity
                    pass

            enemy_type_list.append(enemy_name)

            unit = BattleUnit(
                entity=enemy,
                side="enemy",
                gx=gx,
                gy=gy,
                name=enemy_name,
            )
            # Resource pools for enemies based on archetype
            # Casters get mana, others get stamina
            enemy_max_mana = 0
            enemy_max_stamina = DEFAULT_ENEMY_STAMINA
            
            # Give casters mana based on their archetype
            if arch_id is not None:
                try:
                    arch = get_archetype(arch_id)
                    # Check if archetype has caster skills (dark_hex, etc.)
                    caster_skills = ["dark_hex", "fireball", "lightning_bolt", "slow", "magic_shield"]
                    if any(skill_id in arch.skill_ids for skill_id in caster_skills):
                        enemy_max_mana = DEFAULT_ENEMY_MANA
                        enemy_max_stamina = 8  # Casters have less stamina
                except KeyError:
                    pass
            
            setattr(enemy, "max_mana", enemy_max_mana)
            setattr(enemy, "max_stamina", enemy_max_stamina)
            # Initialize resource pools from entity max values
            unit.init_resources_from_entity()
            
            # Initialize movement points
            unit.max_movement_points = BASE_MOVEMENT_POINTS
            unit.current_movement_points = BASE_MOVEMENT_POINTS

            # Skills from archetype
            if arch_id is not None:
                try:
                    arch = get_archetype(arch_id)
                    for skill_id in arch.skill_ids:
                        try:
                            unit.skills[skill_id] = get_skill(skill_id)
                            unit.cooldowns.setdefault(skill_id, 0)
                        except KeyError:
                            # Missing skill definition – skip gracefully
                            pass
                except KeyError:
                    pass

            # Fallback: generic weakening hit so nothing breaks
            if not unit.skills:
                try:
                    cb = get_skill("crippling_blow")
                    unit.skills["crippling_blow"] = cb
                    unit.cooldowns.setdefault("crippling_blow", 0)
                except KeyError:
                    pass

            self.enemy_units.append(unit)

        # Group label for enemies (used in victory text etc.)
        counter = Counter(enemy_type_list)
        if counter:
            parts = []
            for etype, count in counter.items():
                if count == 1:
                    parts.append(etype)
                else:
                    parts.append(f"{count}x {etype}")
            self.enemy_group_label = ", ".join(parts)
        else:
            self.enemy_group_label = "???"

    def _init_turn_order(self) -> None:
        """Initialize turn order and battle state."""
        # Turn state
        self.turn_order: List[BattleUnit] = self.player_units + self.enemy_units
        random.shuffle(self.turn_order)
        self.turn_index: int = 0
        self.turn: Side = self.turn_order[0].side if self.turn_order else "player"
        self.status: BattleStatus = "ongoing"
        self.finished: bool = False

        # Enemy AI timer – small delay so actions are readable
        # Apply battle speed multiplier (higher speed = faster timer countdown)
        config = get_config()
        battle_speed = getattr(config, "battle_speed", 1.0)
        self.enemy_timer: float = BATTLE_ENEMY_TIMER / battle_speed

    def _init_managers(self) -> None:
        """Initialize battle system managers (renderer, pathfinding, combat, AI)."""
        # Initialize renderer
        self.renderer = BattleRenderer(self)
        
        # Initialize pathfinding
        self.pathfinding = BattlePathfinding(self)
        
        # Initialize combat calculator
        self.combat = BattleCombat(self)
        
        # Initialize AI
        self.ai = BattleAI(self)

    # ------------ Log helpers ------------

    def _log(self, msg: str) -> None:
        """
        Append a message to the combat log and keep last_action in sync.
        """
        self.last_action = msg
        self.log.append(msg)
        if len(self.log) > self.max_log_lines:
            self.log.pop(0)

    # ------------ Helpers ------------

    def _all_units(self) -> List[BattleUnit]:
        return self.player_units + self.enemy_units

    def _active_unit(self) -> BattleUnit:
        return self.turn_order[self.turn_index]

    def _hero_unit(self) -> Optional[BattleUnit]:
        for u in self.player_units:
            if u.entity is self.player:
                return u
        return self.player_units[0] if self.player_units else None

    # ----- Status helpers -----

    def _tick_statuses_on_turn_start(self, unit: BattleUnit) -> None:
        """
        Tick down statuses, apply DOT damage, and update HP.
        """
        dot = tick_statuses(unit.statuses)
        if dot > 0:
            current_hp = getattr(unit.entity, "hp", 0)
            setattr(unit.entity, "hp", max(0, current_hp - dot))
            self._log(f"{unit.name} suffers {dot} damage from effects.")

    def _has_status(self, unit: BattleUnit, name: str) -> bool:
        return has_status(unit.statuses, name)

    def _is_stunned(self, unit: BattleUnit) -> bool:
        return is_stunned(unit.statuses)

    # Status multiplier methods have been moved to engine.battle.combat.BattleCombat

    def _has_dot(self, unit: BattleUnit) -> bool:
        """Return True if the unit has any damage-over-time status."""
        return any(s.flat_damage_each_turn > 0 for s in unit.statuses)


    def _add_status(self, unit: BattleUnit, status: StatusEffect) -> None:
        """
        Add or refresh a status on the unit.
        For stackable statuses (like disease), increase stacks instead of refreshing.
        """
        for existing in unit.statuses:
            if existing.name == status.name:
                # Stackable statuses: increase stacks and refresh duration
                if status.name == "diseased" and hasattr(status, "stacks"):
                    existing.stacks = getattr(existing, "stacks", 1) + getattr(status, "stacks", 1)
                    existing.duration = max(existing.duration, status.duration)
                    existing.flat_damage_each_turn = existing.stacks  # Damage scales with stacks
                    self._log(f"{unit.name}'s {status.name} stacks to {existing.stacks}!")
                    return
                # Non-stackable: refresh duration and values
                existing.duration = max(existing.duration, status.duration)
                existing.incoming_mult = status.incoming_mult
                existing.outgoing_mult = status.outgoing_mult
                existing.flat_damage_each_turn = status.flat_damage_each_turn
                existing.stunned = status.stunned
                existing.stacks = status.stacks
                return
        unit.statuses.append(status)
        self._log(f"{unit.name} is affected by {status.name}.")

    # Terrain management methods have been moved to engine.battle.terrain.BattleTerrainManager

    def _on_unit_turn_start(self, unit: BattleUnit) -> None:
        self._tick_statuses_on_turn_start(unit)
        for k in list(unit.cooldowns.keys()):
            if unit.cooldowns[k] > 0:
                unit.cooldowns[k] -= 1

        # Regenerate resources each turn (scales with level)
        # Higher level characters regain more stamina/mana per turn
        unit.regenerate_stamina()  # Amount calculated based on level
        unit.regenerate_mana()  # Amount calculated based on level
        
        # Reset movement points at start of turn
        unit.current_movement_points = unit.max_movement_points
        
        # Auto-start movement mode for player units if not engaged
        if unit.side == "player" and unit.current_movement_points > 0:
            # Check if unit is engaged (adjacent to enemies)
            enemies_adjacent = self._adjacent_enemies(unit)
            if not enemies_adjacent:
                # Not engaged - auto-start movement mode
                self._enter_movement_mode(unit)
        
        # Apply hazard damage if standing on hazardous terrain
        terrain = self.terrain_manager.get_terrain(unit.gx, unit.gy)
        if terrain.hazard_damage > 0:
            current_hp = getattr(unit.entity, "hp", 0)
            new_hp = max(0, current_hp - terrain.hazard_damage)
            setattr(unit.entity, "hp", new_hp)
            if new_hp < current_hp:
                self._log(f"{unit.name} takes {terrain.hazard_damage} damage from hazardous terrain!")

    # ----- Grid / movement helpers -----

    def _cell_blocked(self, gx: int, gy: int) -> bool:
        if gx < 0 or gy < 0 or gx >= self.grid_width or gy >= self.grid_height:
            return True
        # Check for obstacles
        terrain = self.terrain_manager.get_terrain(gx, gy)
        if terrain.blocks_movement:
            return True
        # Check for units
        for u in self._all_units():
            if not u.is_alive:
                continue
            if u.gx == gx and u.gy == gy:
                return True
        return False

    def _get_movement_cost(self, gx: int, gy: int) -> int:
        """
        Get the movement cost to enter a cell.
        Normal cells cost 1, hazards cost extra.
        """
        terrain = self.terrain_manager.get_terrain(gx, gy)
        if terrain.terrain_type == "hazard":
            return HAZARD_MOVEMENT_COST
        return 1
    
    # Pathfinding methods have been moved to engine.battle.pathfinding.BattlePathfinding

    def _try_move_unit(self, unit: BattleUnit, dx: int, dy: int) -> bool:
        """
        Legacy single-step movement. For new pathfinding system, use _move_unit_along_path.
        """
        new_gx = unit.gx + dx
        new_gy = unit.gy + dy
        
        # Check movement cost
        move_cost = self._get_movement_cost(new_gx, new_gy)
        if unit.current_movement_points < move_cost:
            return False
        
        if self._cell_blocked(new_gx, new_gy):
            return False
        
        unit.gx = new_gx
        unit.gy = new_gy
        unit.current_movement_points -= move_cost
        return True
    
    def _move_unit_along_path(self, unit: BattleUnit, path: List[tuple[int, int]]) -> bool:
        """
        Move unit along a path, consuming movement points.
        Returns True if movement was successful.
        """
        if not path or len(path) < 2:
            return False
        
        total_cost = 0
        for i in range(1, len(path)):
            gx, gy = path[i]
            total_cost += self._get_movement_cost(gx, gy)
        
        if unit.current_movement_points < total_cost:
            return False
        
        # Move unit to end of path
        final_pos = path[-1]
        unit.gx, unit.gy = final_pos
        unit.current_movement_points -= total_cost
        return True

    def _enemies_in_range(self, unit: BattleUnit, max_range: int) -> List[BattleUnit]:
        """
        Return all enemy units within a given Manhattan range.
        Delegates to AI module.
        """
        return self.ai.enemies_in_range(unit, max_range)

    def _adjacent_enemies(self, unit: BattleUnit) -> List[BattleUnit]:
        """
        Backwards-compatible helper: enemies at distance 1.
        Delegates to AI module.
        """
        return self.ai.adjacent_enemies(unit)

    # Weapon range method has been moved to engine.battle.combat.BattleCombat._get_weapon_range
    def _get_weapon_range_legacy(self, unit: BattleUnit) -> int:
        """
        Get the weapon range for a unit. Returns 1 for melee weapons (default).
        
        For player: checks equipped weapon in game inventory.
        For companions: checks equipped weapon in companion state.
        For enemies: checks weapon_range attribute or archetype.
        """
        # Default melee range
        default_range = 1
        
        # Check if it's a player entity
        if isinstance(unit.entity, Player) and unit.entity is self.player:
            # Hero: get weapon from game inventory
            if self.game is not None:
                inventory = getattr(self.game, "inventory", None)
                if inventory is not None:
                    weapon_id = inventory.equipped.get("weapon")
                    if weapon_id:
                        weapon_def = get_item_def(weapon_id)
                        if weapon_def:
                            range_val = weapon_def.stats.get("range")
                            if range_val is not None:
                                return int(range_val)
        
        # Check if it's a companion (companions are also Player entities but different instances)
        # Since only one companion is used in battle, check the first companion in party
        if self.game is not None and unit.side == "player" and unit.entity is not self.player:
            party = getattr(self.game, "party", None) or []
            if party:
                # Check first companion's equipment (only one companion is used in battle)
                comp_state = party[0]
                if hasattr(comp_state, "equipped"):
                    comp_weapon_id = comp_state.equipped.get("weapon")
                    if comp_weapon_id:
                        weapon_def = get_item_def(comp_weapon_id)
                        if weapon_def:
                            range_val = weapon_def.stats.get("range")
                            if range_val is not None:
                                return int(range_val)
        
        # For enemies, check weapon_range attribute or archetype
        if isinstance(unit.entity, Enemy):
            # Check direct attribute first
            if hasattr(unit.entity, "weapon_range"):
                return int(getattr(unit.entity, "weapon_range", default_range))
            
            # Check archetype for weapon info
            arch_id = getattr(unit.entity, "archetype_id", None)
            if arch_id:
                try:
                    arch = get_archetype(arch_id)
                    if hasattr(arch, "weapon_range"):
                        return int(getattr(arch, "weapon_range", default_range))
                except KeyError:
                    pass
        
        return default_range

    def _nearest_target(self, unit: BattleUnit, target_side: Side) -> Optional[BattleUnit]:
        """Find nearest target. Delegates to AI module."""
        return self.ai.nearest_target(unit, target_side)

    def _step_towards(self, unit: BattleUnit, target: BattleUnit) -> bool:
        """Move unit one step towards target. Delegates to AI module."""
        return self.ai.step_towards(unit, target)

    # ----- Damage helpers -----

    # Combat calculation methods have been moved to engine.battle.combat.BattleCombat

    # ----- Skill helpers -----

    def _auto_assign_skill_slots(self, unit: BattleUnit) -> None:
        """
        Populate unit.skill_slots from its current skills dict.

        Guard is deliberately left OUT of slots – it has its own
        dedicated GUARD action (usually bound to G).

        Simple default:
        - prefer 'power_strike' (or other core attacks) first
        - then fill with any remaining non-guard skills in dict order
        - cap at 4 entries (SKILL_1..SKILL_4)
        """
        ordered: List[str] = []

        # Priority skills first, if present on this unit.
        for prio in ("power_strike",):
            if prio in unit.skills and prio not in ordered:
                ordered.append(prio)

        # Then everything else EXCEPT 'guard', in insertion order.
        for sid in unit.skills.keys():
            if sid == "guard":
                continue
            if sid not in ordered:
                ordered.append(sid)

        # Take at most MAX_SKILL_SLOTS skills for now.
        unit.skill_slots = ordered[:MAX_SKILL_SLOTS]



    def _apply_persisted_slots(self, unit: BattleUnit, persisted_ids) -> None:
        """
        Apply a pre-defined skill layout from data (hero/companion state).

        - Ignores ids the unit doesn't actually have.
        - Skips 'guard' (dedicated GUARD action).
        - Truncates/pads to 4 entries.
        Falls back to _auto_assign_skill_slots if nothing usable remains.
        """
        if not persisted_ids:
            self._auto_assign_skill_slots(unit)
            return

        ordered: List[Optional[str]] = []

        for sid in persisted_ids:
            if not sid:
                ordered.append(None)
                continue
            if sid == "guard":
                # Guard is not part of the hotbar; keep its own key.
                ordered.append(None)
                continue
            if sid not in unit.skills:
                ordered.append(None)
                continue
            ordered.append(sid)
            if len(ordered) >= 4:
                break

        # Ensure we always have MAX_SKILL_SLOTS entries to match SKILL_1..SKILL_4
        while len(ordered) < MAX_SKILL_SLOTS:
            ordered.append(None)

        # Strip trailing Nones so a fully-empty layout becomes [].
        trimmed = list(ordered)
        while trimmed and trimmed[-1] is None:
            trimmed.pop()

        if trimmed:
            unit.skill_slots = trimmed  # type: ignore[attr-defined]
        else:
            self._auto_assign_skill_slots(unit)


    def _skill_for_action(self, unit: BattleUnit, action: InputAction) -> Optional[Skill]:
        """Resolve InputAction.SKILL_1..4 -> Skill via the unit's skill_slots.

        If there is no slot mapping yet, returns None and the caller can
        fall back to key-based logic.
        """
        slots = getattr(unit, "skill_slots", None)
        if not slots:
            return None

        index_map = {
            InputAction.SKILL_1: 0,
            InputAction.SKILL_2: 1,
            InputAction.SKILL_3: 2,
            InputAction.SKILL_4: 3,
        }
        idx = index_map.get(action)
        if idx is None or idx >= len(slots):
            return None

        skill_id = slots[idx]
        if not skill_id:
            return None

        return unit.skills.get(skill_id)

    def _skill_for_key(self, unit: BattleUnit, key: int) -> Optional[Skill]:
        for skill in unit.skills.values():
            if skill.key == key:
                return skill
        return None

    def _use_skill(self, unit: BattleUnit, skill: Skill, *, for_ai: bool = False) -> bool:
        """
        Fire a skill for a unit (with auto-targeting).
        Returns True if the skill actually consumed the unit's turn.
        """
        if self._is_stunned(unit):
            if not for_ai:
                self._log(f"{unit.name} is stunned and cannot act!")
            self._next_turn()
            return True

        cd = unit.cooldowns.get(skill.id, 0)
        if cd > 0:
            if not for_ai:
                self._log(f"{skill.name} is on cooldown ({cd} turns).")
            return False

        # Decide target
        target_unit: Optional[BattleUnit] = None
        if skill.target_mode == "self":
            target_unit = unit
        elif skill.target_mode == "adjacent_enemy":
            # Range-ready: skills can define range_tiles (defaults to 1)
            max_range = getattr(skill, "range_tiles", 1)
            candidates = self._enemies_in_range(unit, max_range)
            if not candidates:
                if not for_ai:
                    self._log(f"No enemy in range for {skill.name}!")
                return False
            target_unit = candidates[0]

        return self._use_skill_targeted(unit, skill, target_unit, for_ai=for_ai)

    def _use_skill_targeted(self, unit: BattleUnit, skill: Skill, target_unit: Optional[BattleUnit], *, for_ai: bool = False) -> bool:
        """
        Fire a skill for a unit on a specific target.
        Returns True if the skill actually consumed the unit's turn.
        """
        if self._is_stunned(unit):
            if not for_ai:
                self._log(f"{unit.name} is stunned and cannot act!")
            self._next_turn()
            return True

        cd = unit.cooldowns.get(skill.id, 0)
        if cd > 0:
            if not for_ai:
                self._log(f"{skill.name} is on cooldown ({cd} turns).")
            return False

        # Verify target is valid for this skill
        if skill.target_mode == "self":
            target_unit = unit
        elif skill.target_mode == "adjacent_enemy":
            if target_unit is None:
                if not for_ai:
                    self._log(f"No target selected for {skill.name}!")
                return False
            # Verify target is in range
            max_range = getattr(skill, "range_tiles", 1)
            distance = abs(target_unit.gx - unit.gx) + abs(target_unit.gy - unit.gy)
            if distance > max_range:
                if not for_ai:
                    self._log(f"{target_unit.name} is out of range for {skill.name}!")
                return False

        # Check and consume resource costs
        can_use, error_msg = unit.has_resources_for_skill(skill)
        if not can_use:
            if not for_ai and error_msg:
                self._log(error_msg)
            return False
        
        unit.consume_resources_for_skill(skill)

        # Apply damage if any
        damage = 0
        if skill.base_power > 0 and target_unit is not None and target_unit is not unit:
            base = unit.attack_power
            dmg = base * skill.base_power
            if skill.uses_skill_power:
                sp = float(getattr(unit.entity, "skill_power", 1.0))
                dmg *= max(DEFAULT_MIN_SKILL_POWER, sp)
            damage = self.combat.apply_damage(unit, target_unit, int(dmg))
            
            # Handle life drain healing
            if skill.id == "life_drain" and damage > 0:
                heal_amount = max(1, int(damage * 0.5))
                current_hp = getattr(unit.entity, "hp", 0)
                max_hp = getattr(unit.entity, "max_hp", 1)
                new_hp = min(max_hp, current_hp + heal_amount)
                setattr(unit.entity, "hp", new_hp)
                if new_hp > current_hp:
                    self._log(f"{unit.name} drains {heal_amount} HP from {target_unit.name}!")

        # Apply statuses
        if skill.make_self_status is not None:
            self._add_status(unit, skill.make_self_status())
        if skill.make_target_status is not None and target_unit is not None:
            self._add_status(target_unit, skill.make_target_status())

        # Set cooldown
        if skill.cooldown > 0:
            unit.cooldowns[skill.id] = skill.cooldown

        # Messaging & win/loss checks
        if damage > 0 and target_unit is not None and target_unit is not unit:
            if not target_unit.is_alive:
                if target_unit.side == "enemy":
                    if not any(u.is_alive for u in self.enemy_units):
                        self.status = "victory"
                        self._log(
                            f"{unit.name} uses {skill.name} and defeats the enemy party!"
                        )
                        return True
                    else:
                        self._log(
                            f"{unit.name} uses {skill.name} and slays {target_unit.name} "
                            f"({damage} dmg)."
                        )
                else:
                    if not any(u.is_alive for u in self.player_units):
                        self.status = "defeat"
                        self._log(
                            f"{unit.name} uses {skill.name} for {damage} dmg. You fall..."
                        )
                        return True
                    else:
                        self._log(
                            f"{unit.name} uses {skill.name} and fells {target_unit.name} "
                            f"({damage} dmg)."
                        )
            else:
                self._log(f"{unit.name} uses {skill.name} on {target_unit.name} for {damage} dmg.")
        else:
            if skill.id == "guard":
                self._log(f"{unit.name} braces for impact.")
            else:
                self._log(f"{unit.name} uses {skill.name}.")

        self._next_turn()
        return True

    # ------------ Targeting system ------------

    def _enter_targeting_mode(self, unit: BattleUnit, action_type: Literal["attack", "skill"], skill: Optional[Skill] = None) -> bool:
        """
        Enter targeting mode for the given unit and action.
        Returns True if targeting mode was entered (valid targets found), False otherwise.
        """
        # For skills, check cooldown and resources first
        if action_type == "skill" and skill is not None:
            # Check cooldown
            cd = unit.cooldowns.get(skill.id, 0)
            if cd > 0:
                self._log(f"{skill.name} is on cooldown ({cd} turns).")
                return False
            
            # Check resources
            can_use, error_msg = unit.has_resources_for_skill(skill)
            if not can_use:
                if error_msg:
                    self._log(error_msg)
                return False
            
            # Self-targeting skills don't need targeting mode - execute immediately
            if skill.target_mode == "self":
                self._use_skill(unit, skill)
                return False
        
        # Determine valid targets based on action type
        valid_targets: List[BattleUnit] = []
        
        if action_type == "attack":
            weapon_range = self.combat._get_weapon_range(unit)
            valid_targets = self._enemies_in_range(unit, weapon_range)
        elif action_type == "skill" and skill is not None:
            if skill.target_mode == "adjacent_enemy":
                max_range = getattr(skill, "range_tiles", 1)
                valid_targets = self._enemies_in_range(unit, max_range)
        
        if not valid_targets:
            # No valid targets - can't enter targeting mode
            if action_type == "attack":
                weapon_range = self.combat._get_weapon_range(unit)
                if weapon_range > 1:
                    self._log(f"No enemy in range! (weapon range: {weapon_range})")
                else:
                    self._log("No enemy in range!")
            elif skill:
                self._log(f"No enemy in range for {skill.name}!")
            return False
        
        # Enter targeting mode
        self.targeting_mode = {
            "action_type": action_type,
            "skill": skill,
            "targets": valid_targets,
            "target_index": 0,  # Start with first target
        }
        return True

    def _exit_targeting_mode(self) -> None:
        """Exit targeting mode without executing an action."""
        self.targeting_mode = None

    def _get_current_target(self) -> Optional[BattleUnit]:
        """Get the currently selected target in targeting mode."""
        if self.targeting_mode is None:
            return None
        targets = self.targeting_mode.get("targets", [])
        target_index = self.targeting_mode.get("target_index", 0)
        if targets and 0 <= target_index < len(targets):
            return targets[target_index]
        return None

    # Damage preview method has been moved to engine.battle.combat.BattleCombat.get_damage_preview

    def _cycle_target(self, direction: int) -> None:
        """
        Cycle to next/previous target in targeting mode.
        direction: 1 for next, -1 for previous.
        """
        if self.targeting_mode is None:
            return
        targets = self.targeting_mode.get("targets", [])
        if not targets:
            return
        current_index = self.targeting_mode.get("target_index", 0)
        new_index = (current_index + direction) % len(targets)
        self.targeting_mode["target_index"] = new_index

    def _execute_targeted_action(self) -> bool:
        """
        Execute the action that's pending in targeting mode.
        Returns True if action was executed, False otherwise.
        """
        if self.targeting_mode is None:
            return False
        
        unit = self._active_unit()
        if unit.side != "player":
            return False
        
        target = self._get_current_target()
        if target is None:
            return False
        
        action_type = self.targeting_mode.get("action_type")
        skill = self.targeting_mode.get("skill")
        
        # Execute the action
        executed = False
        if action_type == "attack":
            self._perform_basic_attack_targeted(unit, target)
            executed = True
        elif action_type == "skill" and skill is not None:
            executed = self._use_skill_targeted(unit, skill, target)
        
        # Exit targeting mode after execution
        if executed:
            self._exit_targeting_mode()
        
        return executed

    # ------------ Turn helpers ------------

    def _next_turn(self) -> None:
        if self.status != "ongoing":
            return

        # Clear targeting mode and movement mode when turn changes
        self._exit_targeting_mode()
        self._exit_movement_mode()

        alive_units = [u for u in self.turn_order if u.is_alive]
        if not any(u.side == "enemy" for u in alive_units):
            self.status = "victory"
            return
        if not any(u.side == "player" for u in alive_units):
            self.status = "defeat"
            return

        for _ in range(len(self.turn_order)):
            self.turn_index = (self.turn_index + 1) % len(self.turn_order)
            unit = self.turn_order[self.turn_index]
            if unit.is_alive:
                self.turn = unit.side
                if unit.side == "enemy":
                    # Apply battle speed multiplier when resetting timer
                    config = get_config()
                    battle_speed = getattr(config, "battle_speed", 1.0)
                    self.enemy_timer = BATTLE_ENEMY_TIMER / battle_speed
                else:
                    self.enemy_timer = 0.0
                self._on_unit_turn_start(unit)
                return

        self.status = "victory"

    # ------------ Player actions ------------

    def _perform_move(self, unit: BattleUnit, dx: int, dy: int) -> None:
        """
        Legacy single-step movement. Still works but consumes movement points.
        """
        if self._is_stunned(unit):
            self._log(f"{unit.name} is stunned and cannot move!")
            self._next_turn()
            return

        if self._try_move_unit(unit, dx, dy):
            self._log(f"{unit.name} moves.")
            # Don't end turn if movement points remain
            if unit.current_movement_points <= 0:
                self._next_turn()
        else:
            self._log("You can't move there.")
    
    def _enter_movement_mode(self, unit: BattleUnit) -> None:
        """Enter movement mode to select destination with pathfinding."""
        if unit.current_movement_points <= 0:
            self._log(f"{unit.name} has no movement points remaining!")
            return
        
        self.movement_mode = True
        self.movement_target = (unit.gx, unit.gy)  # Start at current position
        self.movement_path = [(unit.gx, unit.gy)]
        self.movement_key_press_count = 0  # Reset press counter
        self._update_movement_path(unit)
    
    def _exit_movement_mode(self) -> None:
        """Exit movement mode."""
        self.movement_mode = False
        self.movement_target = None
        self.movement_path = []
        self.mouse_hover_cell = None
        self.movement_key_press_count = 0
    
    def _update_movement_path(self, unit: BattleUnit) -> None:
        """Update the movement path preview based on current target."""
        if not self.movement_mode or self.movement_target is None:
            return
        
        target_gx, target_gy = self.movement_target
        path = self.pathfinding.find_path(unit, target_gx, target_gy)
        if path:
            self.movement_path = path
        else:
            # Pathfinding failed (out of bounds, obstacle, etc.) - reset to starting position
            # but keep movement mode active so player can plan a different route
            self.movement_path = [(unit.gx, unit.gy)]
            # Reset target back to starting position
            self.movement_target = (unit.gx, unit.gy)
            # Reset press counter so looping behavior restarts
            self.movement_key_press_count = 0
    
    def _confirm_movement(self, unit: BattleUnit) -> None:
        """Confirm and execute movement along the current path."""
        if not self.movement_mode or not self.movement_path:
            return
        
        if len(self.movement_path) <= 1:
            self._exit_movement_mode()
            return
        
        if self._move_unit_along_path(unit, self.movement_path):
            path_length = len(self.movement_path) - 1
            self._log(f"{unit.name} moves {path_length} square(s).")
            self._exit_movement_mode()
            # End turn if no movement points remain
            if unit.current_movement_points <= 0:
                self._next_turn()
        else:
            self._log("Not enough movement points for that path!")

    def _perform_basic_attack(self, unit: BattleUnit, target: Optional[BattleUnit] = None) -> None:
        """Perform basic attack with auto-targeting (for AI and backwards compatibility). Delegates to AI module."""
        self.ai.perform_basic_attack(unit, target)

    def _perform_basic_attack_targeted(self, unit: BattleUnit, target_unit: BattleUnit) -> None:
        """Perform basic attack on a specific target. Delegates to AI module."""
        self.ai.perform_basic_attack_targeted(unit, target_unit)

    # ------------ Input ------------

    def _screen_to_grid(self, screen_x: int, screen_y: int) -> Optional[tuple[int, int]]:
        """Convert screen coordinates to grid coordinates. Returns None if outside grid."""
        gx = (screen_x - self.grid_origin_x) // self.cell_size
        gy = (screen_y - self.grid_origin_y) // self.cell_size
        
        if 0 <= gx < self.grid_width and 0 <= gy < self.grid_height:
            return (gx, gy)
        return None

    def handle_event(self, game, event: pygame.event.Event) -> None:
        """Main event handler that delegates to specialized handlers."""
        # Handle mouse events first
        if self._handle_mouse_events(event):
            return
        
        # Only process keyboard events from here
        if event.type != pygame.KEYDOWN:
            return

        input_manager = getattr(game, "input_manager", None)

        # Handle UI toggles (tutorial, log history)
        if self._handle_ui_toggles(event, input_manager):
            return

        # Handle battle end input (defeat/victory)
        if self._handle_battle_end_input(event, input_manager):
            return

        unit = self._active_unit()
        if unit.side != "player":
            return

        # Handle movement mode input
        if self._handle_movement_mode_input(event, unit, input_manager):
            return

        # Handle targeting mode input
        if self._handle_targeting_mode_input(event, input_manager):
            return

        # Handle action input (movement, attack, guard, skills)
        self._handle_action_input(event, unit, input_manager)

    def _handle_mouse_events(self, event: pygame.event.Event) -> bool:
        """Handle mouse events (wheel, motion, clicks). Returns True if event was handled."""
        # Handle mouse wheel for tutorial scrolling
        if event.type == pygame.MOUSEWHEEL:
            if self.show_tutorial:
                # Scroll tutorial (negative y means scroll up)
                self.tutorial_scroll_offset = max(0, self.tutorial_scroll_offset - event.y * 30)
                return True
        
        # Handle mouse motion for path preview
        if event.type == pygame.MOUSEMOTION:
            unit = self._active_unit()
            if unit and unit.side == "player" and self.status == "ongoing" and self.movement_mode:
                grid_pos = self._screen_to_grid(event.pos[0], event.pos[1])
                if grid_pos:
                    gx, gy = grid_pos
                    reachable = self.pathfinding.get_reachable_cells(unit)
                    if (gx, gy) in reachable:
                        self.mouse_hover_cell = (gx, gy)
                        self.movement_target = (gx, gy)
                        self._update_movement_path(unit)
                    else:
                        self.mouse_hover_cell = None
                else:
                    self.mouse_hover_cell = None
            return True
        
        # Handle mouse clicks for movement and targeting
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                unit = self._active_unit()
                if unit and unit.side == "player" and self.status == "ongoing":
                    # Get grid coordinates from mouse click
                    grid_pos = self._screen_to_grid(event.pos[0], event.pos[1])
                    
                    # Check if we're in targeting mode
                    if self.targeting_mode is not None:
                        # In targeting mode - check if clicked on a valid target
                        if grid_pos:
                            gx, gy = grid_pos
                            valid_targets = self.targeting_mode.get("targets", [])
                            # Find which target unit is at this grid position
                            clicked_target = None
                            for target_unit in valid_targets:
                                if target_unit.gx == gx and target_unit.gy == gy:
                                    clicked_target = target_unit
                                    break
                            
                            if clicked_target:
                                # Select this target and execute action
                                target_index = valid_targets.index(clicked_target)
                                self.targeting_mode["target_index"] = target_index
                                self._execute_targeted_action()
                            else:
                                # Clicked outside valid targets - cancel targeting
                                self._exit_targeting_mode()
                        else:
                            # Clicked outside grid - cancel targeting
                            self._exit_targeting_mode()
                        return True
                    
                    # Not in targeting mode - handle movement
                    if not self.movement_mode:
                        # Auto-enter movement mode if not already in it
                        if unit.current_movement_points > 0:
                            self._enter_movement_mode(unit)
                    
                    if grid_pos:
                        gx, gy = grid_pos
                        # Check if clicked cell is reachable
                        reachable = self.pathfinding.get_reachable_cells(unit)
                        if (gx, gy) in reachable:
                            # Set target and update path
                            self.movement_target = (gx, gy)
                            self._update_movement_path(unit)
                            # Auto-confirm movement if path is valid
                            if self.movement_path and len(self.movement_path) > 1:
                                self._confirm_movement(unit)
                        elif self.movement_mode:
                            # Clicked outside reachable area - cancel movement mode
                            self._exit_movement_mode()
            return True
        
        return False

    def _handle_ui_toggles(self, event: pygame.event.Event, input_manager) -> bool:
        """Handle UI toggle events (tutorial, log history). Returns True if event was handled."""
        # Tutorial toggle (H key) - works at any time
        if event.key == pygame.K_h:
            self.show_tutorial = not self.show_tutorial
            if self.show_tutorial:
                self.show_log_history = False  # Close log history if opening tutorial
            return True
        
        # Log history toggle (L key) - works at any time
        if event.key == pygame.K_l:
            self.show_log_history = not self.show_log_history
            if self.show_log_history:
                self.show_tutorial = False  # Close tutorial if opening log history
            return True
        
        # If tutorial is showing, handle scrolling and closing
        if self.show_tutorial:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_h:
                self.show_tutorial = False
                self.tutorial_scroll_offset = 0  # Reset scroll when closing
                return True
            # Handle scrolling with arrow keys
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.tutorial_scroll_offset = max(0, self.tutorial_scroll_offset - 20)
                return True
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.tutorial_scroll_offset += 20
                return True
            if event.key == pygame.K_PAGEUP:
                self.tutorial_scroll_offset = max(0, self.tutorial_scroll_offset - 200)
                return True
            if event.key == pygame.K_PAGEDOWN:
                self.tutorial_scroll_offset += 200
                return True
        
        # If log history is showing, only allow closing it
        if self.show_log_history:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_l:
                self.show_log_history = False
                return True
        
        return False

    def _handle_battle_end_input(self, event: pygame.event.Event, input_manager) -> bool:
        """Handle input when battle is ended (defeat/victory). Returns True if event was handled."""
        # If battle is already resolved, only listen for simple confirmations.
        if self.status == "defeat":
            # Keep the original behaviour: R to leave / restart.
            if event.key == pygame.K_r:
                self.finished = True
            return True

        if self.status == "victory":
            # Any generic "confirm" key (Enter/Space by default) will exit.
            if input_manager is not None:
                if input_manager.event_matches_action(InputAction.CONFIRM, event):
                    self.finished = True
            else:
                if event.key == pygame.K_SPACE:
                    self.finished = True
            return True
        
        return False

    def _handle_movement_mode_input(self, event: pygame.event.Event, unit: BattleUnit, input_manager) -> bool:
        """Handle input when in movement mode. Returns True if event was handled."""
        if not self.movement_mode:
            return False
        
        # Cancel movement mode (X key, not ESC - ESC is for pause menu)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CANCEL, event):
                self._exit_movement_mode()
                return True
        else:
            if event.key == pygame.K_x:
                self._exit_movement_mode()
                return True
        
        # Confirm movement
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CONFIRM, event):
                self._confirm_movement(unit)
                return True
        else:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._confirm_movement(unit)
                return True
        
        # Move cursor to select destination
        if self.movement_target is not None:
            target_gx, target_gy = self.movement_target
            moved = False
            direction = None  # Track direction for looping
            
            if input_manager is not None:
                if input_manager.event_matches_action(InputAction.MOVE_UP, event):
                    target_gy = max(0, target_gy - 1)
                    moved = True
                    direction = (0, -1)
                elif input_manager.event_matches_action(InputAction.MOVE_DOWN, event):
                    target_gy = min(self.grid_height - 1, target_gy + 1)
                    moved = True
                    direction = (0, 1)
                elif input_manager.event_matches_action(InputAction.MOVE_LEFT, event):
                    target_gx = max(0, target_gx - 1)
                    moved = True
                    direction = (-1, 0)
                elif input_manager.event_matches_action(InputAction.MOVE_RIGHT, event):
                    target_gx = min(self.grid_width - 1, target_gx + 1)
                    moved = True
                    direction = (1, 0)
            else:
                if event.key in (pygame.K_UP, pygame.K_w):
                    target_gy = max(0, target_gy - 1)
                    moved = True
                    direction = (0, -1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    target_gy = min(self.grid_height - 1, target_gy + 1)
                    moved = True
                    direction = (0, 1)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    target_gx = max(0, target_gx - 1)
                    moved = True
                    direction = (-1, 0)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    target_gx = min(self.grid_width - 1, target_gx + 1)
                    moved = True
                    direction = (1, 0)
            
            if moved:
                self.movement_key_press_count += 1
                
                # On the 4th press (and every 4th press after), loop back to first movement point and continue in same direction
                if self.movement_key_press_count % 4 == 0 and len(self.movement_path) > 1:
                    # Get the first movement point (second element, since first is starting position)
                    if len(self.movement_path) >= 2:
                        first_move = self.movement_path[1]
                        # Continue in the same direction from the first move point
                        loop_gx = first_move[0] + direction[0]
                        loop_gy = first_move[1] + direction[1]
                        # Clamp to grid bounds
                        loop_gx = max(0, min(self.grid_width - 1, loop_gx))
                        loop_gy = max(0, min(self.grid_height - 1, loop_gy))
                        target_gx, target_gy = loop_gx, loop_gy
                
                self.movement_target = (target_gx, target_gy)
                self._update_movement_path(unit)
                
                # If pathfinding failed (path only has starting position), reset target and counter
                # but keep movement mode active so player can plan a different route
                if len(self.movement_path) <= 1 and self.movement_target != (unit.gx, unit.gy):
                    # Path is invalid - reset to starting position
                    self.movement_target = (unit.gx, unit.gy)
                    self.movement_key_press_count = 0
                    self._update_movement_path(unit)
                
                return True
        
        return False

    def _handle_targeting_mode_input(self, event: pygame.event.Event, input_manager) -> bool:
        """Handle input when in targeting mode. Returns True if event was handled."""
        if self.targeting_mode is None:
            return False
        
        # Cancel targeting mode (X key, not ESC - ESC is for pause menu)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CANCEL, event):
                self._exit_targeting_mode()
                return True
        else:
            if event.key == pygame.K_x:
                self._exit_targeting_mode()
                return True
        
        # Confirm target selection
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.CONFIRM, event):
                self._execute_targeted_action()
                return True
        else:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._execute_targeted_action()
                return True
        
        # Cycle through targets
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.MOVE_UP, event) or \
               input_manager.event_matches_action(InputAction.MOVE_LEFT, event) or \
               input_manager.event_matches_action(InputAction.SCROLL_UP, event):
                self._cycle_target(-1)
                return True
            if input_manager.event_matches_action(InputAction.MOVE_DOWN, event) or \
               input_manager.event_matches_action(InputAction.MOVE_RIGHT, event) or \
               input_manager.event_matches_action(InputAction.SCROLL_DOWN, event):
                self._cycle_target(1)
                return True
        else:
            # Fallback key handling for targeting
            if event.key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w, pygame.K_a):
                self._cycle_target(-1)
                return True
            if event.key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_s, pygame.K_d):
                self._cycle_target(1)
                return True
            if event.key == pygame.K_TAB:
                self._cycle_target(1)
                return True
        
        # In targeting mode, ignore other inputs
        return True

    def _handle_action_input(self, event: pygame.event.Event, unit: BattleUnit, input_manager) -> None:
        """Handle action input (movement, attack, guard, skills)."""
        # Exit movement mode if entering other actions
        if self.movement_mode:
            # Any non-movement action cancels movement mode
            if input_manager is not None:
                if (input_manager.event_matches_action(InputAction.BASIC_ATTACK, event) or
                    input_manager.event_matches_action(InputAction.GUARD, event) or
                    any(input_manager.event_matches_action(getattr(InputAction, f"SKILL_{i}"), event) for i in range(1, MAX_SKILL_SLOTS + 1))):
                    self._exit_movement_mode()
            else:
                if event.key == pygame.K_SPACE or event.key == pygame.K_g:
                    self._exit_movement_mode()

        # Movement mode entry (M key)
        if event.key == pygame.K_m:
            if self.movement_mode:
                self._exit_movement_mode()
            else:
                self._enter_movement_mode(unit)
            return

        # Movement (logical actions) - only when not targeting
        # Single-step movement still works (legacy support)
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.MOVE_UP, event):
                self._perform_move(unit, 0, -1)
                return
            if input_manager.event_matches_action(InputAction.MOVE_DOWN, event):
                self._perform_move(unit, 0, 1)
                return
            if input_manager.event_matches_action(InputAction.MOVE_LEFT, event):
                self._perform_move(unit, -1, 0)
                return
            if input_manager.event_matches_action(InputAction.MOVE_RIGHT, event):
                self._perform_move(unit, 1, 0)
                return
        else:
            move_keys = {
                pygame.K_UP: (0, -1),
                pygame.K_w: (0, -1),
                pygame.K_DOWN: (0, 1),
                pygame.K_s: (0, 1),
                pygame.K_LEFT: (-1, 0),
                pygame.K_a: (-1, 0),
                pygame.K_RIGHT: (1, 0),
                pygame.K_d: (1, 0),
            }
            if event.key in move_keys:
                dx, dy = move_keys[event.key]
                self._perform_move(unit, dx, dy)
                return

        # Basic attack - enter targeting mode
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.BASIC_ATTACK, event):
                if not self._enter_targeting_mode(unit, "attack"):
                    # No valid targets, can't enter targeting mode
                    pass
                return
        else:
            if event.key == pygame.K_SPACE:
                if not self._enter_targeting_mode(unit, "attack"):
                    # No valid targets, can't enter targeting mode
                    pass
                return

        # Guard (dedicated action) - no targeting needed
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.GUARD, event):
                guard_skill = unit.skills.get("guard")
                if guard_skill is not None:
                    self._use_skill(unit, guard_skill)
                    return

        # Skills (hotbar-style) - enter targeting mode
        skill = None
        if input_manager is not None:
            # First try to resolve by logical slot → skill id.
            if input_manager.event_matches_action(InputAction.SKILL_1, event):
                skill = self._skill_for_action(unit, InputAction.SKILL_1)
            elif input_manager.event_matches_action(InputAction.SKILL_2, event):
                skill = self._skill_for_action(unit, InputAction.SKILL_2)
            elif input_manager.event_matches_action(InputAction.SKILL_3, event):
                skill = self._skill_for_action(unit, InputAction.SKILL_3)
            elif input_manager.event_matches_action(InputAction.SKILL_4, event):
                skill = self._skill_for_action(unit, InputAction.SKILL_4)

            # If we have an input manager but no slot mapping yet (older saves /
            # future weirdness), fall back to key-based lookup.
            if skill is None:
                skill = self._skill_for_key(unit, event.key)
        else:
            # No input manager: direct keybinding on skills.
            skill = self._skill_for_key(unit, event.key)

        if skill is not None:
            # Self-targeting skills execute immediately, others enter targeting mode
            if skill.target_mode == "self":
                self._use_skill(unit, skill)
            else:
                if not self._enter_targeting_mode(unit, "skill", skill=skill):
                    # No valid targets or skill on cooldown/insufficient resources
                    pass
            return

    # ------------ Enemy AI ------------

    def _allies_in_range(self, unit: BattleUnit, max_range: int) -> List[BattleUnit]:
        """Return all ally units within range (for support skills). Delegates to AI module."""
        return self.ai.allies_in_range(unit, max_range)

    def _get_ai_profile(self, unit: BattleUnit) -> str:
        """Get the AI profile for an enemy unit. Delegates to AI module."""
        return self.ai.get_ai_profile(unit)

    def _choose_target_by_priority(self, unit: BattleUnit, targets: List[BattleUnit]) -> Optional[BattleUnit]:
        """Choose target based on AI profile and tactical priorities. Delegates to AI module."""
        return self.ai.choose_target_by_priority(unit, targets)

    def _find_injured_ally(self, unit: BattleUnit, max_range: int = 1) -> Optional[BattleUnit]:
        """Find an injured ally within range (for healing). Delegates to AI module."""
        return self.ai.find_injured_ally(unit, max_range)

    def _find_ally_to_buff(self, unit: BattleUnit, max_range: int = 1) -> Optional[BattleUnit]:
        """Find an ally that could benefit from buffs (not already buffed). Delegates to AI module."""
        return self.ai.find_ally_to_buff(unit, max_range)

    def update(self, dt: float) -> None:
        if self.status != "ongoing":
            return
        
        # Update animation time for pulsing effects
        self.animation_time += dt

        # Update floating damage numbers
        for damage_info in self._floating_damage[:]:
            damage_info["timer"] -= dt
            # Crits float faster and higher (slightly slower for longer visibility)
            speed = 45 if damage_info.get("is_crit", False) else 35
            damage_info["y_offset"] += dt * speed
            if damage_info["timer"] <= 0:
                self._floating_damage.remove(damage_info)
        
        # Update hit sparks
        for spark in self._hit_sparks[:]:
            spark["timer"] -= dt
            if spark["timer"] <= 0:
                self._hit_sparks.remove(spark)

        unit = self._active_unit()

        # Only enemies act automatically; players/companions are driven by input.
        if unit.side != "enemy":
            return

        self.enemy_timer -= dt
        if self.enemy_timer > 0.0:
            return

        # Execute AI turn
        self.ai.execute_ai_turn(unit)

    # ------------ Drawing ------------
    # All drawing methods have been moved to engine.battle.renderer.BattleRenderer

    def draw(self, surface: pygame.Surface, game=None) -> None:
        surface.fill((5, 5, 10))
        screen_w, screen_h = surface.get_size()

        # ------------------------------------------------------------------
        # 1) Decide where the grid lives (centered between top info and bottom UI)
        # ------------------------------------------------------------------
        grid_px_w = self.grid_width * self.cell_size
        grid_px_h = self.grid_height * self.cell_size

        top_ui_height = 150  # space for Party/Enemy HP, Turn, Active, Turn Order, etc.
        # Bottom UI: hint line (20px) + gap (8px) + max log (6 lines * 20px = 120px) + margin (20px)
        bottom_ui_height = 168  # space for log + gap + key hints

        available_h = max(0, screen_h - top_ui_height - bottom_ui_height)

        self.grid_origin_x = (screen_w - grid_px_w) // 2
        # Center the grid in the middle band, but never above the top_ui area
        self.grid_origin_y = top_ui_height + max(0, (available_h - grid_px_h) // 2)

        # ------------------------------------------------------------------
        # 2) Grid + units
        # ------------------------------------------------------------------
        self.renderer.draw_grid(surface)
        self.renderer.draw_units(surface, screen_w)
        
        # ---------------- Targeting overlays (drawn after units) ----------------
        # ---------------- Damage preview (when targeting) ----------------
        if self.targeting_mode is not None:
            current_target = self._get_current_target()
            if current_target is not None:
                active_unit = self._active_unit()
                if active_unit is not None:
                    normal_dmg, crit_dmg = self.combat.get_damage_preview(active_unit, current_target)
                    if normal_dmg is not None:
                        self.renderer.draw_damage_preview(surface, current_target, normal_dmg, crit_dmg)
                        self.renderer.draw_enemy_info_panel(surface, current_target, screen_w)
        
        # ---------------- Range visualization (when targeting) ----------------
        if self.targeting_mode is not None:
            active_unit = self._active_unit()
            if active_unit is not None:
                self.renderer.draw_range_visualization(surface, active_unit)

        # ------------------------------------------------------------------
        # 3) Top UI: party / enemy unit cards + active unit panel
        # ------------------------------------------------------------------
        active_unit = self._active_unit() if self.status == "ongoing" and self.turn_order else None
        
        # Party unit cards (left side)
        party_x = 20
        party_y = 20
        card_width = 180
        card_spacing = 10
        
        for idx, unit in enumerate(self.player_units):
            if not unit.is_alive:
                continue
            is_active = (active_unit == unit)
            _draw_battle_unit_card(
                surface,
                self.font,
                party_x,
                party_y + idx * (70 + card_spacing),
                card_width,
                unit.name,
                unit.hp,
                unit.max_hp,
                getattr(unit, "current_stamina", 0),
                getattr(unit, "max_stamina", 0),
                getattr(unit, "current_mana", 0),
                getattr(unit, "max_mana", 0),
                is_active=is_active,
                is_player=True,
                statuses=getattr(unit, "statuses", []),
            )
        
        # Enemy unit cards (right side)
        enemy_x = screen_w - card_width - 20
        enemy_y = 20
        
        for idx, unit in enumerate(self.enemy_units):
            if not unit.is_alive:
                continue
            is_active = (active_unit == unit)
            _draw_battle_unit_card(
                surface,
                self.font,
                enemy_x,
                enemy_y + idx * (70 + card_spacing),
                card_width,
                unit.name,
                unit.hp,
                unit.max_hp,
                getattr(unit, "current_stamina", 0),
                getattr(unit, "max_stamina", 0),
                getattr(unit, "current_mana", 0),
                getattr(unit, "max_mana", 0),
                is_active=is_active,
                is_player=False,
                statuses=getattr(unit, "statuses", []),
            )
        
        # Active unit HUD panel (center top) - keep existing for detailed info
        self.renderer.draw_active_unit_panel(surface, active_unit, screen_w)
        
        # Turn indicator (center, above active panel)
        if self.status == "ongoing" and self.turn_order:
            side_label = active_unit.side if active_unit else "-"
        else:
            side_label = "-"
        
        turn_text = self.font.render(
            f"Turn: {side_label.upper()}",
            True,
            (200, 200, 255),
        )
        turn_x = (screen_w - turn_text.get_width()) // 2
        surface.blit(turn_text, (turn_x, 8))
        
        # Turn order indicator (show next 3-4 units)
        if self.status == "ongoing":
            self.renderer.draw_turn_order_indicator(surface, screen_w)

        # ------------------------------------------------------------------
        # 4) Bottom UI: combat log + key hints
        # ------------------------------------------------------------------
        line_height = 20
        bottom_margin = 20
        hint_height = 20
        log_hint_gap = 8  # Gap between log and hint line

        # Where the hint line will sit (just above bottom margin)
        hint_y = screen_h - bottom_margin - hint_height

        # Decide where the log starts: just above the hint, but also below the grid
        log_lines = self.log[-self.max_log_lines:]
        log_total_height = line_height * len(log_lines)

        grid_bottom_y = self.grid_origin_y + grid_px_h
        
        # Calculate log position: below grid, but above hint with proper spacing
        # We want the log to end at least `log_hint_gap` pixels above the hint line
        desired_log_bottom = hint_y - log_hint_gap
        desired_log_top = desired_log_bottom - log_total_height
        
        # But also ensure it's below the grid
        min_log_top = grid_bottom_y + 10
        
        # Use the higher of the two (which ensures it's below grid)
        # But if that would cause overlap with hint, clamp it
        log_y_start = max(min_log_top, desired_log_top)
        
        # Final check: ensure log doesn't overlap with hint
        log_bottom = log_y_start + log_total_height
        if log_bottom > hint_y - log_hint_gap:
            # Not enough space - reduce log lines shown to fit
            available_height = hint_y - log_hint_gap - log_y_start
            max_fittable_lines = max(1, available_height // line_height)
            if max_fittable_lines < len(log_lines):
                log_lines = log_lines[-max_fittable_lines:]
                log_total_height = line_height * len(log_lines)
                # Recalculate log position with new height
                log_y_start = hint_y - log_hint_gap - log_total_height
                # But still ensure it's below the grid
                log_y_start = max(min_log_top, log_y_start)
        
        log_y = log_y_start

        # Draw log on the left side (hotbar will be on right)
        log_x = 40  # Left side
        for msg in log_lines:
            _draw_battle_log_line(surface, self.font, log_x, log_y, msg)
            log_y += line_height

        # ------------------------------------------------------------------
        # 5) Status prompts / key hints OR end-of-battle messages
        # ------------------------------------------------------------------
        if self.status == "ongoing":
            active = self._active_unit() if self.turn_order else None

            # We may or may not have a Game / InputManager (defensive)
            input_manager = None
            if game is not None:
                input_manager = getattr(game, "input_manager", None)

            name_prefix = "Party"
            
            if active is not None and active.side == "player":
                name_prefix = active.name

            # Draw skill hotbar if it's a player unit's turn (right side, log is on left)
            if active is not None and active.side == "player":
                # Get input manager for key bindings
                input_manager = None
                if game is not None:
                    input_manager = getattr(game, "input_manager", None)
                
                # Only show hotbar when not in targeting mode
                if self.targeting_mode is None:
                    # Draw hotbar in a more prominent position - center-bottom, above hint line
                    skill_slots = getattr(active, "skill_slots", [])
                    slot_width = 140  # Match the new size in hud_battle.py
                    slot_spacing = 12
                    hotbar_w = len(skill_slots) * (slot_width + slot_spacing) - slot_spacing
                    # Center the hotbar horizontally
                    hotbar_x = (screen_w - hotbar_w) // 2
                    # Position it prominently above the hint line with more spacing
                    hotbar_y = hint_y - 120
                    _draw_battle_skill_hotbar(
                        surface,
                        self.font,
                        hotbar_x,
                        hotbar_y,
                        active.skills,
                        skill_slots,
                        getattr(active, "cooldowns", {}),
                        getattr(active, "current_stamina", 0),
                        getattr(active, "max_stamina", 0),
                        getattr(active, "current_mana", 0),
                        getattr(active, "max_mana", 0),
                        input_manager,
                    )
            
            # Show targeting instructions or normal hints
            if self.targeting_mode is not None:
                # Targeting mode hints
                target = self._get_current_target()
                action_type = self.targeting_mode.get("action_type", "attack")
                skill = self.targeting_mode.get("skill")
                
                action_name = skill.name if skill else "Attack"
                target_name = target.name if target else "None"
                
                # Get key bindings for hints
                confirm_key = "SPACE"
                cancel_key = "X"  # X is now the cancel key (ESC is for pause menu)
                cycle_key = "ARROWS/TAB"
                if input_manager is not None:
                    try:
                        confirm_keys = input_manager.get_bindings(InputAction.CONFIRM)
                        if confirm_keys:
                            confirm_key = pygame.key.name(list(confirm_keys)[0]).upper()
                        cancel_keys = input_manager.get_bindings(InputAction.CANCEL)
                        if cancel_keys:
                            cancel_key = pygame.key.name(list(cancel_keys)[0]).upper()
                    except (AttributeError, TypeError):
                        pass
                
                hint_text = self.font.render(
                    f"Targeting: {action_name} → {target_name} | {confirm_key} confirm | {cancel_key} cancel | {cycle_key} cycle",
                    True,
                    (255, 255, 150),
                )
            else:
                # Normal movement/action hints
                # --- Basic attack hint (Space or whatever it's bound to) ----
                atk_part = "SPACE atk"
                if input_manager is not None:
                    try:
                        atk_keys = input_manager.get_bindings(InputAction.BASIC_ATTACK)
                    except AttributeError:
                        atk_keys = set()
                    atk_labels: List[str] = []
                    for key in sorted(atk_keys):
                        atk_labels.append(pygame.key.name(key).upper())
                    if atk_labels:
                        atk_part = f"{'/'.join(atk_labels)} atk"
                
                # --- Guard hint (if unit has guard skill) ----
                guard_part = ""
                if active_unit and "guard" in active_unit.skills:
                    guard_key = "G"
                    if input_manager is not None:
                        try:
                            guard_keys = input_manager.get_bindings(InputAction.GUARD)
                            if guard_keys:
                                guard_labels = [pygame.key.name(k).upper() for k in sorted(guard_keys)]
                                if guard_labels:
                                    guard_key = "/".join(guard_labels)
                        except (AttributeError, TypeError):
                            pass
                    guard_part = f" | {guard_key} guard"
                
                hint_text = self.font.render(
                    f"{name_prefix}: move WASD/arrows | {atk_part}{guard_part}",
                    True,
                    (180, 180, 180),
                )
            surface.blit(hint_text, (40, hint_y))
            
            # Add tutorial hint
            tutorial_hint = self.font.render("Press H for combat tutorial", True, (120, 120, 150))
            surface.blit(tutorial_hint, (screen_w - tutorial_hint.get_width() - 40, hint_y))

        elif self.status == "defeat":
            dead_text = self.font.render(
                "You died - press R to restart",
                True,
                (255, 80, 80),
            )
            dead_x = 40
            dead_y = max(self.grid_origin_y - 30, 40)
            surface.blit(dead_text, (dead_x, dead_y))

        elif self.status == "victory":
            # Use the actual CONFIRM bindings for the victory hint
            confirm_part = "SPACE"
            input_manager = None
            if game is not None:
                input_manager = getattr(game, "input_manager", None)
            if input_manager is not None:
                confirm_keys = input_manager.get_bindings(InputAction.CONFIRM)
                labels: List[str] = [
                    pygame.key.name(k).upper() for k in sorted(confirm_keys)
                ]
                if labels:
                    confirm_part = "/".join(labels)

            win_text = self.font.render(
                f"Victory! Press {confirm_part} to continue.",
                True,
                (120, 220, 120),
            )
            win_x = 40
            win_y = max(self.grid_origin_y - 30, 40)
            surface.blit(win_text, (win_x, win_y))
        
        # Draw log history viewer if active
        if self.show_log_history:
            self.renderer.draw_log_history(surface)
        
        # Draw tutorial overlay if active (draws on top of everything, last)
        if self.show_tutorial:
            draw_combat_tutorial(surface, self.font, self)


