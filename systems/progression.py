# systems/progression.py

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import copy

from .stats import StatBlock
from .classes import ClassDef


@dataclass
class HeroStats:
    """
    Hero meta-progression for the current run.

    - level, xp: progression
    - gold:      current currency for this run
    - base:      core stats (HP, attack, defense, etc.) stored in a StatBlock

    We keep convenience properties (max_hp, attack_power, defense, skill_power)
    so the rest of the game can keep using them.

    Perks:
    - stored as a list of perk ids (strings)
    - their mechanical effects are applied by systems.perks when they are learned

    Class:
    - hero_class_id: points to a ClassDef in systems.classes
    - hero_name:     for UI; does not affect mechanics directly
    """
    level: int = 1
    xp: int = 0
    gold: int = 0

    hero_class_id: str = "warrior"
    hero_name: str = "Adventurer"

    base: StatBlock = field(default_factory=StatBlock)

    # Learned perk ids (e.g. ["toughness_1", "weapon_training_1"])
    perks: List[str] = field(default_factory=list)

    # Hotbar-style skill layout; indices 0–3 map to SKILL_1..SKILL_4.
    # Values are skill IDs (strings) or None.
    skill_slots: List[Optional[str]] = field(
        default_factory=lambda: [None, None, None, None]
    )

    # Skill progression system
    # Available skill points to spend on upgrading skills
    skill_points: int = 0
    
    # Track skill ranks: skill_id -> current_rank (0 = unranked, max 5)
    skill_ranks: Dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # XP / Level
    # ------------------------------------------------------------------

    def xp_to_next(self) -> int:
        """
        XP needed for the *next* level.

        Simple linear curve for now:
            level 1 -> 2: 10 XP
            level 2 -> 3: 15 XP
            level 3 -> 4: 20 XP
        etc.

        We can replace this with a steeper curve later if needed.
        """
        return 10 + (self.level - 1) * 5

    def grant_xp(self, amount: int) -> list[str]:
        """
        Give XP, handle level ups, and return text messages describing what happened.
        Perk selection is handled elsewhere (e.g. systems.perks).
        """
        messages: list[str] = []
        if amount <= 0:
            return messages

        self.xp += amount
        messages.append(f"Gained {amount} XP.")

        # May level up multiple times if amount is big
        while True:
            needed = self.xp_to_next()
            if self.xp < needed:
                break

            self.xp -= needed
            self.level += 1

            # Stat growth per level (tweakable)
            self.base.max_hp += 5
            self.base.attack += 1
            # defense / skill_power are mostly perk- or reward-driven
            
            # Initiative growth per level (small, to keep up with floor scaling)
            # +1 initiative every 2 levels (so level 2, 4, 6, etc.)
            if self.level % 2 == 0:
                self.base.initiative += 1
            
            # Resource pool growth per level
            self.base.max_stamina += 3  # +3 stamina per level
            self.base.max_mana += 2  # +2 mana per level

            # Grant skill points on level up
            # Formula: 1 + (level // 5) points per level
            points_gained = 1 + (self.level // 5)
            self.skill_points += points_gained

            messages.append(f"Level up! You reached level {self.level}.")
            if points_gained > 0:
                messages.append(f"Gained {points_gained} skill point{'s' if points_gained > 1 else ''}.")

        return messages

    # ------------------------------------------------------------------
    # Gold helpers
    # ------------------------------------------------------------------

    def add_gold(self, amount: int) -> int:
        """
        Add some gold to the hero and return how much was actually added.
        Useful for random rewards where amount may be <= 0.
        """
        amount = int(amount)
        if amount <= 0:
            return 0
        self.gold += amount
        return amount

    def can_afford(self, cost: int) -> bool:
        """
        Check if the hero has enough gold to pay 'cost'.
        """
        cost = int(cost)
        if cost <= 0:
            return True
        return self.gold >= cost

    def spend_gold(self, cost: int) -> bool:
        """
        Try to spend 'cost' gold. Returns True on success, False if not enough.
        Does nothing if cost <= 0.
        """
        cost = int(cost)
        if cost <= 0:
            return True

        if self.gold >= cost:
            self.gold -= cost
            return True
        return False

    # ------------------------------------------------------------------
    # Class helpers
    # ------------------------------------------------------------------

    def apply_class(self, class_def: ClassDef) -> None:
        """
        Apply a ClassDef to this hero for a *fresh run*.

        - Resets level / XP.
        - Sets hero_class_id.
        - Copies base stats from the class.
        - Replaces perks with the class's starting perks.
        - Sets starting gold from class_def.starting_gold.

        Starting items are handled elsewhere (Game / inventory).
        """
        self.hero_class_id = class_def.id
        self.hero_name = class_def.name  # can be renamed later by the player

        # Fresh progression state
        self.level = 1
        self.xp = 0
        self.gold = class_def.starting_gold

        # Copy base stats so we don't mutate the shared ClassDef template
        self.base = copy.deepcopy(class_def.base_stats)

        # Start with the class's default perks
        self.perks = list(class_def.starting_perks)

        # Reset skill progression
        self.skill_points = 0
        self.skill_ranks = {}

        # Seed a simple default hotbar layout for a fresh hero.
        # Guard stays on its dedicated GUARD action; we prefer "power_strike"
        # as the first slotted offensive skill if available.
        self.skill_slots = [None, None, None, None]
        self.ensure_default_skill_slots(["power_strike"])

    # ------------------------------------------------------------------
    # Convenience properties (so older code still works)
    # ------------------------------------------------------------------

    @property
    def max_hp(self) -> int:
        return self.base.max_hp

    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self.base.max_hp = int(value)

    @property
    def attack_power(self) -> int:
        return self.base.attack

    @attack_power.setter
    def attack_power(self, value: int) -> None:
        self.base.attack = int(value)

    @property
    def defense(self) -> int:
        return self.base.defense

    @defense.setter
    def defense(self, value: int) -> None:
        self.base.defense = int(value)

    @property
    def skill_power(self) -> float:
        return self.base.skill_power

    @skill_power.setter
    def skill_power(self, value: float) -> None:
        self.base.skill_power = float(value)

    @property
    def max_mana(self) -> int:
        return self.base.max_mana

    @max_mana.setter
    def max_mana(self, value: int) -> None:
        self.base.max_mana = int(value)

    @property
    def max_stamina(self) -> int:
        return self.base.max_stamina

    @max_stamina.setter
    def max_stamina(self, value: int) -> None:
        self.base.max_stamina = int(value)

    # ------------------------------------------------------------------
    # Skill slot helpers
    # ------------------------------------------------------------------

    def ensure_default_skill_slots(
        self,
        available_skill_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Ensure that skill_slots has a reasonable default layout.

        - Keeps any existing non-empty layout.
        - Otherwise, prefers 'power_strike' if available, then the first
          remaining available skill id (excluding 'guard').
        """
        # If we already have at least one real slot, don't touch it.
        if any(slot for slot in self.skill_slots):
            return

        ordered: List[Optional[str]] = []

        available = list(available_skill_ids or [])
        # Guard has its own dedicated GUARD action.
        available = [sid for sid in available if sid != "guard"]

        if "power_strike" in available:
            ordered.append("power_strike")
        elif available:
            ordered.append(available[0])

        # Pad to 4 entries
        while len(ordered) < 4:
            ordered.append(None)

        self.skill_slots = ordered[:4]

    # ------------------------------------------------------------------
    # Skill rank helpers
    # ------------------------------------------------------------------

    def get_skill_rank(self, skill_id: str) -> int:
        """Get the current rank of a skill (0 if not ranked)."""
        return self.skill_ranks.get(skill_id, 0)

    def can_upgrade_skill(self, skill_id: str) -> bool:
        """
        Check if a skill can be upgraded.
        
        Requirements:
        - Skill must exist
        - Current rank must be less than max_rank
        - Must have enough skill points for the next rank
        """
        from .skills import get, get_skill_rank_cost
        
        try:
            skill = get(skill_id)
        except KeyError:
            return False
        
        current_rank = self.get_skill_rank(skill_id)
        if current_rank >= skill.max_rank:
            return False
        
        next_rank = current_rank + 1
        cost = get_skill_rank_cost(next_rank)
        return self.skill_points >= cost

    def upgrade_skill(self, skill_id: str) -> bool:
        """
        Upgrade a skill by one rank.
        
        Returns True if upgrade was successful, False otherwise.
        """
        if not self.can_upgrade_skill(skill_id):
            return False
        
        from .skills import get, get_skill_rank_cost
        
        current_rank = self.get_skill_rank(skill_id)
        next_rank = current_rank + 1
        cost = get_skill_rank_cost(next_rank)
        
        self.skill_points -= cost
        self.skill_ranks[skill_id] = next_rank
        return True
