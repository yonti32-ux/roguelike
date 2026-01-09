"""
Companion generation system for village recruitment.

Generates random companions with names, classes, stats, and perks.
"""

import random
from dataclasses import dataclass
from typing import List, Optional

from systems.party import CompanionState, CompanionDef, get_companion, init_companion_stats
from systems.classes import all_classes, get_class
from systems.perks import get as get_perk, all_perks


@dataclass
class AvailableCompanion:
    """A companion available for recruitment in a village."""
    companion_state: CompanionState
    recruitment_cost: int
    generated_name: str
    backstory_snippet: str = ""  # Optional flavor text


def generate_random_companion(
    village_level: int,
    seed: Optional[int] = None,
) -> CompanionState:
    """
    Generate a random companion for recruitment.
    
    Args:
        village_level: Village level (affects companion level and quality)
        seed: Optional random seed for deterministic generation
        
    Returns:
        CompanionState instance ready for recruitment
    """
    if seed is not None:
        random.seed(seed)
    
    # Select random class
    class_id = select_random_class()
    class_def = get_class(class_id)
    
    # Calculate level (village level ±2 variance)
    base_level = village_level
    level_variance = random.randint(-2, 2)
    companion_level = max(1, min(base_level + level_variance, base_level + 2))
    
    # Generate name
    companion_name = generate_companion_name()
    
    # Create companion state
    # Use a unique template ID for generated companions
    template_id = f"generated_{class_id}"
    companion_state = CompanionState(
        template_id=template_id,
        name_override=companion_name,
        level=companion_level,
        xp=0,
        class_id=class_id,
    )
    
    # Create a template for stat calculation
    # The recalc function will use class_id if available, but needs a template
    template = CompanionDef(
        id=template_id,
        name=companion_name,
        role=class_def.name,
        class_id=class_id,
        hp_factor=1.0,  # Full stats (not reduced like default companions)
        attack_factor=1.0,
        defense_factor=1.0,
        skill_power_factor=1.0,
        skill_ids=class_def.starting_skills.copy() if hasattr(class_def, "starting_skills") else [],
    )
    
    # Register the template temporarily (or just use it for initialization)
    # We don't need to register it permanently since we have the state
    
    # Initialize stats
    init_companion_stats(companion_state, template)
    
    # Assign starting perks
    assign_starting_perks(companion_state, companion_level, class_id)
    
    # Recalculate stats after perks are assigned
    # Note: We use the template we created earlier, not from registry
    from systems.party import recalc_companion_stats_for_level
    recalc_companion_stats_for_level(companion_state, template)
    
    # Initialize skill slots
    from systems.party import init_companion_skill_slots
    init_companion_skill_slots(companion_state, template)
    
    return companion_state


def calculate_recruitment_cost(companion_state: CompanionState) -> int:
    """
    Calculate the gold cost to recruit a companion.
    
    Formula:
    - Base cost = 50 * level
    - Perk bonus = 10 * num_perks
    - Total = base_cost + perk_bonus
    
    Args:
        companion_state: The companion to calculate cost for
        
    Returns:
        Recruitment cost in gold
    """
    base_cost = 50 * companion_state.level
    num_perks = len(companion_state.perks)
    perk_bonus = 10 * num_perks
    total_cost = base_cost + perk_bonus
    
    # Minimum cost
    return max(50, total_cost)


def generate_companion_name() -> str:
    """
    Generate a random name for a companion.
    
    For now, uses a simple name generator. In the future, could use
    the name generation system.
    
    Returns:
        Generated name string
    """
    # Simple name generation - first name + optional title
    first_names = [
        "Aldric", "Brenna", "Cedric", "Dara", "Ewan", "Fara", "Gareth", "Hilda",
        "Ivor", "Jenna", "Kael", "Lira", "Marcus", "Nora", "Owen", "Petra",
        "Quinn", "Rhea", "Soren", "Tara", "Ulric", "Vera", "Wynn", "Yara", "Zane"
    ]
    
    titles = [
        "the Brave", "the Swift", "the Wise", "the Strong", "the Clever",
        "the Bold", "the Steady", "the Keen", "the Stalwart", ""
    ]
    
    first_name = random.choice(first_names)
    title = random.choice(titles)
    
    if title:
        return f"{first_name} {title}"
    else:
        return first_name


def select_random_class() -> str:
    """
    Select a random class from available classes.
    
    Returns:
        Class ID string
    """
    classes = all_classes()
    if not classes:
        # Fallback to warrior if no classes available
        return "warrior"
    
    # Equal probability for each class
    class_def = random.choice(classes)
    return class_def.id


def assign_starting_perks(
    companion_state: CompanionState,
    level: int,
    class_id: str,
) -> None:
    """
    Assign random starting perks to a companion based on level and class.
    
    Args:
        companion_state: Companion to assign perks to
        level: Companion level
        class_id: Companion's class ID
    """
    # Number of perks: min(level // 3, 2) (0-2 perks)
    num_perks = min(level // 3, 2)
    
    if num_perks <= 0:
        return
    
    # Get available perks for this class
    # For now, get all perks that are available at this level
    available_perks = []
    for perk in all_perks():
        # Check if perk is unlocked at this level
        if perk.unlock_level <= level:
            # Prefer class-appropriate perks (check branch/tags)
            # For now, just get any available perk
            available_perks.append(perk)
    
    if not available_perks:
        return
    
    # Select random perks
    selected_perks = random.sample(available_perks, min(num_perks, len(available_perks)))
    
    # Add to companion
    for perk in selected_perks:
        companion_state.perks.append(perk.id)
    
    # Recalculate stats with new perks
    # For generated companions, we need to create a template locally
    # since they're not in the registry
    from systems.party import recalc_companion_stats_for_level, CompanionDef
    from systems.classes import get_class
    
    # Check if this is a generated companion (template_id starts with "generated")
    is_generated = companion_state.template_id.startswith("generated") if companion_state.template_id else False
    
    if is_generated:
        # Create template locally for recalculation
        class_def = get_class(companion_state.class_id) if companion_state.class_id else None
        template = CompanionDef(
            id=companion_state.template_id,
            name=companion_state.name_override or "Companion",
            role=class_def.name if class_def else "Adventurer",
            class_id=companion_state.class_id,
            hp_factor=1.0,
            attack_factor=1.0,
            defense_factor=1.0,
            skill_power_factor=1.0,
            skill_ids=class_def.starting_skills.copy() if class_def and hasattr(class_def, "starting_skills") else [],
        )
    else:
        # Try to get from registry
        try:
            from systems.party import get_companion
            template = get_companion(companion_state.template_id)
        except (KeyError, Exception):
            # Fallback: create minimal template
            class_def = get_class(companion_state.class_id) if companion_state.class_id else None
            template = CompanionDef(
                id=companion_state.template_id or "unknown",
                name=companion_state.name_override or "Companion",
                role=class_def.name if class_def else "Adventurer",
                class_id=companion_state.class_id,
            )
    
    recalc_companion_stats_for_level(companion_state, template)


def generate_village_companions(
    village_level: int,
    count: int,
    seed: Optional[int] = None,
) -> List[AvailableCompanion]:
    """
    Generate a list of available companions for a village.
    
    Args:
        village_level: Village level
        count: Number of companions to generate (1-3)
        seed: Optional random seed
        
    Returns:
        List of AvailableCompanion instances
    """
    if seed is not None:
        random.seed(seed)
    
    companions: List[AvailableCompanion] = []
    
    for i in range(count):
        # Use index in seed to ensure different companions
        companion_seed = (seed + i * 1000) if seed is not None else None
        companion_state = generate_random_companion(village_level, seed=companion_seed)
        cost = calculate_recruitment_cost(companion_state)
        
        # Generate backstory snippet (optional flavor)
        backstory = _generate_backstory_snippet(companion_state)
        
        available = AvailableCompanion(
            companion_state=companion_state,
            recruitment_cost=cost,
            generated_name=companion_state.name_override or "Companion",
            backstory_snippet=backstory,
        )
        companions.append(available)
    
    return companions


def _generate_backstory_snippet(companion_state: CompanionState) -> str:
    """Generate a simple backstory snippet for flavor."""
    snippets = [
        "A seasoned adventurer looking for work.",
        "Seeking fortune and glory.",
        "Lost their previous party, looking for a new one.",
        "A wanderer with a mysterious past.",
        "Looking to prove themselves in battle.",
    ]
    return random.choice(snippets)

