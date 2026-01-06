from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

from systems.progression import HeroStats
from systems.inventory import Inventory, get_item_def
from systems.party import (
    CompanionState,
    default_party_states_for_class,
    get_companion,
    init_companion_stats,
    recalc_companion_stats_for_level,
)

if TYPE_CHECKING:
    from engine.game import Game


def init_hero_for_class(game: "Game", hero_class_id: str) -> None:
    """
    Initialize hero for a given class.
    
    Creates HeroStats, Inventory, and Party for a fresh run.
    """
    from systems.classes import all_classes  # local import to avoid cycles

    class_def = None
    for cls in all_classes():
        if cls.id == hero_class_id:
            class_def = cls
            break
    if class_def is None:
        raise ValueError(f"Unknown hero class: {hero_class_id}")

    # Fresh hero stats
    game.hero_stats = HeroStats()
    game.hero_stats.apply_class(class_def)
    # Remember which class this hero is using for restarts / UI
    game.hero_stats.hero_class_id = class_def.id

    # Fresh inventory and starting items
    game.inventory = Inventory()
    for item_id in class_def.starting_items:
        game.inventory.add_item(item_id)

    # Auto-equip one item per slot if available
    for slot in ("weapon", "armor", "trinket"):
        for item_id in list(game.inventory.items):
            item_def = get_item_def(item_id)
            if item_def is not None and item_def.slot == slot:
                game.inventory.equip(item_id)
                break

    # Initialize party as runtime CompanionState objects.
    game.party = default_party_states_for_class(
        class_def.id,
        hero_level=game.hero_stats.level,
    )

    # Initialise each companion's stats based on its template and level.
    for comp_state in game.party:
        if not isinstance(comp_state, CompanionState):
            continue
        try:
            template = get_companion(comp_state.template_id)
        except Exception:
            continue
        init_companion_stats(comp_state, template)


def apply_hero_stats_to_player(game: "Game", full_heal: bool = False) -> None:
    """
    Sync hero meta stats (HeroStats) to the in-world Player entity.

    Applies:
    - max hp
    - attack / defense
    - crit / dodge chance
    - status resistance
    - move speed
    """
    if game.player is None or game.hero_stats is None:
        return

    hs = game.hero_stats
    base = getattr(hs, "base_stats", None)

    # ---- Max HP ----
    max_hp = getattr(hs, "max_hp", None)
    if max_hp is None and base is not None:
        max_hp = getattr(base, "max_hp", getattr(base, "hp", None))
    if max_hp is None:
        max_hp = getattr(game.player, "max_hp", 10)
    game.player.max_hp = max_hp
    if full_heal:
        game.player.hp = max_hp

    # ---- Attack / Attack Power ----
    attack_val = getattr(hs, "attack_power", None)
    if attack_val is None:
        attack_val = getattr(hs, "attack", None)
    if attack_val is None and base is not None:
        attack_val = getattr(base, "attack", getattr(base, "atk", None))
    if attack_val is None:
        attack_val = getattr(game.player, "attack", 1)

    # keep both names in sync so exploration & battle use same value
    game.player.attack = attack_val
    game.player.attack_power = attack_val

    # ---- Defense ----
    defense_val = getattr(hs, "defense", None)
    if defense_val is None and base is not None:
        defense_val = getattr(base, "defense", getattr(base, "def_", None))
    if defense_val is None:
        defense_val = getattr(game.player, "defense", 0)
    game.player.defense = defense_val

    # ---- Derived stats ----
    game.player.crit_chance = getattr(hs, "crit_chance",
                                      getattr(hs, "crit", 0.0))
    game.player.dodge_chance = getattr(hs, "dodge_chance",
                                       getattr(hs, "dodge", 0.0))
    game.player.status_resist = getattr(hs, "status_resist", 0.0)

    # --- New: resource pools from HeroStats (max stamina / mana) ---
    # HeroStats already exposes max_stamina / max_mana properties.
    max_sta = max(0, int(getattr(hs, "max_stamina", 0)))
    max_mana = max(0, int(getattr(hs, "max_mana", 0)))

    game.player.max_stamina = max_sta
    game.player.max_mana = max_mana
    # ---- Move speed ----
    move_speed = getattr(hs, "move_speed",
                         getattr(hs, "speed",
                                 getattr(game.player, "speed", 200.0)))
    game.player.speed = move_speed

    # Mirror learned perks onto the Player entity so BattleScene can
    # grant skills based on perks.
    perks_list = getattr(hs, "perks", None)
    if perks_list is not None:
        setattr(game.player, "perks", list(perks_list))


def grant_xp_to_companions(
    game: "Game",
    amount: int,
    leveled_indices: Optional[List[int]] = None,
) -> List[str]:
    """
    Grant XP to all recruited companions and recalc their stats.

    This keeps companion progression independent from the hero: they share
    XP gains, but track their own levels.

    Args:
        game: Game instance
        amount: XP amount to grant
        leveled_indices: Optional list to append indices of companions that leveled up

    Returns a list of log strings about companion level-ups.
    """
    party_list = getattr(game, "party", None) or []
    amount = int(amount)

    if amount <= 0 or not party_list:
        return []

    messages: List[str] = []

    for idx, comp_state in enumerate(party_list):
        # Only handle real CompanionState objects
        if not isinstance(comp_state, CompanionState):
            continue

        # Skip companions that aren't recruited or shouldn't scale with hero XP.
        # If the attributes don't exist yet, we treat them as True so old saves still work.
        if not getattr(comp_state, "recruited", True):
            continue
        if not getattr(comp_state, "scales_with_hero", True):
            continue

        grant = getattr(comp_state, "grant_xp", None)
        if not callable(grant):
            continue

        old_level = getattr(comp_state, "level", 1)
        old_max_hp = getattr(comp_state, "max_hp", 0)
        # CompanionState normally uses attack_power; fall back to attack if needed.
        old_attack = getattr(comp_state, "attack_power", getattr(comp_state, "attack", 0))

        try:
            levels_gained = grant(amount)
        except Exception:
            # Don't let one weird companion break rewards.
            continue

        # No actual level up? Skip.
        new_level = getattr(comp_state, "level", old_level)
        if levels_gained <= 0 or new_level <= old_level:
            continue

        # Track that this companion leveled up
        if leveled_indices is not None:
            leveled_indices.append(idx)

        # Recompute stats from template + level + perks
        template = None
        try:
            template = get_companion(comp_state.template_id)
        except Exception:
            pass
        if template is None:
            continue

        recalc_companion_stats_for_level(comp_state, template)

        # Note: Perk selection is handled after all level-ups via run_perk_selection()

        # Compose a quick summary line with stat gains
        new_max_hp = getattr(comp_state, "max_hp", old_max_hp)
        new_attack = getattr(comp_state, "attack_power", getattr(comp_state, "attack", old_attack))

        delta_hp = new_max_hp - old_max_hp
        delta_attack = new_attack - old_attack

        # Figure out a nice display name for logging
        display_name = getattr(comp_state, "name_override", None)
        if not display_name:
            display_name = getattr(comp_state, "name", None)
        if not display_name:
            # Fall back to the companion template name if available
            try:
                template_for_name = get_companion(comp_state.template_id)
            except Exception:
                template_for_name = None
            if template_for_name is not None:
                display_name = getattr(template_for_name, "name", None)
        if not display_name:
            display_name = f"Companion {idx + 1}"

        parts: List[str] = [f"{display_name} reaches level {comp_state.level}"]

        bonuses: List[str] = []
        if delta_hp > 0:
            bonuses.append(f"+{delta_hp} HP")
        if delta_attack > 0:
            bonuses.append(f"+{delta_attack} ATK")

        if bonuses:
            parts.append("(" + ", ".join(bonuses) + ")")

        messages.append(" ".join(parts))

    return messages


def gain_xp_from_event(game: "Game", amount: int) -> List[str]:
    """
    Grant XP from a map event, showing messages + perk selection scene.
    
    Returns:
        List of message strings (for compatibility with events.py)
    """
    if amount <= 0:
        return []

    old_level = game.hero_stats.level
    messages = game.hero_stats.grant_xp(amount)
    for msg in messages:
        game.add_message(msg)

    new_level = game.hero_stats.level
    hero_leveled_up = new_level > old_level
    
    # Track perk selection entries
    perk_entries: List[tuple[str, Optional[int]]] = []
    if hero_leveled_up:
        perk_entries.append(("hero", None))

    # Companions share the same XP amount, but track their own levels
    # Track which companions leveled up
    leveled_companions: List[int] = []
    companion_msgs = grant_xp_to_companions(game, amount, leveled_companions)
    for msg in companion_msgs:
        game.add_message(msg)
    
    # Add leveled companions to perk entries
    for idx in leveled_companions:
        perk_entries.append(("companion", idx))

    # On level-up from an event, full-heal the hero immediately.
    if hero_leveled_up and game.player is not None:
        apply_hero_stats_to_player(game, full_heal=False)
        game.player.hp = game.hero_stats.max_hp
        game.add_message("You feel completely renewed!")

    # If anyone leveled up, trigger perk selection scene
    if perk_entries:
        game.run_perk_selection(perk_entries)

    # Return messages for compatibility with events.py
    return messages

