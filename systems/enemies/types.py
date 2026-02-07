"""
Enemy type definitions.

Contains the core dataclasses for enemy archetypes and pack templates.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnemyArchetype:
    """
    Defines a *type* of enemy that can appear on the map and in battle.

    - id:          stable internal id (used for lookups)
    - name:        display name (used in UI / battle group labels)
    - role:        loose combat role ("Skirmisher", "Brute", "Invoker", etc.)
    - tier:        rough difficulty band (1=early, 2=mid, 3=late) [DEPRECATED: use difficulty_level]
    - ai_profile:  hint for future AI logic ("skirmisher", "brute", "caster"...)

    - base_*:      stats at floor 1
    - *_per_floor: per-floor scaling for those stats

    - skill_ids:   list of skill ids from systems.skills that this archetype can use
    
    New Difficulty System (modular and scalable):
    - difficulty_level: 1-100+ difficulty rating (replaces tier for spawn selection)
    - spawn_min_floor:  Earliest floor this enemy can appear
    - spawn_max_floor:  Latest floor (None = unlimited)
    - spawn_weight:     Relative spawn chance within valid floors
    - tags:             Categorization tags (["early_game", "undead", "caster"], etc.)
    """
    id: str
    name: str
    role: str
    tier: int  # Kept for backward compatibility, will be deprecated
    ai_profile: str

    base_hp: int
    hp_per_floor: float
    base_attack: int
    atk_per_floor: float
    base_defense: int
    def_per_floor: float
    base_xp: int
    xp_per_floor: float

    skill_ids: List[str]

    # Initiative controls turn order in battle (higher = acts earlier).
    # Defaults keep older content working without specifying values.
    base_initiative: int = 10
    init_per_floor: float = 0.0
    
    # New Difficulty System fields (optional, auto-calculated from tier if not provided)
    difficulty_level: Optional[int] = None
    spawn_min_floor: Optional[int] = None
    spawn_max_floor: Optional[int] = None
    spawn_weight: float = 1.0
    tags: List[str] = field(default_factory=list)
    
    # Unique Mechanics & Resistances (for tactical depth)
    unique_mechanics: List[str] = field(default_factory=list)
    # Examples: "regeneration", "fire_immunity", "phase_through", "summon_on_kill", "death_explosion"
    resistances: Dict[str, float] = field(default_factory=dict)
    # Examples: {"fire": 0.0} = immune, {"fire": 0.5} = 50% damage, {"fire": 1.5} = 150% damage (weakness)
    
    def __post_init__(self):
        """
        Auto-calculate new difficulty system fields from tier for backward compatibility.
        This allows existing enemies to work without modification.
        """
        # Auto-calculate difficulty_level from tier if not provided
        if self.difficulty_level is None:
            # Map tier to difficulty level (1-100 scale)
            # Tier 1: 10-30, Tier 2: 40-60, Tier 3: 70-90
            tier_to_level = {1: 20, 2: 50, 3: 80}
            self.difficulty_level = tier_to_level.get(self.tier, 50)
        
        # Auto-calculate spawn_min_floor from tier if not provided
        if self.spawn_min_floor is None:
            tier_to_min_floor = {1: 1, 2: 3, 3: 5}
            self.spawn_min_floor = tier_to_min_floor.get(self.tier, 1)
        
        # Auto-calculate spawn_max_floor from tier if not provided
        if self.spawn_max_floor is None:
            # Tier 1: floors 1-3, Tier 2: floors 3-6, Tier 3: unlimited
            tier_to_max_floor = {1: 3, 2: 6, 3: None}
            self.spawn_max_floor = tier_to_max_floor.get(self.tier, None)
        
        # Auto-add tier-based tags if tags are empty
        if not self.tags:
            tier_tags = {1: ["early_game"], 2: ["mid_game"], 3: ["late_game"]}
            base_tags = tier_tags.get(self.tier, [])
            # Add role-based tag
            role_tag = self.role.lower().replace(" ", "_")
            self.tags = base_tags + [role_tag]


@dataclass
class EnemyPackTemplate:
    """
    Themed group of enemies that tends to spawn together.

    - id:               internal id
    - name:             optional flavor / debug label
    - tier:             difficulty band (1, 2, 3...) matching archetype tiers
    - member_arch_ids:  list of EnemyArchetype ids that form this pack
    - preferred_room_tag: optional room tag this pack likes ("lair", "event", ...)
    - weight:           base selection weight among same-tier packs
    """
    id: str
    tier: int
    member_arch_ids: List[str]
    name: str = ""
    preferred_room_tag: Optional[str] = None
    weight: float = 1.0
