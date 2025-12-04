from collections import Counter
from dataclasses import dataclass, field
from typing import Literal, List, Dict, Optional

import random
import pygame

from settings import COLOR_PLAYER, COLOR_ENEMY
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
from systems.party import CompanionDef  # NEW

BattleStatus = Literal["ongoing", "victory", "defeat"]
Side = Literal["player", "enemy"]


@dataclass
class BattleUnit:
    """
    Wrapper around a world entity (Player or Enemy) for use on the battle grid.

    Keeps track of side, grid position, and combat state.
    """
    entity: object
    side: Side
    gx: int
    gy: int
    name: str = "Unit"

    statuses: List[StatusEffect] = field(default_factory=list)
    cooldowns: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, Skill] = field(default_factory=dict)

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
    def is_alive(self) -> bool:
        return self.hp > 0


class BattleScene:
    """
    Turn-based battle on a small abstract grid.

    - 2-player party (hero + companion) vs a small enemy group (up to 3).
    - Initiative per unit.
    - Units can:
        - Move 1 tile (WASD / arrows)
        - Basic attack adjacent enemies (SPACE)
        - Skills (Guard, Power Strike, Crippling Blow) from systems.skills
    """

    def __init__(
        self,
        player: Player,
        enemies: List[Enemy],
        font: pygame.font.Font,
        companions: Optional[List[CompanionDef]] = None,
    ) -> None:
        self.player = player
        self.font = font

        # Grid configuration (battlefield, not dungeon grid)
        self.grid_width = 6
        self.grid_height = 4
        self.cell_size = 80
        self.grid_origin_x = 120
        self.grid_origin_y = 160

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
            gx=1,
            gy=self.grid_height // 2,
            name=hero_name,
        )
        hero_unit.skills = {
            "guard": get_skill("guard"),
            "power_strike": get_skill("power_strike"),
        }
        hero_unit.cooldowns["power_strike"] = 0  # ready

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


        # --- Player side: hero + companions from Game.party -----------------

        self.player_units: List[BattleUnit] = [hero_unit]

        # Base stats used to derive simple companion stats in P1
        base_max_hp = getattr(self.player, "max_hp", 24)
        base_atk = getattr(self.player, "attack_power", 5)
        base_def = int(getattr(self.player, "defense", 0))
        base_sp = float(getattr(self.player, "skill_power", 1.0))

        hero_row = self.grid_height // 2
        companion_row = max(0, hero_row - 1)

        created_any_companion = False

        if companions:
            # For P1 we only use the FIRST companion in the list.
            comp_def = companions[0]

            comp_max_hp = max(1, int(base_max_hp * comp_def.hp_factor))
            comp_hp = comp_max_hp
            comp_atk = max(1, int(base_atk * comp_def.attack_factor))
            comp_defense = int(base_def * comp_def.defense_factor)
            comp_sp = max(0.1, base_sp * comp_def.skill_power_factor)

            companion_entity = Player(
                x=0,
                y=0,
                width=self.player.width,
                height=self.player.height,
                speed=0.0,
                color=self.player.color,
                max_hp=comp_max_hp,
                hp=comp_hp,
                attack_power=comp_atk,
            )
            setattr(companion_entity, "defense", comp_defense)
            setattr(companion_entity, "skill_power", comp_sp)

            companion_name = comp_def.name or getattr(self.player, "companion_name", "Companion")
            companion_unit = BattleUnit(
                entity=companion_entity,
                side="player",
                gx=1,
                gy=companion_row,
                name=companion_name,
            )

            # Skills for the companion: from template, fallback to Guard
            skills = {}
            for skill_id in comp_def.skill_ids:
                try:
                    skills[skill_id] = get_skill(skill_id)
                except KeyError:
                    continue
            if "guard" not in skills:
                skills["guard"] = get_skill("guard")

            companion_unit.skills = skills
            self.player_units.append(companion_unit)
            created_any_companion = True

        if not created_any_companion:
            # Fallback to old behaviour: one generic companion
            companion_max_hp = getattr(self.player, "max_hp", 24)
            companion_display_name = getattr(self.player, "companion_name", "Companion")
            companion = Player(
                x=0,
                y=0,
                width=self.player.width,
                height=self.player.height,
                speed=0.0,
                color=self.player.color,
                max_hp=int(companion_max_hp * 0.8),
                hp=int(companion_max_hp * 0.8),
                attack_power=max(2, int(getattr(self.player, "attack_power", 5) * 0.7)),
            )
            companion_unit = BattleUnit(
                entity=companion,
                side="player",
                gx=1,
                gy=max(0, self.grid_height // 2 - 1),
                name=companion_display_name,
            )
            companion_unit.skills = {
                "guard": get_skill("guard"),
            }
            self.player_units.append(companion_unit)

        # --- Enemy side: create a unit per enemy in the encounter group ---

        self.enemy_units: List[BattleUnit] = []

        # We assume Game.start_battle already capped group size,
        # but we defensively cap here as well.
        max_enemies = min(len(enemies), 3)

        start_col = self.grid_width - 2
        # Place them vertically near the right side
        start_row = max(0, self.grid_height // 2 - (max_enemies // 2))

        enemy_type_list: List[str] = []

        for i, enemy in enumerate(enemies[:max_enemies]):
            gx = start_col
            gy = start_row + i

            enemy_type = getattr(enemy, "enemy_type", "Enemy")
            enemy_type_list.append(enemy_type)

            unit = BattleUnit(
                entity=enemy,
                side="enemy",
                gx=gx,
                gy=gy,
                name=enemy_type,
            )
            unit.skills = {
                "crippling_blow": get_skill("crippling_blow"),
            }
            self.enemy_units.append(unit)

        # Group label for enemies ("2x Goblin, Bandit")
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

        # Turn order
        self.turn_order: List[BattleUnit] = []
        self.turn_order.extend(self.player_units)
        self.turn_order.extend(self.enemy_units)

        self.turn_index: int = 0
        self.turn: Side = self.turn_order[self.turn_index].side

        # Enemy action timer
        self.enemy_timer: float = 0.0

        self.status: BattleStatus = "ongoing"
        self.finished: bool = False

        # Prepare first unit
        self._on_unit_turn_start(self._active_unit())
        self._log("A hostile group approaches!")

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

    def _adjacent_enemies(self, unit: BattleUnit) -> List[BattleUnit]:
        enemies = self.enemy_units if unit.side == "player" else self.player_units
        res: List[BattleUnit] = []
        for u in enemies:
            if not u.is_alive:
                continue
            dist = abs(u.gx - unit.gx) + abs(u.gy - unit.gy)
            if dist == 1:
                res.append(u)
        return res

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
            adj = self._adjacent_enemies(unit)
            if not adj:
                if not for_ai:
                    self._log(f"No enemy in range for {skill.name}!")
                return False
            target_unit = adj[0]

        # Apply damage if any
        damage = 0
        if skill.base_power > 0 and target_unit is not None and target_unit is not unit:
            base = unit.attack_power
            dmg = base * skill.base_power
            if skill.uses_skill_power:
                sp = float(getattr(unit.entity, "skill_power", 1.0))
                dmg *= max(0.5, sp)
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
                    self.enemy_timer = 0.6
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
                if unit.side == "player":
                    self._log(f"{unit.name} slays {target_unit.name} ({damage} dmg).")
                else:
                    self._log(f"{unit.name} slays {target_unit.name} ({damage} dmg).")
        else:
            self._log(f"{unit.name} hits {target_unit.name} for {damage} dmg.")

        self._next_turn()

    # ------------ Input ------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self.status == "defeat":
            if event.key == pygame.K_r:
                self.finished = True
            return

        if self.status == "victory":
            if event.key == pygame.K_SPACE:
                self.finished = True
            return

        unit = self._active_unit()
        if unit.side != "player":
            return

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

        if event.key == pygame.K_SPACE:
            self._perform_basic_attack(unit)
            return

        skill = self._skill_for_key(unit, event.key)
        if skill is not None:
            self._use_skill(unit, skill)
            return

    # ------------ Enemy AI ------------

    def update(self, dt: float) -> None:
        if self.status != "ongoing":
            return

        unit = self._active_unit()

        if unit.side == "enemy":
            self.enemy_timer -= dt
            if self.enemy_timer > 0.0:
                return

            if self._is_stunned(unit):
                self._log(f"{unit.name} is stunned!")
                self._next_turn()
                return

            adj_players = self._adjacent_enemies(unit)
            if adj_players:
                skill = unit.skills.get("crippling_blow")
                can_use_skill = (
                    skill is not None
                    and unit.cooldowns.get(skill.id, 0) == 0
                    and random.random() < 0.35
                )
                if can_use_skill and self._use_skill(unit, skill, for_ai=True):
                    return

                self._perform_basic_attack(unit)
                return

            target = self._nearest_target(unit, "player")
            if target is None:
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

    def _draw_grid(self, surface: pygame.Surface) -> None:
        for gy in range(self.grid_height):
            for gx in range(self.grid_width):
                x = self.grid_origin_x + gx * self.cell_size
                y = self.grid_origin_y + gy * self.cell_size
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                pygame.draw.rect(surface, (40, 40, 60), rect, width=1)

    def _draw_units(self, surface: pygame.Surface) -> None:
        active = self._active_unit() if self.status == "ongoing" else None

        # Player units
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
            pygame.draw.rect(surface, COLOR_PLAYER, rect)
            if active is unit:
                pygame.draw.rect(surface, (240, 240, 160), rect, width=3)

            # Status icons
            icon_y = rect.y - 18
            if self._has_status(unit, "guard"):
                g_text = self.font.render("G", True, (255, 255, 180))
                surface.blit(g_text, (rect.x + 4, icon_y))
                icon_y -= 18
            if self._has_status(unit, "weakened"):
                w_text = self.font.render("W", True, (255, 200, 100))
                surface.blit(w_text, (rect.x + 20, icon_y))
                icon_y -= 18
            if self._is_stunned(unit):
                s_text = self.font.render("!", True, (255, 100, 100))
                surface.blit(s_text, (rect.x + 36, icon_y))

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
            name_y = rect.bottom + 2
            surface.blit(name_surf, (name_x, name_y))

        # Enemy units
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
            pygame.draw.rect(surface, COLOR_ENEMY, rect)
            if active is unit:
                pygame.draw.rect(surface, (255, 200, 160), rect, width=3)

            icon_y = rect.y - 18
            if self._has_status(unit, "guard"):
                g_text = self.font.render("G", True, (255, 255, 180))
                surface.blit(g_text, (rect.x + 4, icon_y))
                icon_y -= 18
            if self._has_status(unit, "weakened"):
                w_text = self.font.render("W", True, (255, 200, 100))
                surface.blit(w_text, (rect.x + 20, icon_y))
                icon_y -= 18
            if self._is_stunned(unit):
                s_text = self.font.render("!", True, (255, 100, 100))
                surface.blit(s_text, (rect.x + 36, icon_y))

            # Name label
            name_surf = self.font.render(unit.name, True, (230, 210, 210))
            name_x = rect.centerx - name_surf.get_width() // 2
            name_y = rect.bottom + 2
            surface.blit(name_surf, (name_x, name_y))

    # ------------ Drawing ------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((5, 5, 10))

        self._draw_grid(surface)
        self._draw_units(surface)

        total_player_hp = sum(u.hp for u in self.player_units)
        total_player_maxhp = sum(u.max_hp for u in self.player_units)
        total_enemy_hp = sum(u.hp for u in self.enemy_units)
        total_enemy_maxhp = sum(u.max_hp for u in self.enemy_units)

        player_hp_text = self.font.render(
            f"Party HP: {total_player_hp}/{total_player_maxhp}",
            True,
            (220, 220, 220),
        )
        enemy_hp_text = self.font.render(
            f"Enemy HP: {total_enemy_hp}/{total_enemy_maxhp}",
            True,
            (220, 220, 220),
        )

        surface.blit(player_hp_text, (40, 40))
        surface.blit(enemy_hp_text, (400, 40))

        # Turn label
        if self.status == "ongoing":
            side_label = self._active_unit().side
        else:
            side_label = "-"
        status_text = self.font.render(
            f"Turn: {side_label}",
            True,
            (200, 200, 255),
        )
        surface.blit(status_text, (40, 70))

        # Enemy group label
        group_text = self.font.render(
            f"Enemies: {self.enemy_group_label}",
            True,
            (220, 200, 200),
        )
        surface.blit(group_text, (400, 70))

        # Combat log (bottom-left-ish)
        log_y = 110
        for msg in self.log:
            log_text = self.font.render(msg, True, (200, 200, 200))
            surface.blit(log_text, (40, log_y))
            log_y += 20

        # Status prompts
        if self.status == "ongoing":
            hero = self._hero_unit()
            if hero is not None:
                parts: List[str] = []
                for skill in hero.skills.values():
                    if skill.key is None:
                        continue
                    key_name = pygame.key.name(skill.key).upper()
                    parts.append(f"{key_name}: {skill.name}")
                skills_str = " | ".join(parts) if parts else "No skills"
            else:
                skills_str = "No skills"

            hint_text = self.font.render(
                f"Battle: Move WASD/arrows | SPACE atk | {skills_str}",
                True,
                (180, 180, 180),
            )
            surface.blit(hint_text, (40, 150 + (self.max_log_lines * 0)))  # below log area

        elif self.status == "defeat":
            dead_text = self.font.render(
                "You died - press R to restart",
                True,
                (255, 80, 80),
            )
            surface.blit(dead_text, (40, 150))
        elif self.status == "victory":
            win_text = self.font.render(
                "Victory! Press SPACE to continue.",
                True,
                (120, 220, 120),
            )
            surface.blit(win_text, (40, 150))
