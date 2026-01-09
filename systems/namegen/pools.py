"""
Shared name pools used across all name generators.

These pools contain building blocks for generating names:
syllables, prefixes, suffixes, descriptors, etc.
"""

from .base import NamePools
import random


# Syllable pools for constructing names
FANTASY_SYLLABLES = [
    "gor", "thak", "mal", "char", "nix", "arth", "mor", "gal", "thor",
    "zel", "xyl", "syl", "arc", "cel", "drax", "vex", "kor", "zar",
    "ven", "nex", "ryl", "tarn", "val", "mir", "thor", "brax", "lyn",
]

BRUTAL_SYLLABLES = [
    "krul", "zarg", "vor", "gorth", "thrak", "mort", "drak", "grath",
    "skarn", "blak", "vorth", "rath", "grash", "mort", "krag", "borth",
    "zark", "grom", "thrax", "vorak",
]

MYSTICAL_SYLLABLES = [
    "arc", "cel", "xyl", "sylph", "merid", "elest", "ether", "myth",
    "aura", "lumen", "stella", "luna", "sol", "nimbus", "veil", "mist",
    "shade", "glim", "ray", "beam",
]

BEAST_SYLLABLES = [
    "fang", "claw", "dire", "iron", "shadow", "venom", "scale", "hide",
    "horn", "talon", "tooth", "beast", "wild", "feral", "savage",
]

# Prefix pools
DUNGEON_PREFIXES = [
    "Dark", "Ancient", "Cursed", "Forgotten", "Haunted", "Abandoned",
    "Lost", "Ruined", "Shadow", "Blood", "Death", "Black", "Crimson",
    "Eternal", "Doomed", "Twisted", "Corrupted",
]

TOWN_PREFIXES = [
    "New", "Old", "Green", "Iron", "Gold", "Silver", "Bright", "Dark",
    "Sun", "Moon", "Star", "Oak", "Stone", "Hill", "Valley", "River",
    "North", "South", "East", "West", "Fair", "White", "Black",
]

# Suffix pools
DUNGEON_SUFFIXES = [
    "Crypt", "Caverns", "Keep", "Temple", "Tomb", "Catacombs", "Vault",
    "Sanctum", "Lair", "Den", "Pit", "Abyss", "Chamber", "Hall",
    "Fortress", "Tower", "Dungeon", "Maze", "Prison", "Cage",
]

TOWN_SUFFIXES = [
    "ville", "ton", "ham", "burgh", "ford", "port", "field", "vale",
    "dale", "bridge", "wood", "hill", "peak", "moor", "haven", "rest",
    "watch", "point", "shore", "grove",
]

# Descriptor/Adjective pools (tiered)
BRUTAL_DESCRIPTORS_T1 = [
    "the Bold", "the Fierce", "the Ruthless", "the Cunning",
    "the Savage", "the Brutal", "the Merciless",
]

BRUTAL_DESCRIPTORS_T2 = [
    "the Bloodthirsty", "the Terrible", "the Unstoppable", "the Savage",
    "the Destroyer", "the Warlord", "the Conqueror", "the Furious",
]

BRUTAL_DESCRIPTORS_T3 = [
    "the Destroyer", "the Annihilator", "the Harbinger", "the Executioner",
    "the Slayer", "the Butcher", "the Ruiner",
]

MYSTICAL_DESCRIPTORS_T1 = [
    "the Wise", "the Enlightened", "the Mystic", "the Arcane",
]

MYSTICAL_DESCRIPTORS_T2 = [
    "the Ancient", "the Elder", "the Warden", "the Keeper",
]

MYSTICAL_DESCRIPTORS_T3 = [
    "the Ancient", "the Eternal", "the Omnipotent", "the Transcendent",
]

FINAL_BOSS_TITLES = [
    "the Final Guardian", "the Last Warden", "the Ultimate Keeper",
    "the End of All", "the Final Arbiter", "the Eternal Keeper",
    "the Last Stand", "the Final Trial",
]

# Dungeon descriptors
DUNGEON_DESCRIPTORS = [
    "of Shadows", "of the Damned", "of Despair", "of Doom",
    "of Darkness", "of Fear", "of the Lost", "of Ruin",
]

# Geographical terms
TERRAIN_TYPES = [
    "Valley", "Peak", "Forest", "Marsh", "Desert", "Plains", "Hills",
    "Mountains", "Coast", "Island", "Peninsula",
]

STRUCTURE_TYPES = [
    "Tower", "Castle", "Fortress", "Keep", "Manor", "Hall", "Academy",
    "Temple", "Sanctuary", "Monastery",
]


def create_name_pools() -> NamePools:
    """
    Create and return a NamePools instance with all pools populated.
    
    Returns:
        NamePools instance ready for use
    """
    return NamePools(
        fantasy_syllables=FANTASY_SYLLABLES,
        brutal_syllables=BRUTAL_SYLLABLES,
        mystical_syllables=MYSTICAL_SYLLABLES,
        beast_syllables=BEAST_SYLLABLES,
        dungeon_prefixes=DUNGEON_PREFIXES,
        town_prefixes=TOWN_PREFIXES,
        dungeon_suffixes=DUNGEON_SUFFIXES,
        town_suffixes=TOWN_SUFFIXES,
        brutal_descriptors=BRUTAL_DESCRIPTORS_T1 + BRUTAL_DESCRIPTORS_T2 + BRUTAL_DESCRIPTORS_T3,
        mystical_descriptors=MYSTICAL_DESCRIPTORS_T1 + MYSTICAL_DESCRIPTORS_T2 + MYSTICAL_DESCRIPTORS_T3,
        dungeon_descriptors=DUNGEON_DESCRIPTORS,
        terrain_types=TERRAIN_TYPES,
        structure_types=STRUCTURE_TYPES,
    )


# Global pools instance (created on import)
_global_pools: NamePools = None


def get_pools() -> NamePools:
    """
    Get the global name pools instance.
    Creates it on first access.
    
    Returns:
        Global NamePools instance
    """
    global _global_pools
    if _global_pools is None:
        _global_pools = create_name_pools()
    return _global_pools


def get_brutal_descriptor_for_tier(tier: int) -> str:
    """Get a brutal descriptor appropriate for the given tier."""
    if tier <= 1:
        pool = BRUTAL_DESCRIPTORS_T1
    elif tier == 2:
        pool = BRUTAL_DESCRIPTORS_T2
    else:
        pool = BRUTAL_DESCRIPTORS_T3
    return random.choice(pool)


def get_mystical_descriptor_for_tier(tier: int) -> str:
    """Get a mystical descriptor appropriate for the given tier."""
    if tier <= 1:
        pool = MYSTICAL_DESCRIPTORS_T1
    elif tier == 2:
        pool = MYSTICAL_DESCRIPTORS_T2
    else:
        pool = MYSTICAL_DESCRIPTORS_T3
    return random.choice(pool)

