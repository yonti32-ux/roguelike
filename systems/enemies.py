@dataclass
class EnemyArchetype:
    id: str            # "goblin_brute", "cultist_invoker"
    name: str          # "Goblin Brute"
    role: str          # "Brute", "Skirmisher", "Invoker"
    tier: int          # 1 = early, 2 = mid, 3 = late

    # Scaling:
    base_hp: int
    base_attack: int
    base_defense: int
    hp_per_floor: float
    atk_per_floor: float
    def_per_floor: float

    skill_ids: list[str]    # from systems.skills
    ai_profile: str         # "brute", "skirmisher", "caster"
    xp_value: int
