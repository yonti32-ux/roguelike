from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
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

    # Initiative controls turn order in battle (higher = acts earlier).
    # Defaults keep older content working without specifying values.
    base_initiative: int = 10
    init_per_floor: float = 0.0


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

# Mapping of room tags to special "unique" enemy archetype ids.
# These are used as rare spawns in matching room types.
# 
# Note: these are effectively "mini-boss" style enemies. Their actual
# minimum floor index is controlled by UNIQUE_MIN_FLOOR below so that
# we can progressively unlock tougher uniques as the player descends.
UNIQUE_ROOM_ENEMIES: Dict[str, List[str]] = {
    "graveyard": ["grave_warden"],
    "sanctum": ["sanctum_guardian"],
    "lair": ["pit_champion"],
    "treasure": ["hoard_mimic"],
}

# Minimum floor index at which a given unique can appear.
# This lets us gate early-game difficulty and introduce tougher
# uniques deeper into the dungeon.
UNIQUE_MIN_FLOOR: Dict[str, int] = {
    "grave_warden": 3,
    "sanctum_guardian": 4,
    "pit_champion": 5,
    "hoard_mimic": 3,
    # Future uniques (e.g., deeper lair/dragon-themed)
    # "dragon_highlord": 6,
}


def register_archetype(arch: EnemyArchetype) -> EnemyArchetype:
    ENEMY_ARCHETYPES[arch.id] = arch
    return arch


def get_archetype(arch_id: str) -> EnemyArchetype:
    return ENEMY_ARCHETYPES[arch_id]


def register_pack(pack: EnemyPackTemplate) -> EnemyPackTemplate:
    ENEMY_PACKS[pack.id] = pack
    return pack


def compute_scaled_stats(arch: EnemyArchetype, floor_index: int) -> tuple[int, int, int, int, int]:
    """
    Scale an archetype's stats for the given floor.

    Returns (max_hp, attack_power, defense, xp_reward, initiative).
    
    Note: Initiative scaling is intentionally slow to prevent enemies from always
    outpacing the player. Default init_per_floor is 0.0, and even when set, it
    should be kept low (e.g., 0.2-0.5 per floor max) to maintain balance.
    """
    level = max(1, floor_index)
    max_hp = int(arch.base_hp + arch.hp_per_floor * (level - 1))
    attack = int(arch.base_attack + arch.atk_per_floor * (level - 1))
    defense = int(arch.base_defense + arch.def_per_floor * (level - 1))
    xp = int(arch.base_xp + arch.xp_per_floor * (level - 1))
    
    # Initiative scaling: cap at reasonable maximum to prevent runaway scaling
    # Player gets +1 initiative every 2 levels, so enemies should scale slower
    raw_initiative = arch.base_initiative + arch.init_per_floor * (level - 1)
    # Cap initiative scaling: base + floor-based growth shouldn't exceed base + (floor * 0.5)
    # This ensures enemies don't outpace player level-based growth too much
    max_initiative = arch.base_initiative + (level - 1) * 0.5
    initiative = int(min(raw_initiative, max_initiative))
    
    return max_hp, attack, defense, xp, initiative


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

    # --- New Tier 1 Enemies ----------------------------------------------------

    register_archetype(
        EnemyArchetype(
            id="goblin_shaman",
            name="Goblin Shaman",
            role="Support",
            tier=1,
            ai_profile="caster",
            base_hp=9,
            hp_per_floor=1.0,
            base_attack=3,
            atk_per_floor=0.6,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=8,
            xp_per_floor=1.2,
            skill_ids=[
                "heal_ally",
                "buff_ally",
                "dark_hex",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="skeleton_archer",
            name="Skeleton Archer",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=10,
            hp_per_floor=1.0,
            base_attack=5,
            atk_per_floor=0.8,
            base_defense=0,
            def_per_floor=0.2,
            base_xp=7,
            xp_per_floor=1.1,
            skill_ids=[
                "mark_target",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="dire_rat",
            name="Dire Rat",
            role="Skirmisher",
            tier=1,
            ai_profile="skirmisher",
            base_hp=8,
            hp_per_floor=0.8,
            base_attack=4,
            atk_per_floor=0.7,
            base_defense=0,
            def_per_floor=0.1,
            base_xp=5,
            xp_per_floor=0.9,
            skill_ids=[
                "disease_strike",
                "nimble_step",
            ],
        )
    )

    # --- New Tier 2 Enemies ----------------------------------------------------

    register_archetype(
        EnemyArchetype(
            id="necromancer",
            name="Necromancer",
            role="Support",
            tier=2,
            ai_profile="caster",
            base_hp=20,
            hp_per_floor=1.9,
            base_attack=6,
            atk_per_floor=1.0,
            base_defense=1,
            def_per_floor=0.3,
            base_xp=17,
            xp_per_floor=2.1,
            skill_ids=[
                "dark_hex",
                "heal_ally",
                "life_drain",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="shadow_stalker",
            name="Shadow Stalker",
            role="Skirmisher",
            tier=2,
            ai_profile="skirmisher",
            base_hp=16,
            hp_per_floor=1.6,
            base_attack=8,
            atk_per_floor=1.1,
            base_defense=0,
            def_per_floor=0.3,
            base_xp=16,
            xp_per_floor=2.0,
            skill_ids=[
                "mark_target",
                "poison_strike",
                "nimble_step",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="stone_golem",
            name="Stone Golem",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=32,
            hp_per_floor=2.5,
            base_attack=6,
            atk_per_floor=0.9,
            base_defense=4,
            def_per_floor=0.6,
            base_xp=18,
            xp_per_floor=2.2,
            skill_ids=[
                "heavy_slam",
                "counter_attack",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="banshee",
            name="Banshee",
            role="Invoker",
            tier=2,
            ai_profile="caster",
            base_hp=19,
            hp_per_floor=1.8,
            base_attack=7,
            atk_per_floor=1.2,
            base_defense=0,
            def_per_floor=0.3,
            base_xp=19,
            xp_per_floor=2.3,
            skill_ids=[
                "fear_scream",
                "dark_hex",
                "berserker_rage",  # Enrages when low HP
            ],
        )
    )

    # --- New Tier 3 Enemies ----------------------------------------------------

    register_archetype(
        EnemyArchetype(
            id="lich",
            name="Lich",
            role="Elite Support",
            tier=3,
            ai_profile="caster",
            base_hp=35,
            hp_per_floor=2.8,
            base_attack=10,
            atk_per_floor=1.4,
            base_defense=2,
            def_per_floor=0.6,
            base_xp=28,
            xp_per_floor=3.2,
            skill_ids=[
                "life_drain",
                "dark_hex",
                "heal_ally",
                "regeneration",
            ],
        )
    )

    # --- Room-themed unique enemies (rare spawns) ------------------------------

    # Graveyard unique: tougher undead guardian
    register_archetype(
        EnemyArchetype(
            id="grave_warden",
            name="Grave Warden",
            role="Elite Support",
            tier=2,
            ai_profile="caster",
            base_hp=32,
            hp_per_floor=2.2,
            base_attack=8,
            atk_per_floor=1.2,
            base_defense=3,
            def_per_floor=0.6,
            base_xp=26,
            xp_per_floor=2.6,
            skill_ids=[
                "dark_hex",
                "fear_scream",
                "regeneration",
            ],
        )
    )

    # Sanctum unique: defensive guardian
    register_archetype(
        EnemyArchetype(
            id="sanctum_guardian",
            name="Sanctum Guardian",
            role="Elite Brute",
            tier=2,
            ai_profile="brute",
            base_hp=38,
            hp_per_floor=2.5,
            base_attack=7,
            atk_per_floor=1.0,
            base_defense=4,
            def_per_floor=0.7,
            base_xp=24,
            xp_per_floor=2.4,
            skill_ids=[
                "heavy_slam",
                "counter_attack",
                "war_cry",
            ],
        )
    )

    # Lair unique: brutal champion
    register_archetype(
        EnemyArchetype(
            id="pit_champion",
            name="Pit Champion",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=50,
            hp_per_floor=3.2,
            base_attack=13,
            atk_per_floor=1.7,
            base_defense=4,
            def_per_floor=0.8,
            base_xp=34,
            xp_per_floor=3.4,
            skill_ids=[
                "heavy_slam",
                "berserker_rage",
                "war_cry",
            ],
        )
    )

    # Treasure unique: mimic-style boss
    register_archetype(
        EnemyArchetype(
            id="hoard_mimic",
            name="Hoard Mimic",
            role="Brute",
            tier=2,
            ai_profile="brute",
            base_hp=36,
            hp_per_floor=2.3,
            base_attack=9,
            atk_per_floor=1.2,
            base_defense=3,
            def_per_floor=0.5,
            base_xp=28,
            xp_per_floor=2.8,
            skill_ids=[
                "heavy_slam",
                "feral_claws",
            ],
        )
    )

    register_archetype(
        EnemyArchetype(
            id="dragonkin",
            name="Dragonkin",
            role="Elite Brute",
            tier=3,
            ai_profile="brute",
            base_hp=45,
            hp_per_floor=3.2,
            base_attack=12,
            atk_per_floor=1.6,
            base_defense=3,
            def_per_floor=0.7,
            base_xp=30,
            xp_per_floor=3.5,
            skill_ids=[
                "heavy_slam",
                "berserker_rage",
                "war_cry",
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

    # --- Themed packs for new room types --------------------------------------

    # Graveyard rooms: undead-heavy encounters
    register_pack(
        EnemyPackTemplate(
            id="graveyard_undead_pack_t1",
            name="Restless Dead",
            tier=1,
            member_arch_ids=[
                "skeleton_archer",
                "dire_rat",
                "cultist_adept",
            ],
            preferred_room_tag="graveyard",
            weight=1.4,
        )
    )

    register_pack(
        EnemyPackTemplate(
            id="graveyard_undead_pack_t2",
            name="Desecrated Burial",
            tier=2,
            member_arch_ids=[
                "necromancer",
                "ghoul_ripper",
                "ghoul_ripper",
            ],
            preferred_room_tag="graveyard",
            weight=1.6,
        )
    )

    register_pack(
        EnemyPackTemplate(
            id="graveyard_undead_pack_t3",
            name="Court of the Damned",
            tier=3,
            member_arch_ids=[
                "lich",
                "banshee",
                "dread_knight",
            ],
            preferred_room_tag="graveyard",
            weight=1.6,
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

    # --- New Synergistic Packs -------------------------------------------------

    # Tier 1: Goblin pack with shaman support
    register_pack(
        EnemyPackTemplate(
            id="goblin_warband",
            name="Goblin Warband",
            tier=1,
            member_arch_ids=[
                "goblin_brute",
                "goblin_skirmisher",
                "goblin_shaman",
            ],
            preferred_room_tag="lair",
            weight=1.3,
        )
    )

    # Tier 1: Swarm of rats
    register_pack(
        EnemyPackTemplate(
            id="rat_swarm",
            name="Rat Swarm",
            tier=1,
            member_arch_ids=[
                "dire_rat",
                "dire_rat",
                "dire_rat",
            ],
            preferred_room_tag=None,
            weight=1.1,
        )
    )

    # Tier 1: Skeleton archers with support
    register_pack(
        EnemyPackTemplate(
            id="skeleton_ambush",
            name="Skeleton Ambush",
            tier=1,
            member_arch_ids=[
                "skeleton_archer",
                "skeleton_archer",
                "goblin_shaman",
            ],
            preferred_room_tag=None,
            weight=1.2,
        )
    )

    # Tier 2: Necromancer with undead minions
    register_pack(
        EnemyPackTemplate(
            id="necromancer_retinue",
            name="Necromancer's Retinue",
            tier=2,
            member_arch_ids=[
                "necromancer",
                "ghoul_ripper",
                "ghoul_ripper",
            ],
            preferred_room_tag="event",
            weight=1.4,
        )
    )

    # Tier 2: Shadow stalkers working together
    register_pack(
        EnemyPackTemplate(
            id="shadow_hunters",
            name="Shadow Hunters",
            tier=2,
            member_arch_ids=[
                "shadow_stalker",
                "shadow_stalker",
                "dark_adept",
            ],
            preferred_room_tag=None,
            weight=1.3,
        )
    )

    # Tier 2: Tanky golem with support
    register_pack(
        EnemyPackTemplate(
            id="golem_guardians",
            name="Golem Guardians",
            tier=2,
            member_arch_ids=[
                "stone_golem",
                "necromancer",
            ],
            preferred_room_tag="lair",
            weight=1.3,
        )
    )

    # Tier 2: Banshee with undead
    register_pack(
        EnemyPackTemplate(
            id="haunted_encounter",
            name="Haunted Encounter",
            tier=2,
            member_arch_ids=[
                "banshee",
                "ghoul_ripper",
                "ghoul_ripper",
            ],
            preferred_room_tag="event",
            weight=1.2,
        )
    )

    # Tier 3: Lich with powerful minions
    register_pack(
        EnemyPackTemplate(
            id="lich_court",
            name="Lich's Court",
            tier=3,
            member_arch_ids=[
                "lich",
                "dread_knight",
                "cultist_harbinger",
            ],
            preferred_room_tag="lair",
            weight=1.5,
        )
    )

    # Tier 3: Dragonkin boss encounter
    register_pack(
        EnemyPackTemplate(
            id="dragonkin_warriors",
            name="Dragonkin Warriors",
            tier=3,
            member_arch_ids=[
                "dragonkin",
                "orc_raider",
                "orc_raider",
            ],
            preferred_room_tag="lair",
            weight=1.4,
        )
    )


# ---------------------------------------------------------------------------
# Elite system - modular elite enemy variants
# ---------------------------------------------------------------------------

# Elite spawn chance per enemy (can be overridden by floor)
BASE_ELITE_SPAWN_CHANCE = 0.15  # 15% chance for any enemy to spawn as elite

# Elite stat multipliers (applied to base stats)
ELITE_HP_MULTIPLIER = 1.5  # +50% HP
ELITE_ATTACK_MULTIPLIER = 1.25  # +25% attack
ELITE_DEFENSE_MULTIPLIER = 1.2  # +20% defense
ELITE_XP_MULTIPLIER = 2.0  # +100% XP (elites are worth more)

# Additional XP bonus just for "unique" enemies (room-themed mini-bosses).
# This stacks on top of the elite multiplier so that uniques feel especially
# rewarding to defeat.
UNIQUE_XP_BONUS_MULTIPLIER = 1.5  # +50% XP on top of elite bonus


def is_elite_spawn(floor_index: int, base_chance: float = BASE_ELITE_SPAWN_CHANCE) -> bool:
    """
    Determine if an enemy should spawn as elite.
    
    Args:
        floor_index: Current floor depth
        base_chance: Base spawn chance (defaults to BASE_ELITE_SPAWN_CHANCE)
    
    Returns:
        True if this enemy should be elite
    """
    # Elite chance scales slightly with floor depth (more elites deeper)
    # Floors 1-2: base chance
    # Floors 3-4: +5% chance
    # Floors 5+: +10% chance
    if floor_index <= 2:
        chance = base_chance
    elif floor_index <= 4:
        chance = base_chance + 0.05
    else:
        chance = base_chance + 0.10
    
    return random.random() < chance


def apply_elite_modifiers(
    max_hp: int,
    attack_power: int,
    defense: int,
    xp_reward: int,
) -> Tuple[int, int, int, int]:
    """
    Apply elite stat multipliers to enemy stats.
    
    Args:
        max_hp: Base max HP
        attack_power: Base attack power
        defense: Base defense
        xp_reward: Base XP reward
    
    Returns:
        Tuple of (elite_max_hp, elite_attack_power, elite_defense, elite_xp_reward)
    """
    elite_hp = int(max_hp * ELITE_HP_MULTIPLIER)
    elite_attack = int(attack_power * ELITE_ATTACK_MULTIPLIER)
    elite_defense = int(defense * ELITE_DEFENSE_MULTIPLIER)
    elite_xp = int(xp_reward * ELITE_XP_MULTIPLIER)
    
    return elite_hp, elite_attack, elite_defense, elite_xp


def make_enemy_elite(enemy, floor_index: int) -> None:
    """
    Convert an existing enemy to an elite variant.
    
    This modifies the enemy in-place, applying:
    - Enhanced stats (HP, attack, defense, XP)
    - Elite name prefix ("Elite")
    - Elite flag for visual/mechanical identification
    
    Args:
        enemy: Enemy entity to make elite
        floor_index: Current floor (for stat scaling)
    """
    # Mark as elite
    setattr(enemy, "is_elite", True)
    
    # Get current stats (or compute from archetype if needed)
    max_hp = getattr(enemy, "max_hp", 12)
    attack_power = getattr(enemy, "attack_power", 4)
    defense = getattr(enemy, "defense", 0)
    xp_reward = getattr(enemy, "xp_reward", 5)
    
    # Apply elite modifiers
    elite_hp, elite_attack, elite_defense, elite_xp = apply_elite_modifiers(
        max_hp, attack_power, defense, xp_reward
    )
    
    # Update stats
    setattr(enemy, "max_hp", elite_hp)
    setattr(enemy, "hp", elite_hp)  # Full heal when becoming elite
    setattr(enemy, "attack_power", elite_attack)
    setattr(enemy, "defense", elite_defense)
    setattr(enemy, "xp_reward", elite_xp)
    
    # Update name with "Elite" prefix
    enemy_type = getattr(enemy, "enemy_type", "Enemy")
    if not enemy_type.startswith("Elite "):
        setattr(enemy, "enemy_type", f"Elite {enemy_type}")
        # Also update the original name for display
        setattr(enemy, "original_name", enemy_type)
    
    # If this enemy is also marked as "unique" (room-themed mini-boss),
    # give it an extra XP bonus to make the encounter feel especially
    # rewarding.
    if getattr(enemy, "is_unique", False):
        boosted_xp = int(getattr(enemy, "xp_reward", elite_xp) * UNIQUE_XP_BONUS_MULTIPLIER)
        setattr(enemy, "xp_reward", max(boosted_xp, elite_xp))

    # Elite visual indicator: slightly brighter/more vibrant color
    # We'll use a glow effect in rendering, but also tint the base color
    base_color = getattr(enemy, "color", (200, 80, 80))
    # Make elite enemies slightly brighter and more saturated
    elite_color = (
        min(255, int(base_color[0] * 1.2)),
        min(255, int(base_color[1] * 1.15)),
        min(255, int(base_color[2] * 1.1)),
    )
    setattr(enemy, "color", elite_color)


# Build registries on import
_build_enemy_archetypes()
_build_enemy_packs()
