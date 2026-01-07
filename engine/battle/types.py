"""
Battle type definitions.

Contains dataclasses and type aliases used throughout the battle system.
"""

from dataclasses import dataclass, field
from typing import Literal, List, Dict, Optional, Union

from settings import BASE_MOVEMENT_POINTS
from world.entities import Player, Enemy
from systems.statuses import StatusEffect
from systems.skills import Skill


# Type aliases
BattleStatus = Literal["ongoing", "victory", "defeat"]
Side = Literal["player", "enemy"]
TerrainType = Literal["none", "cover", "obstacle", "hazard"]


@dataclass
class BattleTerrain:
    """
    Represents terrain on a battle grid cell.
    
    - cover: Provides cover (reduces ranged damage)
    - obstacle: Blocks movement and line of sight
    - hazard: Damages units that step on it
    """
    terrain_type: TerrainType = "none"
    blocks_movement: bool = False
    blocks_los: bool = False  # Line of sight
    provides_cover: bool = False
    hazard_damage: int = 0  # Damage per turn if unit stands here
    
    def __post_init__(self):
        if self.terrain_type == "cover":
            self.provides_cover = True
        elif self.terrain_type == "obstacle":
            self.blocks_movement = True
            self.blocks_los = True
        elif self.terrain_type == "hazard":
            self.hazard_damage = 2  # Default hazard damage


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
    
    # Movement points system
    max_movement_points: int = BASE_MOVEMENT_POINTS
    current_movement_points: int = BASE_MOVEMENT_POINTS
    
    # Reaction system (for AoO, overwatch, etc.)
    reaction_capabilities: List[str] = field(default_factory=list)  # List of reaction types this unit can perform
    reactions_remaining: int = 0  # Reaction points remaining this turn

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
    def level(self) -> int:
        """Get the level of this unit's entity."""
        # Try to get level from entity (hero/companion have this)
        level = getattr(self.entity, "level", None)
        if level is not None:
            return int(level)
        # Fallback: estimate level from max_hp (rough approximation)
        # This is mainly for enemies that don't have explicit level
        max_hp = self.max_hp
        if max_hp <= 0:
            return 1
        # Rough estimate: base HP ~30, +5 per level
        estimated_level = max(1, (max_hp - 20) // 5)
        return min(estimated_level, 20)  # Cap at 20 for safety

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def init_resources_from_entity(self) -> None:
        """Initialize current resource pools from entity's max values."""
        self.current_mana = self.max_mana
        self.current_stamina = self.max_stamina

    def calculate_regen_amount(self, base_regen: int = 1, regen_bonus: int = 0) -> int:
        """
        Calculate regeneration amount based on level and perks.
        
        Formula: base_regen + (level // 5) + regen_bonus
        - Level 1-4: base_regen + regen_bonus
        - Level 5-9: base_regen + 1 + regen_bonus
        - Level 10-14: base_regen + 2 + regen_bonus
        - Level 15-19: base_regen + 3 + regen_bonus
        - Level 20+: base_regen + 4 + regen_bonus
        
        regen_bonus comes from perks (stamina_regen_bonus or mana_regen_bonus).
        """
        level = self.level
        level_bonus = level // 5  # +1 every 5 levels
        return base_regen + level_bonus + regen_bonus

    def regenerate_stamina(self, amount: Optional[int] = None) -> None:
        """
        Regenerate stamina (used at turn start).
        
        Args:
            amount: Amount to regenerate (if None, calculates based on level and perks)
        """
        max_sta = self.max_stamina
        if max_sta > 0:
            if amount is None:
                # Get stamina regen bonus from entity (set by perks)
                regen_bonus = getattr(self.entity, "stamina_regen_bonus", 0)
                amount = self.calculate_regen_amount(base_regen=1, regen_bonus=regen_bonus)
            self.current_stamina = min(max_sta, self.current_stamina + amount)

    def regenerate_mana(self, amount: Optional[int] = None) -> None:
        """
        Regenerate mana (used at turn start).
        
        Args:
            amount: Amount to regenerate (if None, calculates based on level and perks)
        """
        max_mana = self.max_mana
        if max_mana > 0:
            if amount is None:
                # Get mana regen bonus from entity (set by perks)
                regen_bonus = getattr(self.entity, "mana_regen_bonus", 0)
                amount = self.calculate_regen_amount(base_regen=1, regen_bonus=regen_bonus)
            self.current_mana = min(max_mana, self.current_mana + amount)

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

