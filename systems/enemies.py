from dataclasses import dataclass
from typing import Dict, List, Optional
import random


@dataclass
class EnemyArchetype:
    """
    Defines a *type* of enemy that can appear on the map and in battle.

    - id:          stable internal id (used for lookups)
    - name:        display name (used in UI / battle group labels)
    - role:        loose combat role ("Skirmisher", "Brute", "Invoker", etc.)
    - tier:        rough difficulty band (1=early, 2=mid, 3=late)
    - ai_profile:  hint for future AI logic ("skirmisher", "brute", "caster"...)

    - base_*:      stats at floor 1
    - *_per_floor: per-floor scaling for those stats

    - skill_ids:   list of skill ids from systems.skills that this archetype can use
    """
    id: str
    name: str
    role: str
    tier: int
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


ENEMY_ARCHETYPES: Dict[str, EnemyArchetype] = {}
ENEMY_PACKS: Dict[str, EnemyPackTemplate] = {}


def register_archetype(arch: EnemyArchetype) -> EnemyArchetype:
    ENEMY_ARCHETYPES[arch.id] = arch
    return arch


def get_archetype(arch_id: str) -> EnemyArchetype:
    return ENEMY_ARCHETYPES[arch_id]


def register_pack(pack: EnemyPackTemplate) -> EnemyPackTemplate:
    ENEMY_PACKS[pack.id] = pack
    return pack


def compute_scaled_stats(arch: EnemyArchetype, floor_index: int) -> tuple[int, int, int, int]:
    """
    Scale an archetype's stats for the given floor.

    Returns (max_hp, attack_power, defense, xp_reward).
    """
    level = max(1, floor_index)
    max_hp = int(arch.base_hp + arch.hp_per_floor * (level - 1))
    attack = int(arch.base_attack + arch.atk_per_floor * (level - 1))
    defense = int(arch.base_defense + arch.def_per_floor * (level - 1))
    xp = int(arch.base_xp + arch.xp_per_floor * (level - 1))
    return max_hp, attack, defense, xp


def _tier_for_floor(floor_index: int) -> int:
    if floor_index <= 2:
        return 1
    elif floor_index <= 4:
        return 2
    else:
        return 3


def choose_archetype_for_floor(
    floor_index: int,
    room_tag: Optional[str] = None,
) -> EnemyArchetype:
    """
    Pick an archetype for the given floor + room tag.

    - Floor controls the *tier*.
    - room_tag ("lair", "event", etc.) nudges the weights but doesn't hard-lock anything.
    """
    tier = _tier_for_floor(floor_index)

    candidates = [a for a in ENEMY_ARCHETYPES.values() if a.tier == tier]
    if not candidates:
        # Fallback: use *any* archetype if someone deletes a tier by accident.
        candidates = list(ENEMY_ARCHETYPES.values())

    if not candidates:
        raise RuntimeError("No enemy archetypes registered.")

    weights: List[float] = []
    for arch in candidates:
        w = 1.0

        # Lair rooms tend to have heavier hitters
        if room_tag == "lair" and arch.role in ("Brute", "Elite Brute"):
            w += 1.0

        # Event rooms lean a bit towards casters / cultists
        if room_tag == "event" and arch.role in ("Invoker", "Support"):
            w += 0.7

        weights.append(w)

    return random.choices(candidates, weights=weights, k=1)[0]


def choose_pack_for_floor(
    floor_index: int,
    room_tag: Optional[str] = None,
) -> EnemyPackTemplate:
    """
    Pick a *pack template* for the given floor + room tag.

    - Floor controls the pack tier.
    - room_tag nudges towards packs that prefer that tag.
    - If no packs are defined, falls back to a single-archetype pseudo-pack.
    """
    tier = _tier_for_floor(floor_index)

    candidates = [p for p in ENEMY_PACKS.values() if p.tier == tier]
    if not candidates:
        candidates = list(ENEMY_PACKS.values())

    if not candidates:
        # Fallback: single-archetype pseudo-pack based on the floor.
        arch = choose_archetype_for_floor(floor_index, room_tag=room_tag)
        return EnemyPackTemplate(
            id=f"_single_{arch.id}",
            name=arch.name,
            tier=arch.tier,
            member_arch_ids=[arch.id],
            preferred_room_tag=room_tag,
            weight=1.0,
        )

    weights: List[float] = []
    for pack in candidates:
        w = pack.weight
        if pack.preferred_room_tag is not None and pack.preferred_room_tag == room_tag:
            w += 1.0
        weights.append(w)

    return random.choices(candidates, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------


def _build_enemy_archetypes() -> None:
    # --- Tier 1: early-game fodder ----------------------------------------

    register_archetype(
        EnemyArchetype(
            id="goblin_skirmisher",
            name="Goblin Skirmisher",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=10,
            hp_per_floor=1.0,
            base_attack=4,
            atk_per_floor=0.7,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=6,
            xp_per_floor=1.0,
            skill_ids=[
                "poison_strike",  # new enemy-only skill
                "nimble_step",    # reuses existing defensive skill
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="goblin_brute",
            name="Goblin Brute",
            role="Brute",
            tier=1,
            ai_profile="brute",
            base_hp=16,
            hp_per_floor=1.5,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=8,
            xp_per_floor=1.1,
            skill_ids=[
                "heavy_slam",      # big single-hit
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="bandit_cutthroat",
            name="Bandit Cutthroat",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=12,
            hp_per_floor=1.2,
            base_attack=5,
            atk_per_floor=0.9,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=7,
            xp_per_floor=1.1,
            skill_ids=[
                "lunge",           # uses existing hero-style skill
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="cultist_adept",
            name="Cultist Adept",
            role="Invoker",
            tier=1,
            ai_profile="caster",
            base_hp=11,
            hp_per_floor=1.1,
            base_attack=4,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=9,
            xp_per_floor=1.3,
            skill_ids=[
                "dark_hex",        # curse / debuff
            ],
        )
    )

    # --- Tier 2: midgame threats ------------------------------------------

    register_archetype(
        EnemyArchetype(
            id="ghoul_ripper",
            name="Ghoul Ripper",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=22,
            hp_per_floor=2.0,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.4,
            base_xp=14,
            xp_per_floor=1.8,
            skill_ids=[
                "feral_claws",     # bleeding DOT
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="orc_raider",
            name="Orc Raider",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=26,
            hp_per_floor=2.2,
            base_attack=8,
            atk_per_floor=1.2,
            base_defense=2,
            def_per_floor=0.5,
            base_xp=16,
            xp_per_floor=2.0,
            skill_ids=[
                "heavy_slam",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="dark_adept",
            name="Dark Adept",
            role="Invoker",
            tier=2,
            ai_profile="caster",
            base_hp=18,
            hp_per_floor=1.8,
            base_attack=6,
            atk_per_floor=1.1,
            base_defense=1,
            def_per_floor=0.4,
            base_xp=18,
            xp_per_floor=2.2,
            skill_ids=[
                "dark_hex",
                "crippling_blow",
            ],
        )
    )

    # --- Tier 3: late floors / scary stuff --------------------------------

    register_archetype(
        EnemyArchetype(
            id="dread_knight",
            name="Dread Knight",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=40,
            hp_per_floor=3.0,
            base_attack=11,
            atk_per_floor=1.5,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=26,
            xp_per_floor=3.0,
            skill_ids=[
                "heavy_slam",
                "war_cry",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="voidspawn_mauler",
            name="Voidspawn Mauler",
            role="Brute",
            tier=3,
            ai_profile="brute",
            base_hp=36,
            hp_per_floor=2.8,
            base_attack=10,
            atk_per_floor=1.4,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=24,
            xp_per_floor=2.8,
            skill_ids=[
                "feral_claws",
                "poison_strike",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="cultist_harbinger",
            name="Cultist Harbinger",
            role="Support",
            tier=3,
            ai_profile="caster",
            base_hp=30,
            hp_per_floor=2.4,
            base_attack=9,
            atk_per_floor=1.3,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=25,
            xp_per_floor=3.0,
            skill_ids=[
                "dark_hex",
                "crippling_blow",
            ],
        )
    )


# ---------------------------------------------------------------------------
# Pack templates
# ---------------------------------------------------------------------------


def _build_enemy_packs() -> None:
    # --- Tier 1 packs ------------------------------------------------------

    # Classic early pack: 1 brute, 2 skirmishers in lairs
    register_pack(
        EnemyPackTemplate(
            id="goblin_raiding_party",
            name="Goblin Raiding Party",
            tier=1,
            member_arch_ids=[
                "goblin_brute",
                "goblin_skirmisher",
                "goblin_skirmisher",
            ],
            preferred_room_tag="lair",
            weight=1.5,
        )
    )

    # Fast, stabby ambush
    register_pack(
        EnemyPackTemplate(
            id="bandit_ambush",
            name="Bandit Ambush",
            tier=1,
            member_arch_ids=[
                "bandit_cutthroat",
                "bandit_cutthroat",
                "goblin_skirmisher",
            ],
            preferred_room_tag=None,  # generic rooms / corridors
            weight=1.0,
        )
    )

    # Small cult cell in event-ish rooms
    register_pack(
        EnemyPackTemplate(
            id="cult_cell",
            name="Cultist Cell",
            tier=1,
            member_arch_ids=[
                "cultist_adept",
                "cultist_adept",
            ],
            preferred_room_tag="event",
            weight=1.2,
        )
    )

    # --- Tier 2 packs ------------------------------------------------------

    register_pack(
        EnemyPackTemplate(
            id="ghoul_feeders",
            name="Ghoul Feeders",
            tier=2,
            member_arch_ids=[
                "ghoul_ripper",
                "ghoul_ripper",
            ],
            preferred_room_tag="lair",
            weight=1.4,
        )
    )

    register_pack(
        EnemyPackTemplate(
            id="orc_raiding_party",
            name="Orc Raiding Party",
            tier=2,
            member_arch_ids=[
                "orc_raider",
                "orc_raider",
                "ghoul_ripper",
            ],
            preferred_room_tag="lair",
            weight=1.3,
        )
    )

    register_pack(
        EnemyPackTemplate(
            id="dark_cabal",
            name="Dark Cabal",
            tier=2,
            member_arch_ids=[
                "dark_adept",
                "cultist_adept",
            ],
            preferred_room_tag="event",
            weight=1.3,
        )
    )

    # --- Tier 3 packs ------------------------------------------------------

    register_pack(
        EnemyPackTemplate(
            id="dread_patrol",
            name="Dread Patrol",
            tier=3,
            member_arch_ids=[
                "dread_knight",
                "cultist_harbinger",
            ],
            preferred_room_tag="lair",
            weight=1.5,
        )
    )

    register_pack(
        EnemyPackTemplate(
            id="void_hunt_pack",
            name="Void Hunt Pack",
            tier=3,
            member_arch_ids=[
                "voidspawn_mauler",
                "voidspawn_mauler",
                "cultist_harbinger",
            ],
            preferred_room_tag="lair",
            weight=1.2,
        )
    )


# Build registries on import
_build_enemy_archetypes()
_build_enemy_packs()
