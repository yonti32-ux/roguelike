"""
Faction generator.

Generates random factions for each playthrough, creating unique worlds.
"""

import random
from typing import List, Dict, Optional, Tuple

from systems.factions import Faction, FactionAlignment, register_faction


# Faction name components for generation
FACTION_NAME_PREFIXES = [
    "Kingdom of", "Empire of", "Realm of", "Domain of", "Land of",
    "Free", "United", "Grand", "High", "Ancient",
    "Shadow", "Dark", "Crimson", "Iron", "Golden",
]

FACTION_NAME_SUFFIXES = [
    "Aetheria", "Valoria", "Eldoria", "Nordheim", "Southend",
    "Westmarch", "Eastwind", "Northreach", "Southhold",
    "Crimson", "Shadow", "Iron", "Golden", "Silver",
    "Storm", "Fire", "Ice", "Stone", "Wood",
    "Winds", "Tides", "Flames", "Frost", "Thunder",
]

FACTION_NAME_TYPES = [
    "Cities", "Towns", "Villages", "Tribes", "Clans",
    "Alliance", "Confederacy", "League", "Guild", "Order",
    "Cult", "Brotherhood", "Sisterhood", "Circle", "Council",
]

# POI type preferences by alignment
ALIGNMENT_POI_PREFERENCES = {
    FactionAlignment.GOOD: {
        "town": 3.0,
        "village": 2.5,
        "castle": 2.0,
        "camp": 0.5,
    },
    FactionAlignment.NEUTRAL: {
        "town": 2.0,
        "village": 2.0,
        "camp": 1.5,
        "castle": 0.5,
    },
    FactionAlignment.EVIL: {
        "camp": 3.0,
        "bandit_camp": 2.5,
        "cult_sanctuary": 2.0,
        "town": 0.3,
        "village": 0.5,
    },
}

# Party type preferences by alignment
ALIGNMENT_PARTY_PREFERENCES = {
    FactionAlignment.GOOD: {
        "guard": 2.5,
        "villager": 2.0,
        "ranger": 1.5,
        "adventurer": 1.0,
        "pilgrim": 1.0,
        "merchant": 0.8,
    },
    FactionAlignment.NEUTRAL: {
        "merchant": 2.5,
        "trader": 2.0,
        "villager": 1.5,
        "scout": 1.5,
        "noble": 1.0,
    },
    FactionAlignment.EVIL: {
        "bandit": 2.5,
        "goblin": 2.0,
        "orc": 1.8,
        "cultist": 1.5,
        "monster": 1.0,
        "wolf": 0.8,
    },
}

# Color ranges by alignment (RGB)
ALIGNMENT_COLORS = {
    FactionAlignment.GOOD: {
        "base": (100, 150, 255),  # Blue tones
        "variations": [
            (80, 130, 220), (120, 170, 255), (90, 140, 240),
            (110, 160, 250), (100, 150, 230),
        ],
    },
    FactionAlignment.NEUTRAL: {
        "base": (200, 200, 200),  # Gray tones
        "variations": [
            (180, 180, 180), (220, 220, 220), (190, 190, 190),
            (210, 210, 210), (200, 200, 180),
        ],
    },
    FactionAlignment.EVIL: {
        "base": (200, 0, 0),  # Red/dark tones
        "variations": [
            (180, 0, 50), (220, 20, 20), (150, 0, 100),
            (200, 50, 0), (139, 0, 139),  # Dark magenta
        ],
    },
}


def generate_faction_name(alignment: FactionAlignment, seed: Optional[int] = None) -> str:
    """
    Generate a random faction name based on alignment.
    
    Args:
        alignment: Faction alignment
        seed: Optional random seed for deterministic generation
        
    Returns:
        Generated faction name
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random
    
    # Different naming patterns by alignment
    if alignment == FactionAlignment.GOOD:
        # Good factions: "Kingdom of X", "Realm of X", etc.
        if rng.random() < 0.6:
            prefix = rng.choice(FACTION_NAME_PREFIXES[:5])  # First 5 are "of" types
            suffix = rng.choice(FACTION_NAME_SUFFIXES)
            return f"{prefix} {suffix}"
        else:
            # Sometimes just a name
            return rng.choice(FACTION_NAME_SUFFIXES)
    
    elif alignment == FactionAlignment.NEUTRAL:
        # Neutral: "Free X", "United X", or type-based
        if rng.random() < 0.5:
            prefix = rng.choice(["Free", "United", "Independent"])
            suffix = rng.choice(FACTION_NAME_TYPES[:5])  # Cities, Towns, etc.
            return f"{prefix} {suffix}"
        else:
            name = rng.choice(FACTION_NAME_SUFFIXES)
            type_name = rng.choice(FACTION_NAME_TYPES[:5])
            return f"{name} {type_name}"
    
    else:  # EVIL
        # Evil: "Shadow X", "Dark X", "Crimson X", or type-based
        if rng.random() < 0.5:
            prefix = rng.choice(["Shadow", "Dark", "Crimson", "Iron"])
            suffix = rng.choice(FACTION_NAME_TYPES[5:])  # Cult, Brotherhood, etc.
            return f"{prefix} {suffix}"
        else:
            prefix = rng.choice(["Shadow", "Dark", "Crimson"])
            name = rng.choice(FACTION_NAME_SUFFIXES)
            return f"{prefix} {name}"


def generate_faction_color(alignment: FactionAlignment, seed: Optional[int] = None) -> Tuple[int, int, int]:
    """
    Generate a color for a faction based on alignment.
    
    Args:
        alignment: Faction alignment
        seed: Optional random seed
        
    Returns:
        RGB color tuple
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random
    
    color_info = ALIGNMENT_COLORS[alignment]
    
    # 70% chance to use a variation, 30% base
    if rng.random() < 0.7 and color_info["variations"]:
        return rng.choice(color_info["variations"])
    else:
        return color_info["base"]


def generate_faction_description(alignment: FactionAlignment, name: str, seed: Optional[int] = None) -> str:
    """
    Generate a description for a faction.
    
    Args:
        alignment: Faction alignment
        name: Faction name
        seed: Optional random seed
        
    Returns:
        Generated description
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random
    
    descriptions = {
        FactionAlignment.GOOD: [
            f"{name} is a noble faction that protects the realm.",
            f"{name} stands for justice and order in the land.",
            f"{name} is known for its strong defenses and fair rule.",
            f"{name} maintains peace and prosperity across its territories.",
        ],
        FactionAlignment.NEUTRAL: [
            f"{name} is an independent faction focused on trade and commerce.",
            f"{name} maintains neutrality in most conflicts.",
            f"{name} values freedom and self-determination above all.",
            f"{name} is known for its merchants and travelers.",
        ],
        FactionAlignment.EVIL: [
            f"{name} seeks to spread chaos and darkness across the land.",
            f"{name} is feared by all who know of its dark deeds.",
            f"{name} preys upon the weak and innocent.",
            f"{name} is a threat to all civilized peoples.",
        ],
    }
    
    return rng.choice(descriptions[alignment])


def generate_faction_poi_types(alignment: FactionAlignment, seed: Optional[int] = None) -> List[str]:
    """
    Generate preferred POI types for a faction based on alignment.
    
    Args:
        alignment: Faction alignment
        seed: Optional random seed
        
    Returns:
        List of POI type IDs
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random
    
    preferences = ALIGNMENT_POI_PREFERENCES[alignment]
    
    # Select POI types with weight > 1.0 (preferred)
    preferred = [poi_type for poi_type, weight in preferences.items() if weight >= 1.5]
    
    # Sometimes add a secondary type
    secondary = [poi_type for poi_type, weight in preferences.items() if 0.5 <= weight < 1.5]
    
    result = preferred.copy()
    if secondary and rng.random() < 0.4:
        result.append(rng.choice(secondary))
    
    return result


def generate_faction_party_types(alignment: FactionAlignment, seed: Optional[int] = None) -> List[str]:
    """
    Generate default party types for a faction based on alignment.
    
    Args:
        alignment: Faction alignment
        seed: Optional random seed
        
    Returns:
        List of party type IDs
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random
    
    preferences = ALIGNMENT_PARTY_PREFERENCES[alignment]
    
    # Select party types with weight >= 1.5 (core types)
    core = [party_type for party_type, weight in preferences.items() if weight >= 1.5]
    
    # Add some secondary types (weight >= 1.0)
    secondary = [party_type for party_type, weight in preferences.items() if 1.0 <= weight < 1.5]
    
    result = core.copy()
    
    # Add 1-2 secondary types
    num_secondary = rng.randint(1, min(2, len(secondary)))
    if secondary:
        selected = rng.sample(secondary, min(num_secondary, len(secondary)))
        result.extend(selected)
    
    return result


def generate_faction_relations(
    faction_id: str,
    alignment: FactionAlignment,
    all_factions: List[Faction],
    seed: Optional[int] = None,
) -> Dict[str, int]:
    """
    Generate relations for a faction with all other factions.
    
    Relations are based on alignment:
    - Good vs Evil: -80 to -100 (very hostile)
    - Good vs Good: 20 to 50 (friendly)
    - Good vs Neutral: 0 to 30 (neutral to friendly)
    - Neutral vs Neutral: -20 to 20 (varies)
    - Evil vs Evil: -20 to 20 (varies, sometimes allied)
    
    Args:
        faction_id: ID of the faction generating relations
        alignment: This faction's alignment
        all_factions: List of all other factions
        seed: Optional random seed
        
    Returns:
        Dictionary mapping faction_id -> relation value
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random
    
    relations = {}
    
    for other_faction in all_factions:
        if other_faction.id == faction_id:
            continue
        
        other_alignment = other_faction.alignment
        
        # Same faction (shouldn't happen, but handle it)
        if other_faction.id == faction_id:
            relations[other_faction.id] = 100
            continue
        
        # Good vs Evil: Very hostile
        if (alignment == FactionAlignment.GOOD and other_alignment == FactionAlignment.EVIL) or \
           (alignment == FactionAlignment.EVIL and other_alignment == FactionAlignment.GOOD):
            relations[other_faction.id] = rng.randint(-100, -70)
        
        # Good vs Good: Friendly
        elif alignment == FactionAlignment.GOOD and other_alignment == FactionAlignment.GOOD:
            relations[other_faction.id] = rng.randint(20, 50)
        
        # Good vs Neutral: Neutral to friendly
        elif (alignment == FactionAlignment.GOOD and other_alignment == FactionAlignment.NEUTRAL) or \
             (alignment == FactionAlignment.NEUTRAL and other_alignment == FactionAlignment.GOOD):
            relations[other_faction.id] = rng.randint(0, 30)
        
        # Evil vs Evil: Varies (sometimes allied, sometimes hostile)
        elif alignment == FactionAlignment.EVIL and other_alignment == FactionAlignment.EVIL:
            # 30% chance to be somewhat allied, 70% chance to be hostile
            if rng.random() < 0.3:
                relations[other_faction.id] = rng.randint(10, 30)
            else:
                relations[other_faction.id] = rng.randint(-40, -10)
        
        # Neutral vs Neutral: Varies
        elif alignment == FactionAlignment.NEUTRAL and other_alignment == FactionAlignment.NEUTRAL:
            relations[other_faction.id] = rng.randint(-20, 20)
        
        # Evil vs Neutral: Slightly hostile to neutral
        elif (alignment == FactionAlignment.EVIL and other_alignment == FactionAlignment.NEUTRAL) or \
             (alignment == FactionAlignment.NEUTRAL and other_alignment == FactionAlignment.EVIL):
            relations[other_faction.id] = rng.randint(-30, 10)
        
        # Default: neutral
        else:
            relations[other_faction.id] = 0
    
    return relations


def generate_random_factions(
    count_by_alignment: Dict[FactionAlignment, int],
    world_seed: Optional[int] = None,
    use_predefined: bool = False,
) -> List[Faction]:
    """
    Generate random factions for a playthrough.
    
    Args:
        count_by_alignment: Dict mapping alignment -> number of factions to generate
        world_seed: Optional world seed for deterministic generation
        use_predefined: If True, includes predefined factions, then adds random ones
        
    Returns:
        List of generated Faction objects (already registered)
    """
    factions = []
    
    # Create a random number generator with world seed
    if world_seed is not None:
        rng = random.Random(world_seed)
    else:
        rng = random
    
    # Track used names to avoid duplicates
    used_names = set()
    faction_counter = 0
    
    # Generate factions by alignment (sorted)
    alignments = [FactionAlignment.GOOD, FactionAlignment.NEUTRAL, FactionAlignment.EVIL]
    
    for alignment in alignments:
        count = count_by_alignment.get(alignment, 0)
        
        for i in range(count):
            faction_counter += 1
            
            # Generate unique name
            name_seed = (world_seed or rng.randint(0, 2**31)) + faction_counter * 1000
            name_rng = random.Random(name_seed)
            
            name = generate_faction_name(alignment, seed=name_seed)
            attempts = 0
            while name in used_names and attempts < 10:
                name_seed += 1
                name = generate_faction_name(alignment, seed=name_seed)
                attempts += 1
            used_names.add(name)
            
            # Generate other properties
            color_seed = name_seed + 100
            color = generate_faction_color(alignment, seed=color_seed)
            
            desc_seed = name_seed + 200
            description = generate_faction_description(alignment, name, seed=desc_seed)
            
            poi_seed = name_seed + 300
            poi_types = generate_faction_poi_types(alignment, seed=poi_seed)
            
            party_seed = name_seed + 400
            party_types = generate_faction_party_types(alignment, seed=party_seed)
            
            # Generate faction ID from name
            faction_id = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
            # Ensure unique ID
            base_id = faction_id
            id_counter = 1
            existing_ids = {f.id for f in factions}
            while faction_id in existing_ids:
                faction_id = f"{base_id}_{id_counter}"
                id_counter += 1
            
            # Create faction (relations will be set after all factions are created)
            faction = Faction(
                id=faction_id,
                name=name,
                description=description,
                alignment=alignment,
                color=color,
                default_relations={},  # Will be filled after all factions created
                home_poi_types=poi_types,
                default_party_types=party_types,
                spawn_weight=rng.uniform(0.8, 2.0),  # Random spawn weight
            )
            
            factions.append(faction)
    
    # Now generate relations between all factions
    for faction in factions:
        rel_seed = (world_seed or rng.randint(0, 2**31)) + hash(faction.id) % 10000
        relations = generate_faction_relations(
            faction.id,
            faction.alignment,
            factions,
            seed=rel_seed,
        )
        faction.default_relations = relations
    
    # Register all factions
    for faction in factions:
        register_faction(faction)
    
    return factions


def generate_factions_for_world(
    world_seed: Optional[int] = None,
    good_count: int = 2,
    neutral_count: int = 2,
    evil_count: int = 2,
    use_predefined: bool = False,
) -> List[Faction]:
    """
    Generate factions for a new world.
    
    This is the main entry point for faction generation.
    Factions are sorted by alignment (Good, Neutral, Evil).
    
    Args:
        world_seed: World seed for deterministic generation
        good_count: Number of good-aligned factions
        neutral_count: Number of neutral-aligned factions
        evil_count: Number of evil-aligned factions
        use_predefined: If True, uses predefined factions as base, then adds random ones
        
    Returns:
        List of all factions (sorted by alignment)
    """
    count_by_alignment = {
        FactionAlignment.GOOD: good_count,
        FactionAlignment.NEUTRAL: neutral_count,
        FactionAlignment.EVIL: evil_count,
    }
    
    factions = generate_random_factions(
        count_by_alignment=count_by_alignment,
        world_seed=world_seed,
        use_predefined=use_predefined,
    )
    
    # Sort by alignment (Good, Neutral, Evil)
    alignment_order = {FactionAlignment.GOOD: 0, FactionAlignment.NEUTRAL: 1, FactionAlignment.EVIL: 2}
    factions.sort(key=lambda f: alignment_order[f.alignment])
    
    return factions

