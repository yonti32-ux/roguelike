"""
Ally type definitions.

Contains the core dataclasses for ally archetypes and pack templates,
similar to enemy archetypes but designed for friendly units that fight alongside the player.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AllyArchetype:
    """
    Defines a *type* of ally that can join the player in battle.
    
    Similar to EnemyArchetype but designed for friendly units:
    - id:          stable internal id (used for lookups)
    - name:        display name (used in UI / battle)
    - role:        combat role ("Guardian", "Skirmisher", "Support", etc.)
    - ai_profile:  AI behavior profile ("defender", "skirmisher", "support", etc.)
    
    - base_*:      stats at level 1 (scaled to player level)
    - *_per_level: per-level scaling for those stats
    
    - skill_ids:   list of skill ids this ally can use
    
    - party_type_ids: which party types can spawn this ally (e.g., ["guard", "ranger"])
    
    - tags:        categorization tags for synergies (["guardian", "military", "support"], etc.)
    """
    id: str
    name: str
    role: str
    ai_profile: str
    
    # Base stats (at level 1, scaled to player level)
    base_hp: int
    hp_per_level: float
    base_attack: int
    atk_per_level: float
    base_defense: int
    def_per_level: float
    
    # Skill power for support/caster allies
    base_skill_power: float = 1.0
    skill_power_per_level: float = 0.05
    
    # Initiative (turn order)
    base_initiative: int = 10
    init_per_level: float = 0.5
    
    # Skills this ally can use
    skill_ids: List[str] = field(default_factory=list)
    
    # Which party types can spawn this ally
    party_type_ids: List[str] = field(default_factory=list)
    
    # Tags for synergies and categorization
    tags: List[str] = field(default_factory=list)
    # Examples: ["guardian", "military", "support", "ranger", "merchant"]
    
    # Optional: unique mechanics (like enemies)
    unique_mechanics: List[str] = field(default_factory=list)
    # Examples: "guardian_aura", "ranger_mark", "merchant_blessing"
    
    # Optional: resistances
    resistances: Dict[str, float] = field(default_factory=dict)
    
    # Description for UI/tooltips
    description: str = ""


@dataclass
class AllyPackTemplate:
    """
    Themed group of allies that can join together in battle.
    
    Similar to EnemyPackTemplate but for friendly units:
    - id:               internal id
    - name:             display name for the pack
    - member_arch_ids:  list of AllyArchetype ids that form this pack
    - party_type_ids:   which party types can spawn this pack
    - weight:           selection weight when multiple packs are possible
    - synergy_bonus:    optional synergy bonus description
    """
    id: str
    member_arch_ids: List[str]
    name: str = ""
    party_type_ids: List[str] = field(default_factory=list)
    weight: float = 1.0
    synergy_bonus: str = ""  # Description of pack synergy
