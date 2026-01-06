from dataclasses import dataclass

@dataclass
class StatBlock:
    # Primary-ish stats
    max_hp: int = 30
    attack: int = 6
    defense: int = 0
    speed: float = 1.0      # for turn order later
    skill_power: float = 1.0

    crit_chance: float = 0.0
    dodge_chance: float = 0.0
    status_resist: float = 0.0
    max_mana: int = 0
    max_stamina: int = 0
    
    # Regeneration bonuses (added to base regen per turn)
    stamina_regen_bonus: int = 0
    mana_regen_bonus: int = 0