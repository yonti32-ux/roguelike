"""
Enemy pack templates.

These define groups of enemies that spawn together, organized by tier and theme.
"""

from ..types import EnemyPackTemplate
from ..registry import register_pack


def register_all_packs() -> None:
    """Register all enemy pack templates."""
    
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
    
    # ========================================================================
    # Overworld Party Pack Templates
    # ========================================================================
    
    # Guard Patrols
    register_pack(
        EnemyPackTemplate(
            id="guard_patrol",
            name="Guard Patrol",
            tier=2,
            member_arch_ids=[
                "town_guard",
                "town_guard",
            ],
            preferred_room_tag=None,
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="guard_squad",
            name="Guard Squad",
            tier=2,
            member_arch_ids=[
                "town_guard",
                "town_guard",
                "town_guard",
            ],
            preferred_room_tag=None,
            weight=1.0,
        )
    )
    
    # Ranger Patrols
    register_pack(
        EnemyPackTemplate(
            id="ranger_patrol",
            name="Ranger Patrol",
            tier=2,
            member_arch_ids=[
                "ranger",
                "ranger",
            ],
            preferred_room_tag=None,
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="ranger_scout_party",
            name="Ranger Scout Party",
            tier=2,
            member_arch_ids=[
                "ranger",
                "scout",
                "scout",
            ],
            preferred_room_tag=None,
            weight=1.0,
        )
    )
    
    # Merchant Caravans
    register_pack(
        EnemyPackTemplate(
            id="merchant_caravan",
            name="Merchant Caravan",
            tier=1,
            member_arch_ids=[
                "merchant_guard",
                "merchant_guard",
            ],
            preferred_room_tag=None,
            weight=1.3,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="large_merchant_caravan",
            name="Large Merchant Caravan",
            tier=1,
            member_arch_ids=[
                "merchant_guard",
                "merchant_guard",
                "merchant_guard",
            ],
            preferred_room_tag=None,
            weight=0.9,
        )
    )
    
    # Noble Entourages
    register_pack(
        EnemyPackTemplate(
            id="noble_entourage",
            name="Noble Entourage",
            tier=2,
            member_arch_ids=[
                "noble_guard",
                "noble_guard",
            ],
            preferred_room_tag=None,
            weight=0.8,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="noble_retinue",
            name="Noble Retinue",
            tier=2,
            member_arch_ids=[
                "noble_guard",
                "noble_guard",
                "noble_guard",
            ],
            preferred_room_tag=None,
            weight=0.6,
        )
    )
    
    # Civilian Groups
    register_pack(
        EnemyPackTemplate(
            id="villager_group",
            name="Villager Group",
            tier=1,
            member_arch_ids=[
                "villager",
                "villager",
                "villager",
            ],
            preferred_room_tag=None,
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="pilgrim_group",
            name="Pilgrim Group",
            tier=1,
            member_arch_ids=[
                "pilgrim",
                "pilgrim",
                "pilgrim",
            ],
            preferred_room_tag=None,
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="scout_party",
            name="Scout Party",
            tier=1,
            member_arch_ids=[
                "scout",
                "scout",
            ],
            preferred_room_tag=None,
            weight=1.0,
        )
    )
    
    # Mixed Civilian Groups
    register_pack(
        EnemyPackTemplate(
            id="traveling_group",
            name="Traveling Group",
            tier=1,
            member_arch_ids=[
                "villager",
                "villager",
                "pilgrim",
            ],
            preferred_room_tag=None,
            weight=1.0,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="merchant_with_escort",
            name="Merchant with Escort",
            tier=1,
            member_arch_ids=[
                "merchant_guard",
                "merchant_guard",
                "villager",
            ],
            preferred_room_tag=None,
            weight=1.1,
        )
    )
    
    # ========================================================================
    # NEW PACKS - Using New Enemies
    # ========================================================================
    
    # --- Early Game Packs (Tier 1) ---
    
    register_pack(
        EnemyPackTemplate(
            id="goblin_trapper_ambush",
            name="Goblin Trapper Ambush",
            tier=1,
            member_arch_ids=[
                "goblin_trapper",
                "goblin_trapper",
                "goblin_skirmisher",
            ],
            preferred_room_tag=None,
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="skeleton_legion",
            name="Skeleton Legion",
            tier=1,
            member_arch_ids=[
                "skeleton_warrior",
                "skeleton_archer",
                "skeleton_warrior",
            ],
            preferred_room_tag="graveyard",
            weight=1.3,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="beast_swarm",
            name="Beast Swarm",
            tier=1,
            member_arch_ids=[
                "wild_boar",
                "spider_scout",
                "dire_rat",
            ],
            preferred_room_tag=None,
            weight=1.4,
        )
    )
    
    # --- Mid Game Packs (Tier 2) ---
    
    register_pack(
        EnemyPackTemplate(
            id="wraith_pack",
            name="Wraith Pack",
            tier=2,
            member_arch_ids=[
                "wraith",
                "wraith",
                "banshee",
            ],
            preferred_room_tag="graveyard",
            weight=1.3,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="troll_war_band",
            name="Troll War Band",
            tier=2,
            member_arch_ids=[
                "troll_berserker",
                "cave_troll",
                "orc_raider",
            ],
            preferred_room_tag="lair",
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="elemental_storm",
            name="Elemental Storm",
            tier=2,
            member_arch_ids=[
                "fire_elemental",
                "ice_wraith",
                "storm_elemental",
            ],
            preferred_room_tag="event",
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="hellhound_pack",
            name="Hellhound Pack",
            tier=2,
            member_arch_ids=[
                "hellhound",
                "hellhound",
                "dire_wolf",
            ],
            preferred_room_tag=None,
            weight=1.3,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="dark_coven",
            name="Dark Coven",
            tier=2,
            member_arch_ids=[
                "dark_ritualist",
                "corrupted_priest",
                "cultist_adept",
            ],
            preferred_room_tag="event",
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="plague_carriers",
            name="Plague Carriers",
            tier=2,
            member_arch_ids=[
                "plague_bearer",
                "ghoul_ripper",
                "ghoul_ripper",
            ],
            preferred_room_tag="graveyard",
            weight=1.3,
        )
    )
    
    # --- Late Game Packs (Tier 3) ---
    
    register_pack(
        EnemyPackTemplate(
            id="death_knights_guard",
            name="Death Knights' Guard",
            tier=3,
            member_arch_ids=[
                "death_knight",
                "death_knight",
                "vampire_noble",
            ],
            preferred_room_tag="lair",
            weight=1.4,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="void_mages_cabal",
            name="Void Mages' Cabal",
            tier=3,
            member_arch_ids=[
                "void_mage",
                "archmage",
                "cultist_harbinger",
            ],
            preferred_room_tag="event",
            weight=1.3,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="behemoth_guardians",
            name="Behemoth Guardians",
            tier=3,
            member_arch_ids=[
                "behemoth",
                "ancient_guardian",
                "iron_golem",
            ],
            preferred_room_tag="lair",
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="shadow_lords_court",
            name="Shadow Lord's Court",
            tier=3,
            member_arch_ids=[
                "shadow_lord",
                "soul_reaper",
                "blood_fiend",
            ],
            preferred_room_tag="lair",
            weight=1.3,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="chaos_horde",
            name="Chaos Horde",
            tier=3,
            member_arch_ids=[
                "chaos_spawn",
                "chaos_spawn",
                "voidspawn_mauler",
            ],
            preferred_room_tag="lair",
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="frost_giant_warriors",
            name="Frost Giant Warriors",
            tier=3,
            member_arch_ids=[
                "frost_giant",
                "ice_wraith",
                "ice_wraith",
            ],
            preferred_room_tag="lair",
            weight=1.0,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="abyssal_terror",
            name="Abyssal Terror",
            tier=3,
            member_arch_ids=[
                "abyssal_horror",
                "void_mage",
                "blood_fiend",
            ],
            preferred_room_tag="lair",
            weight=0.9,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="bone_dragon_guard",
            name="Bone Dragon Guard",
            tier=3,
            member_arch_ids=[
                "bone_dragon",
                "skeleton_warrior",
                "skeleton_warrior",
            ],
            preferred_room_tag="graveyard",
            weight=0.8,
        )
    )
    
    # --- Tactical Packs with Advanced AI Profiles ---------------------------
    
    # Mid-Game Tactical Packs
    
    register_pack(
        EnemyPackTemplate(
            id="orc_warband",
            name="Orc Warband",
            tier=2,
            member_arch_ids=[
                "orc_warlord",      # commander - coordinates team
                "orc_raider",       # brute - front line
                "orc_raider",      # brute - front line
                "shadow_assassin",  # assassin - picks off isolated targets
            ],
            preferred_room_tag="lair",
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="necromancer_circle",
            name="Necromancer Circle",
            tier=2,
            member_arch_ids=[
                "necromancer",      # controller - debuffs and crowd control
                "ghoul_ripper",     # brute - front line
                "ghoul_ripper",     # brute - front line
                "dark_adept",       # caster - damage
            ],
            preferred_room_tag="event",
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="guardian_formation",
            name="Guardian Formation",
            tier=2,
            member_arch_ids=[
                "stone_guardian",   # defender - protects allies
                "fire_elemental",    # caster - ranged damage
                "ice_wraith",        # caster - ranged damage
            ],
            preferred_room_tag="lair",
            weight=1.0,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="berserker_band",
            name="Berserker Band",
            tier=2,
            member_arch_ids=[
                "troll_berserker",  # berserker - aggressive when low HP
                "troll_berserker",  # berserker - aggressive when low HP
                "orc_raider",       # brute - support
            ],
            preferred_room_tag="lair",
            weight=1.0,
        )
    )
    
    # Late-Game Tactical Packs
    
    register_pack(
        EnemyPackTemplate(
            id="death_legion",
            name="Death Legion",
            tier=3,
            member_arch_ids=[
                "archlich",         # commander - coordinates undead
                "dread_knight",     # tactician - smart positioning
                "dread_knight",     # tactician - smart positioning
                "soul_reaper",      # caster - support
            ],
            preferred_room_tag="lair",
            weight=1.3,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="void_strike_team",
            name="Void Strike Team",
            tier=3,
            member_arch_ids=[
                "void_assassin",    # assassin - picks off targets
                "void_assassin",    # assassin - picks off targets
                "void_mage",        # controller - debuffs
            ],
            preferred_room_tag=None,
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="dread_guardians",
            name="Dread Guardians",
            tier=3,
            member_arch_ids=[
                "dread_guardian",   # defender - protects allies
                "shadow_lord",      # support - heals and buffs
                "abyssal_horror",   # controller - crowd control
            ],
            preferred_room_tag="lair",
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="chaos_warriors",
            name="Chaos Warriors",
            tier=3,
            member_arch_ids=[
                "chaos_lord",       # berserker - aggressive
                "death_knight",     # tactician - smart combos
                "voidspawn_mauler", # brute - front line
            ],
            preferred_room_tag="lair",
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="elite_tactical_team",
            name="Elite Tactical Team",
            tier=3,
            member_arch_ids=[
                "archlich",         # commander - coordinates
                "death_knight",     # tactician - smart positioning
                "dread_guardian",   # defender - protects
                "void_assassin",    # assassin - picks off targets
            ],
            preferred_room_tag="lair",
            weight=0.9,  # Rare, very challenging
        )
    )
    
    # --- Additional Tactical Packs with New Enemies -------------------------
    
    # Early-Game Packs
    
    register_pack(
        EnemyPackTemplate(
            id="goblin_warband",
            name="Goblin Warband",
            tier=1,
            member_arch_ids=[
                "goblin_brute",
                "goblin_skirmisher",
                "goblin_shaman",  # Support caster
                "goblin_trapper",  # Assassin
            ],
            preferred_room_tag="lair",
            weight=1.3,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="bandit_company",
            name="Bandit Company",
            tier=1,
            member_arch_ids=[
                "bandit_cutthroat",
                "bandit_archer",
                "bandit_cutthroat",
            ],
            preferred_room_tag=None,
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="undead_rising",
            name="Undead Rising",
            tier=1,
            member_arch_ids=[
                "skeleton_warrior",
                "skeleton_warrior",
                "cultist_adept",  # Summoner
            ],
            preferred_room_tag="graveyard",
            weight=1.0,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="beast_pack",
            name="Beast Pack",
            tier=1,
            member_arch_ids=[
                "wild_boar",  # Berserker
                "wolf",
                "dire_rat",
            ],
            preferred_room_tag="lair",
            weight=1.2,
        )
    )
    
    # Mid-Game Packs
    
    register_pack(
        EnemyPackTemplate(
            id="orc_war_party",
            name="Orc War Party",
            tier=2,
            member_arch_ids=[
                "orc_warlord",  # Commander
                "orc_shaman",  # Support
                "orc_raider",
                "orc_raider",
            ],
            preferred_room_tag="lair",
            weight=1.2,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="elemental_guardians",
            name="Elemental Guardians",
            tier=2,
            member_arch_ids=[
                "earth_elemental",  # Defender
                "fire_elemental",
                "ice_wraith",
            ],
            preferred_room_tag="lair",
            weight=1.0,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="shadow_coven",
            name="Shadow Coven",
            tier=2,
            member_arch_ids=[
                "shadow_assassin",
                "shadow_stalker",  # Assassin
                "dark_ranger",  # Tactician
            ],
            preferred_room_tag=None,
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="troll_war_band",
            name="Troll War Band",
            tier=2,
            member_arch_ids=[
                "troll_berserker",
                "cave_troll",  # Berserker
                "ogre_warrior",  # Berserker
            ],
            preferred_room_tag="lair",
            weight=1.0,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="undead_legion",
            name="Undead Legion",
            tier=2,
            member_arch_ids=[
                "necromancer",  # Controller
                "bone_mage",  # Controller
                "ghoul_ripper",
                "ghoul_ripper",
            ],
            preferred_room_tag="graveyard",
            weight=1.1,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="construct_defense",
            name="Construct Defense",
            tier=2,
            member_arch_ids=[
                "stone_guardian",  # Defender
                "iron_golem",  # Defender
                "arcane_golem",
            ],
            preferred_room_tag="lair",
            weight=0.9,
        )
    )
    
    # Late-Game Packs
    
    register_pack(
        EnemyPackTemplate(
            id="dragon_guard",
            name="Dragon Guard",
            tier=3,
            member_arch_ids=[
                "dragon_knight",  # Tactician
                "ancient_dragon",  # Tactician
                "frost_giant_berserker",  # Berserker
            ],
            preferred_room_tag="lair",
            weight=0.8,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="void_legion",
            name="Void Legion",
            tier=3,
            member_arch_ids=[
                "void_guardian",  # Defender
                "void_titan",  # Defender
                "void_mage",  # Controller
                "void_assassin",  # Assassin
            ],
            preferred_room_tag="lair",
            weight=0.9,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="demon_horde",
            name="Demon Horde",
            tier=3,
            member_arch_ids=[
                "demon_lord",  # Commander
                "chaos_lord",  # Berserker
                "blood_fiend",  # Assassin
                "blood_fiend",
            ],
            preferred_room_tag="lair",
            weight=0.7,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="lich_army",
            name="Lich Army",
            tier=3,
            member_arch_ids=[
                "lich_king",  # Commander
                "archlich",  # Commander
                "soul_reaper",  # Controller
                "dread_knight",  # Tactician
                "dread_guardian",  # Defender
            ],
            preferred_room_tag="lair",
            weight=0.6,  # Very rare, extremely challenging
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="shadow_court",
            name="Shadow Court",
            tier=3,
            member_arch_ids=[
                "shadow_weaver",  # Controller
                "shadow_lord",  # Support
                "void_assassin",  # Assassin
                "abyssal_horror",  # Controller
            ],
            preferred_room_tag="lair",
            weight=0.8,
        )
    )
    
    register_pack(
        EnemyPackTemplate(
            id="ultimate_guardians",
            name="Ultimate Guardians",
            tier=3,
            member_arch_ids=[
                "void_titan",  # Defender
                "ancient_dragon",  # Tactician
                "dread_guardian",  # Defender
            ],
            preferred_room_tag="lair",
            weight=0.5,  # Extremely rare
        )
    )
