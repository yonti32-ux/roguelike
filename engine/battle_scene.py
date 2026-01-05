from collections import Counter
from dataclasses import dataclass, field
from typing import Literal, List, Dict, Optional, Union

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
    DEFAULT_COMPANION_HP_FACTOR,
    DEFAULT_COMPANION_ATTACK_FACTOR,
    DEFAULT_MIN_SKILL_POWER,
    BATTLE_ENEMY_START_COL_OFFSET,
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
from ui.hud import (
    _draw_battle_unit_card,
    _draw_battle_skill_hotbar,
    _draw_battle_log_line,
    _draw_status_indicators,
)


BattleStatus = Literal["ongoing", "victory", "defeat"]
Side = Literal["player", "enemy"]


@dataclass
class BattleUnit:
    """
    Wrapper around a world entity (Player or Enemy) for use on the battle grid.

    Keeps track of side, grid position, and combat state.
    """
    entity: Union[Player, Enemy]
    side: Side
    gx: int
    gy: int
    name: str = "Unit"

    statuses: List[StatusEffect] = field(default_factory=list)
    cooldowns: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, Skill] = field(default_factory=dict)
    # Optional hotbar-style layout; indices 0–3 map to SKILL_1..SKILL_4.
    skill_slots: List[str] = field(default_factory=list)

    # Current resource pools used by some skills.
    current_mana: int = 0
    current_stamina: int = 0

    @property
    def hp(self) -> int:
        return getattr(self.entity, "hp", 0)

    @property
    def max_hp(self) -> int:
        return getattr(self.entity, "max_hp", 0)

    @property
    def attack_power(self) -> int:
        return getattr(self.entity, "attack_power", 0)

    @property
    def max_mana(self) -> int:
        return getattr(self.entity, "max_mana", 0)

    @property
    def max_stamina(self) -> int:
        return getattr(self.entity, "max_stamina", 0)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def init_resources_from_entity(self) -> None:
        """Initialize current resource pools from entity's max values."""
        self.current_mana = self.max_mana
        self.current_stamina = self.max_stamina

    def regenerate_stamina(self, amount: int = 1) -> None:
        """
        Regenerate stamina (used at turn start).
        
        Args:
            amount: Amount to regenerate (default 1 per turn)
        """
        max_sta = self.max_stamina
        if max_sta > 0:
            self.current_stamina = min(max_sta, self.current_stamina + amount)

    def has_resources_for_skill(self, skill: Skill) -> tuple[bool, Optional[str]]:
        """
        Check if unit has enough resources to use a skill.
        
        Returns:
            Tuple of (can_use, error_message)
            - (True, None) if resources are sufficient
            - (False, "Not enough mana!") or (False, "Not enough stamina!") if insufficient
        """
        mana_cost = getattr(skill, "mana_cost", 0)
        stamina_cost = getattr(skill, "stamina_cost", 0)

        if mana_cost > 0 and self.current_mana < mana_cost:
            return False, "Not enough mana!"
        
        if stamina_cost > 0 and self.current_stamina < stamina_cost:
            return False, "Not enough stamina!"
        
        return True, None

    def consume_resources_for_skill(self, skill: Skill) -> None:
        """Deduct resource costs for using a skill."""
        mana_cost = getattr(skill, "mana_cost", 0)
        stamina_cost = getattr(skill, "stamina_cost", 0)

        if mana_cost > 0:
            self.current_mana = max(0, self.current_mana - mana_cost)
        if stamina_cost > 0:
            self.current_stamina = max(0, self.current_stamina - stamina_cost)



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
    ) -> None:
        self.player = player
        self.font = font

        # Grid configuration (battlefield, not dungeon grid)
        # Wider battlefield; origin is centered dynamically in draw().
        self.grid_width = BATTLE_GRID_WIDTH
        self.grid_height = BATTLE_GRID_HEIGHT
        self.cell_size = BATTLE_CELL_SIZE
        self.grid_origin_x = 0
        self.grid_origin_y = 0

        # --- Combat log ---
        self.log: List[str] = []
        self.max_log_lines: int = 6
        self.last_action: str = ""

        # Backwards-compatible alias for older game code
        self.combat_log = self.log

        # --- Player party: hero + companion ---

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

        # Core hero skills – now robust against missing registry
        hero_unit.skills = {}
        try:
            hero_unit.skills["guard"] = get_skill("guard")
        except KeyError:
            pass
        try:
            hero_unit.skills["power_strike"] = get_skill("power_strike")
            hero_unit.cooldowns["power_strike"] = 0  # ready
        except KeyError:
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

        # --- Player side: hero + companions from Game.party -----------------



        self.player_units: List[BattleUnit] = [hero_unit]

        # Base stats used to derive simple companion stats in P1
        base_max_hp = getattr(self.player, "max_hp", DEFAULT_PLAYER_MAX_HP)
        base_atk = getattr(self.player, "attack_power", DEFAULT_PLAYER_ATTACK)
        base_def = int(getattr(self.player, "defense", 0))
        base_sp = float(getattr(self.player, "skill_power", 1.0))

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
                        skills["guard"] = get_skill("guard")
                    except KeyError:
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

            try:
                companion_unit.skills = {
                    "guard": get_skill("guard"),
                }
            except KeyError:
                companion_unit.skills = {}

            # Auto-populate fallback companion hotbar as well.
            self._auto_assign_skill_slots(companion_unit)
            self.player_units.append(companion_unit)

        # --- Enemy side: create a unit per enemy in the encounter group ---
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
            # Simple default resource pools for enemies so stamina-based
            # skills can work without extra data wiring.
            enemy_max_mana = 0
            enemy_max_stamina = DEFAULT_ENEMY_STAMINA
            setattr(enemy, "max_mana", enemy_max_mana)
            setattr(enemy, "max_stamina", enemy_max_stamina)
            # Initialize resource pools from entity max values
            unit.init_resources_from_entity()

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

        # Turn state
        self.turn_order: List[BattleUnit] = self.player_units + self.enemy_units
        random.shuffle(self.turn_order)
        self.turn_index: int = 0
        self.turn: Side = self.turn_order[0].side if self.turn_order else "player"
        self.status: BattleStatus = "ongoing"
        self.finished: bool = False

        # Enemy AI timer – small delay so actions are readable
        self.enemy_timer: float = BATTLE_ENEMY_TIMER

        # Initialize cooldowns / statuses for first unit
        if self.turn_order:
            self._on_unit_turn_start(self.turn_order[0])

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

    def _incoming_multiplier(self, unit: BattleUnit) -> float:
        return incoming_multiplier(unit.statuses)

    def _outgoing_multiplier(self, unit: BattleUnit) -> float:
        return outgoing_multiplier(unit.statuses)

    def _has_dot(self, unit: BattleUnit) -> bool:
        """Return True if the unit has any damage-over-time status."""
        return any(s.flat_damage_each_turn > 0 for s in unit.statuses)


    def _add_status(self, unit: BattleUnit, status: StatusEffect) -> None:
        """
        Add or refresh a status on the unit.
        """
        for existing in unit.statuses:
            if existing.name == status.name:
                existing.duration = max(existing.duration, status.duration)
                existing.incoming_mult = status.incoming_mult
                existing.outgoing_mult = status.outgoing_mult
                existing.flat_damage_each_turn = status.flat_damage_each_turn
                existing.stunned = status.stunned
                existing.stacks = status.stacks
                return
        unit.statuses.append(status)
        self._log(f"{unit.name} is affected by {status.name}.")

    def _on_unit_turn_start(self, unit: BattleUnit) -> None:
        self._tick_statuses_on_turn_start(unit)
        for k in list(unit.cooldowns.keys()):
            if unit.cooldowns[k] > 0:
                unit.cooldowns[k] -= 1

        # Simple stamina regeneration each turn so skills recover over time.
        unit.regenerate_stamina(amount=1)

    # ----- Grid / movement helpers -----

    def _cell_blocked(self, gx: int, gy: int) -> bool:
        if gx < 0 or gy < 0 or gx >= self.grid_width or gy >= self.grid_height:
            return True
        for u in self._all_units():
            if not u.is_alive:
                continue
            if u.gx == gx and u.gy == gy:
                return True
        return False

    def _try_move_unit(self, unit: BattleUnit, dx: int, dy: int) -> bool:
        new_gx = unit.gx + dx
        new_gy = unit.gy + dy
        if self._cell_blocked(new_gx, new_gy):
            return False
        unit.gx = new_gx
        unit.gy = new_gy
        return True

    def _enemies_in_range(self, unit: BattleUnit, max_range: int) -> List[BattleUnit]:
        """
        Return all enemy units within a given Manhattan range.
        This prepares us for future ranged skills.
        """
        enemies = self.enemy_units if unit.side == "player" else self.player_units
        res: List[BattleUnit] = []
        for u in enemies:
            if not u.is_alive:
                continue
            dist = abs(u.gx - unit.gx) + abs(u.gy - unit.gy)
            if dist <= max_range:
                res.append(u)
        return res

    def _adjacent_enemies(self, unit: BattleUnit) -> List[BattleUnit]:
        """
        Backwards-compatible helper: enemies at distance 1.
        """
        return self._enemies_in_range(unit, 1)

    def _nearest_target(self, unit: BattleUnit, target_side: Side) -> Optional[BattleUnit]:
        candidates = self.player_units if target_side == "player" else self.enemy_units
        candidates = [u for u in candidates if u.is_alive]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda u: abs(u.gx - unit.gx) + abs(u.gy - unit.gy),
        )

    def _step_towards(self, unit: BattleUnit, target: BattleUnit) -> bool:
        dx = target.gx - unit.gx
        dy = target.gy - unit.gy

        if dx == 0 and dy == 0:
            return False

        step_x = 0
        step_y = 0
        if abs(dx) >= abs(dy) and dx != 0:
            step_x = 1 if dx > 0 else -1
        elif dy != 0:
            step_y = 1 if dy > 0 else -1

        if step_x != 0 or step_y != 0:
            if self._try_move_unit(unit, step_x, step_y):
                return True

        alt_x = 0
        alt_y = 0
        if step_x != 0 and dy != 0:
            alt_y = 1 if dy > 0 else -1
        elif step_y != 0 and dx != 0:
            alt_x = 1 if dx > 0 else -1

        if alt_x != 0 or alt_y != 0:
            return self._try_move_unit(unit, alt_x, alt_y)

        return False

    # ----- Damage helpers -----

    def _apply_damage(self, attacker: BattleUnit, target: BattleUnit, base_damage: int) -> int:
        """
        Apply damage from attacker to target, respecting statuses and defenses.
        Returns the actual damage dealt.
        """
        damage = int(base_damage * self._outgoing_multiplier(attacker))
        damage = int(damage * self._incoming_multiplier(target))

        defense = int(getattr(target.entity, "defense", 0))
        damage = max(1, damage - max(0, defense))

        current_hp = getattr(target.entity, "hp", 0)
        setattr(target.entity, "hp", max(0, current_hp - damage))
        return damage

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
        Fire a skill for a unit.
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
            damage = self._apply_damage(unit, target_unit, int(dmg))

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

    # ------------ Turn helpers ------------

    def _next_turn(self) -> None:
        if self.status != "ongoing":
            return

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
                    self.enemy_timer = BATTLE_ENEMY_TIMER
                else:
                    self.enemy_timer = 0.0
                self._on_unit_turn_start(unit)
                return

        self.status = "victory"

    # ------------ Player actions ------------

    def _perform_move(self, unit: BattleUnit, dx: int, dy: int) -> None:
        if self._is_stunned(unit):
            self._log(f"{unit.name} is stunned and cannot move!")
            self._next_turn()
            return

        if self._try_move_unit(unit, dx, dy):
            self._log(f"{unit.name} moves.")
            self._next_turn()
        else:
            self._log("You can't move there.")

    def _perform_basic_attack(self, unit: BattleUnit) -> None:
        if self._is_stunned(unit):
            self._log(f"{unit.name} is stunned and cannot act!")
            self._next_turn()
            return

        adj_enemies = self._adjacent_enemies(unit)
        if not adj_enemies:
            self._log("No enemy in range!")
            return

        target_unit = adj_enemies[0]
        damage = self._apply_damage(unit, target_unit, unit.attack_power)

        if not target_unit.is_alive:
            if not any(
                u.is_alive
                for u in (self.enemy_units if unit.side == "player" else self.player_units)
            ):
                if unit.side == "player":
                    self.status = "victory"
                    self._log(f"{unit.name} defeats the enemy party!")
                else:
                    self.status = "defeat"
                    self._log(f"{unit.name} destroys the last of your party!")
                return
            else:
                self._log(f"{unit.name} slays {target_unit.name} ({damage} dmg).")
        else:
            self._log(f"{unit.name} hits {target_unit.name} for {damage} dmg.")

        self._next_turn()

    # ------------ Input ------------

    def handle_event(self, game, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        input_manager = getattr(game, "input_manager", None)

        # If battle is already resolved, only listen for simple confirmations.
        if self.status == "defeat":
            # Keep the original behaviour: R to leave / restart.
            if event.key == pygame.K_r:
                self.finished = True
            return

        if self.status == "victory":
            # Any generic "confirm" key (Enter/Space by default) will exit.
            if input_manager is not None:
                if input_manager.event_matches_action(InputAction.CONFIRM, event):
                    self.finished = True
            else:
                if event.key == pygame.K_SPACE:
                    self.finished = True
            return

        unit = self._active_unit()
        if unit.side != "player":
            return

        # ------------------------------
        # Movement (logical actions)
        # ------------------------------
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

        # ------------------------------
        # Basic attack
        # ------------------------------
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.BASIC_ATTACK, event):
                self._perform_basic_attack(unit)
                return
        else:
            if event.key == pygame.K_SPACE:
                self._perform_basic_attack(unit)
                return


        # ------------------------------
        # Guard (dedicated action)
        # ------------------------------
        if input_manager is not None:
            if input_manager.event_matches_action(InputAction.GUARD, event):
                guard_skill = unit.skills.get("guard")
                if guard_skill is not None:
                    self._use_skill(unit, guard_skill)
                    return


        # ------------------------------
        # Skills (hotbar-style)
        # ------------------------------
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
            self._use_skill(unit, skill)
            return

    # ------------ Enemy AI ------------

    def update(self, dt: float) -> None:
        if self.status != "ongoing":
            return

        unit = self._active_unit()

        # Only enemies act automatically; players/companions are driven by input.
        if unit.side != "enemy":
            return

        self.enemy_timer -= dt
        if self.enemy_timer > 0.0:
            return

        # Defensive skills when low HP (e.g. nimble_step, war_cry)
        if unit.max_hp > 0:
            hp_ratio = unit.hp / float(unit.max_hp)
        else:
            hp_ratio = 1.0

        if hp_ratio < BATTLE_AI_DEFENSIVE_HP_THRESHOLD:
            for skill in unit.skills.values():
                if skill.target_mode == "self":
                    cd = unit.cooldowns.get(skill.id, 0)
                    if cd == 0 and random.random() < BATTLE_AI_DEFENSIVE_SKILL_CHANCE:
                        if self._use_skill(unit, skill, for_ai=True):
                            # _use_skill already advanced the turn
                            return

        if self._is_stunned(unit):
            self._log(f"{unit.name} is stunned!")
            self._next_turn()
            return

        # First, see if any offensive skills have a target in range.
        offensive_skills = [
            s
            for s in unit.skills.values()
            if s.target_mode == "adjacent_enemy" and s.base_power > 0.0
        ]
        random.shuffle(offensive_skills)

        any_adjacent = bool(self._enemies_in_range(unit, 1))

        for skill in offensive_skills:
            max_range = getattr(skill, "range_tiles", 1)
            targets_for_skill = self._enemies_in_range(unit, max_range)
            if not targets_for_skill:
                continue

            cd = unit.cooldowns.get(skill.id, 0)
            if cd == 0 and random.random() < BATTLE_AI_SKILL_CHANCE:
                if self._use_skill(unit, skill, for_ai=True):
                    # _use_skill handles logging, damage, win checks, and _next_turn()
                    return

        # If we are adjacent to someone but didn't use a skill, fall back to basic attack.
        if any_adjacent:
            self._perform_basic_attack(unit)
            return

        # Otherwise, move towards the nearest player.
        target = self._nearest_target(unit, "player")
        if target is None:
            # All players are dead / gone; battle should end elsewhere, but be safe:
            self.status = "victory"
            self._log("The foes scatter.")
            return

        moved = self._step_towards(unit, target)
        if moved:
            self._log(f"{unit.name} advances.")
        else:
            self._log(f"{unit.name} hesitates.")

        self._next_turn()

    # ------------ Drawing helpers ------------

    def _draw_active_unit_panel(
        self,
        surface: pygame.Surface,
        unit: Optional[BattleUnit],
        screen_w: int,
    ) -> None:
        """
        Draw a small HUD panel for the currently active unit (hero, companion,
        or enemy), showing name, HP, and basic stats.
        """
        if unit is None:
            return

        panel_width = 320
        panel_height = 80
        x = (screen_w - panel_width) // 2
        y = 16

        bg_rect = pygame.Rect(x, y, panel_width, panel_height)
        # Background
        pygame.draw.rect(surface, (18, 18, 28), bg_rect)

        # Border colour by side
        border_color = COLOR_PLAYER if unit.side == "player" else COLOR_ENEMY
        pygame.draw.rect(surface, border_color, bg_rect, width=2)

        # Name + role
        role = "Party" if unit.side == "player" else "Enemy"
        name_line = f"{unit.name} ({role})"
        name_surf = self.font.render(name_line, True, (230, 230, 230))
        surface.blit(name_surf, (x + 10, y + 8))

        # HP + stats line
        hp_line = f"HP {unit.hp}/{unit.max_hp}"
        atk = getattr(unit.entity, "attack_power", 0)
        defense = getattr(unit.entity, "defense", 0)
        stats_line = f"ATK {atk}   DEF {defense}"

        # Resource line (stamina, and later mana)
        res_line = ""
        max_sta = getattr(unit, "max_stamina", 0)
        cur_sta = getattr(unit, "current_stamina", 0)
        max_mana = getattr(unit, "max_mana", 0)
        cur_mana = getattr(unit, "current_mana", 0)

        if max_sta > 0:
            res_line = f"STA {cur_sta}/{max_sta}"
        if max_mana > 0:
            if res_line:
                res_line = f"MP {cur_mana}/{max_mana}   {res_line}"
            else:
                res_line = f"MP {cur_mana}/{max_mana}"

        hp_surf = self.font.render(hp_line, True, (210, 210, 210))
        stats_surf = self.font.render(stats_line, True, (200, 200, 200))
        res_surf = self.font.render(res_line, True, (190, 190, 230)) if res_line else None

        surface.blit(hp_surf, (x + 10, y + 32))
        surface.blit(stats_surf, (x + 10, y + 48))
        if res_surf is not None:
            surface.blit(res_surf, (x + 10, y + 64))

        # Simple status indicators on the right side of the panel
        icon_x = x + panel_width - 18
        icon_y = y + 10
        
        _draw_status_indicators(
            surface,
            self.font,
            icon_x,
            icon_y,
            has_guard=self._has_status(unit, "guard"),
            has_weakened=self._has_status(unit, "weakened"),
            has_stunned=self._is_stunned(unit),
            has_dot=self._has_dot(unit),
            icon_spacing=18,
        )


    def _draw_grid(self, surface: pygame.Surface) -> None:
        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                x = self.grid_origin_x + gx * self.cell_size
                y = self.grid_origin_y + gy * self.cell_size
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                pygame.draw.rect(surface, (40, 40, 60), rect, width=1)

    def _draw_hp_bar(
            self,
            surface: pygame.Surface,
            rect: pygame.Rect,
            unit: BattleUnit,
            *,
            is_player: bool,
    ) -> None:
        """
        Draw a small HP bar just above the unit's rectangle.
        """
        max_hp = unit.max_hp
        if max_hp <= 0:
            return

        hp = max(0, min(unit.hp, max_hp))
        ratio = hp / float(max_hp)

        bar_height = 6
        bar_width = rect.width
        bar_x = rect.x
        bar_y = rect.y - bar_height - 2

        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, (25, 25, 32), bg_rect)

        if ratio <= 0.0:
            return

        fg_width = max(1, int(bar_width * ratio))
        color = COLOR_PLAYER if is_player else COLOR_ENEMY
        fg_rect = pygame.Rect(bar_x, bar_y, fg_width, bar_height)
        pygame.draw.rect(surface, color, fg_rect)

    def _draw_units(self, surface: pygame.Surface) -> None:
        active = self._active_unit() if self.status == "ongoing" else None

        # ---------------- Player units ----------------
        for unit in self.player_units:
            if not unit.is_alive:
                continue

            x = self.grid_origin_x + unit.gx * self.cell_size
            y = self.grid_origin_y + unit.gy * self.cell_size
            rect = pygame.Rect(
                x + 10,
                y + 10,
                self.cell_size - 20,
                self.cell_size - 20,
            )

            # Body
            pygame.draw.rect(surface, COLOR_PLAYER, rect)
            # Highlight active unit
            if active is unit:
                pygame.draw.rect(surface, (240, 240, 160), rect, width=3)

            # HP bar
            self._draw_hp_bar(surface, rect, unit, is_player=True)

            # Status icons above the HP bar (horizontal layout, going upward)
            icon_y = rect.y - 18
            _draw_status_indicators(
                surface,
                self.font,
                rect.x + 4,  # Start x position
                icon_y,
                has_guard=self._has_status(unit, "guard"),
                has_weakened=self._has_status(unit, "weakened"),
                has_stunned=self._is_stunned(unit),
                has_dot=self._has_dot(unit),
                icon_spacing=-18,  # Negative for upward
                vertical=True,
            )

            # Cooldown indicator for hero's Power Strike
            hero = self._hero_unit()
            if hero is unit:
                cd = unit.cooldowns.get("power_strike", 0)
                if cd > 0:
                    cd_text = self.font.render(str(cd), True, (255, 200, 0))
                    surface.blit(cd_text, (rect.x + rect.width - 16, rect.y + 2))

            # Name label under unit
            name_surf = self.font.render(unit.name, True, (230, 230, 230))
            name_x = rect.centerx - name_surf.get_width() // 2
            name_y = rect.bottom + 10
            surface.blit(name_surf, (name_x, name_y))

        # ---------------- Enemy units ----------------
        for unit in self.enemy_units:
            if not unit.is_alive:
                continue

            x = self.grid_origin_x + unit.gx * self.cell_size
            y = self.grid_origin_y + unit.gy * self.cell_size
            rect = pygame.Rect(
                x + 10,
                y + 10,
                self.cell_size - 20,
                self.cell_size - 20,
            )

            # Body
            pygame.draw.rect(surface, COLOR_ENEMY, rect)
            # Highlight active unit
            if active is unit:
                pygame.draw.rect(surface, (255, 200, 160), rect, width=3)

            # HP bar
            self._draw_hp_bar(surface, rect, unit, is_player=False)

            # Status icons (horizontal layout, going upward)
            icon_y = rect.y - 18
            _draw_status_indicators(
                surface,
                self.font,
                rect.x + 4,  # Start x position
                icon_y,
                has_guard=self._has_status(unit, "guard"),
                has_weakened=self._has_status(unit, "weakened"),
                has_stunned=self._is_stunned(unit),
                has_dot=self._has_dot(unit),
                icon_spacing=-18,  # Negative for upward
                vertical=True,
            )

            # Name label
            name_surf = self.font.render(unit.name, True, (230, 210, 210))
            name_x = rect.centerx - name_surf.get_width() // 2
            name_y = rect.bottom + 10
            surface.blit(name_surf, (name_x, name_y))

    # ------------ Drawing ------------

    def draw(self, surface: pygame.Surface, game=None) -> None:
        surface.fill((5, 5, 10))
        screen_w, screen_h = surface.get_size()

        # ------------------------------------------------------------------
        # 1) Decide where the grid lives (centered between top info and bottom UI)
        # ------------------------------------------------------------------
        grid_px_w = self.grid_width * self.cell_size
        grid_px_h = self.grid_height * self.cell_size

        top_ui_height = 110  # space for Party/Enemy HP, Turn, Active, etc.
        bottom_ui_height = 110  # space for log + key hints

        available_h = max(0, screen_h - top_ui_height - bottom_ui_height)

        self.grid_origin_x = (screen_w - grid_px_w) // 2
        # Center the grid in the middle band, but never above the top_ui area
        self.grid_origin_y = top_ui_height + max(0, (available_h - grid_px_h) // 2)

        # ------------------------------------------------------------------
        # 2) Grid + units
        # ------------------------------------------------------------------
        self._draw_grid(surface)
        self._draw_units(surface)

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
        self._draw_active_unit_panel(surface, active_unit, screen_w)
        
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

        # ------------------------------------------------------------------
        # 4) Bottom UI: combat log + key hints
        # ------------------------------------------------------------------
        line_height = 20
        bottom_margin = 20
        hint_height = 20

        # Where the hint line will sit (just above bottom margin)
        hint_y = screen_h - bottom_margin - hint_height

        # Decide where the log starts: just above the hint, but also below the grid
        log_lines = self.log[-self.max_log_lines:]
        log_total_height = line_height * len(log_lines)

        grid_bottom_y = self.grid_origin_y + grid_px_h
        min_log_top = grid_bottom_y + 10
        max_log_top = hint_y - 4 - log_total_height

        log_y_start = max(min_log_top, max_log_top)
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

            # Draw skill hotbar if it's a player unit's turn (right side, log is on left)
            if active is not None and active.side == "player":
                # Get input manager for key bindings
                input_manager = None
                if game is not None:
                    input_manager = getattr(game, "input_manager", None)
                
                # Draw hotbar on the right side, above hint line
                hotbar_y = hint_y - 80
                # Calculate hotbar width to position it on the right
                skill_slots = getattr(active, "skill_slots", [])
                slot_width = 100
                slot_spacing = 8
                hotbar_w = len(skill_slots) * (slot_width + slot_spacing) - slot_spacing
                hotbar_x = screen_w - hotbar_w - 40  # Right side with margin
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
            
            # Simplified hint - skills are shown in visual hotbar, so just show movement and attack
            hint_text = self.font.render(
                f"{name_prefix}: move WASD/arrows | {atk_part}",
                True,
                (180, 180, 180),
            )
            surface.blit(hint_text, (40, hint_y))


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


