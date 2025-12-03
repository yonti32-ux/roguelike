# systems/progression.py

from dataclasses import dataclass, field
from typing import List
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

            messages.append(f"Level up! You reached level {self.level}.")

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
