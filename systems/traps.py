# systems/traps.py

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from systems import statuses


@dataclass
class TrapResult:
    """Result of triggering a trap."""
    text: str
    damage: int = 0
    status_effect: Optional[statuses.StatusEffect] = None
    gold_lost: int = 0  # Some traps might cause you to drop gold


class TrapDef:
    """
    Represents a trap type with its trigger behavior and effects.
    """
    
    def __init__(
        self,
        trap_id: str,
        name: str,
        description: str,
        handler: Callable[["Game"], TrapResult],
        detection_difficulty: float = 0.5,  # 0.0 = always visible, 1.0 = very hard to detect
        disarm_difficulty: float = 0.6,  # 0.0 = easy, 1.0 = very hard
    ) -> None:
        self.trap_id = trap_id
        self.name = name
        self.description = description
        self.handler = handler
        self.detection_difficulty = detection_difficulty
        self.disarm_difficulty = disarm_difficulty


# Registry
TRAPS: Dict[str, TrapDef] = {}


def register(trap: TrapDef) -> None:
    TRAPS[trap.trap_id] = trap


def get_trap_def(trap_id: str) -> Optional[TrapDef]:
    return TRAPS.get(trap_id)


# -------------------------------------------------------------
# Trap handlers
# -------------------------------------------------------------

def spike_trap_handler(game) -> TrapResult:
    """
    Spike Trap: Physical damage trap.
    Common, moderate damage.
    """
    floor = getattr(game, "floor", 1)
    # Damage scales with floor: 8-15 base, +2 per floor
    base_damage = random.randint(8, 15)
    damage = base_damage + (floor - 1) * 2
    
    if game.player is not None:
        game.player.hp = max(0, game.player.hp - damage)
    
    return TrapResult(
        text=f"Sharp spikes spring from the floor! You take {damage} damage.",
        damage=damage,
    )


def poison_trap_handler(game) -> TrapResult:
    """
    Poison Trap: Damage + poison status effect.
    Less immediate damage but applies DOT.
    """
    floor = getattr(game, "floor", 1)
    base_damage = random.randint(5, 10)
    damage = base_damage + (floor - 1) * 1
    
    if game.player is not None:
        game.player.hp = max(0, game.player.hp - damage)
    
    # Apply poison status (3-5 turns, 2-4 damage per turn)
    poison_duration = random.randint(3, 5)
    poison_damage = random.randint(2, 4)
    
    poison_status = statuses.StatusEffect(
        name="Poisoned",
        duration=poison_duration,
        stacks=1,
        flat_damage_each_turn=poison_damage,
    )
    
    # Add status to player if they have a status list
    if hasattr(game.player, "statuses"):
        game.player.statuses.append(poison_status)
    elif hasattr(game, "player_statuses"):
        if not hasattr(game, "player_statuses"):
            game.player_statuses = []
        game.player_statuses.append(poison_status)
    
    return TrapResult(
        text=f"A cloud of toxic gas erupts! You take {damage} damage and are poisoned.",
        damage=damage,
        status_effect=poison_status,
    )


def fire_trap_handler(game) -> TrapResult:
    """
    Fire Trap: High immediate damage.
    More dangerous but easier to spot.
    """
    floor = getattr(game, "floor", 1)
    base_damage = random.randint(12, 20)
    damage = base_damage + (floor - 1) * 3
    
    if game.player is not None:
        game.player.hp = max(0, game.player.hp - damage)
    
    # Small chance to apply burn status
    if random.random() < 0.3:
        burn_status = statuses.StatusEffect(
            name="Burning",
            duration=random.randint(2, 4),
            stacks=1,
            flat_damage_each_turn=random.randint(1, 3),
        )
        
        if hasattr(game.player, "statuses"):
            game.player.statuses.append(burn_status)
        elif hasattr(game, "player_statuses"):
            if not hasattr(game, "player_statuses"):
                game.player_statuses = []
            game.player_statuses.append(burn_status)
        
        return TrapResult(
            text=f"Flames burst from the floor! You take {damage} damage and catch fire!",
            damage=damage,
            status_effect=burn_status,
        )
    
    return TrapResult(
        text=f"Flames burst from the floor! You take {damage} damage.",
        damage=damage,
    )


def weakness_trap_handler(game) -> TrapResult:
    """
    Weakness Trap: No damage, but applies debuff.
    Reduces attack power temporarily.
    """
    # Apply weakness status (reduces outgoing damage)
    weakness_duration = random.randint(4, 6)
    weakness_status = statuses.StatusEffect(
        name="Weakened",
        duration=weakness_duration,
        stacks=1,
        outgoing_mult=0.7,  # 30% damage reduction
    )
    
    if hasattr(game.player, "statuses"):
        game.player.statuses.append(weakness_status)
    elif hasattr(game, "player_statuses"):
        if not hasattr(game, "player_statuses"):
            game.player_statuses = []
        game.player_statuses.append(weakness_status)
    
    return TrapResult(
        text="A cursed mist saps your strength. You feel weakened.",
        status_effect=weakness_status,
    )


def teleport_trap_handler(game) -> TrapResult:
    """
    Teleport Trap: No damage, but teleports player.
    Can be disorienting but also useful for escaping.
    """
    if game.current_map is None or game.player is None:
        return TrapResult(text="The trap fizzles harmlessly.")
    
    # Find a random walkable tile on the current floor
    walkable_tiles = []
    for ty in range(game.current_map.height):
        for tx in range(game.current_map.width):
            if game.current_map.is_walkable_tile(tx, ty):
                # Avoid stairs
                if game.current_map.up_stairs and (tx, ty) == game.current_map.up_stairs:
                    continue
                if game.current_map.down_stairs and (tx, ty) == game.current_map.down_stairs:
                    continue
                walkable_tiles.append((tx, ty))
    
    if walkable_tiles:
        tx, ty = random.choice(walkable_tiles)
        x, y = game.current_map.center_entity_on_tile(
            tx, ty, game.player.width, game.player.height
        )
        game.player.move_to(x, y)
        return TrapResult(
            text="The floor shifts beneath you! You are teleported elsewhere on this floor.",
        )
    
    return TrapResult(text="The trap fizzles harmlessly.")


def gold_trap_handler(game) -> TrapResult:
    """
    Gold Trap: Causes player to drop some gold.
    Annoying but not deadly.
    """
    hero_stats = getattr(game, "hero_stats", None)
    if hero_stats is None:
        return TrapResult(text="The trap fails to activate.")
    
    current_gold = getattr(hero_stats, "gold", 0)
    if current_gold <= 0:
        return TrapResult(text="A trap triggers, but you have no gold to lose.")
    
    # Lose 10-25% of current gold, minimum 5, maximum 50
    loss_percent = random.uniform(0.10, 0.25)
    gold_lost = max(5, min(50, int(current_gold * loss_percent)))
    
    hero_stats.gold = max(0, current_gold - gold_lost)
    
    return TrapResult(
        text=f"The trap causes you to drop {gold_lost} gold!",
        gold_lost=gold_lost,
    )


# -------------------------------------------------------------
# Register traps
# -------------------------------------------------------------

register(
    TrapDef(
        "spike_trap",
        "Spike Trap",
        "A pressure plate triggers sharp spikes from the floor.",
        spike_trap_handler,
        detection_difficulty=0.4,  # Moderately easy to spot
        disarm_difficulty=0.5,
    )
)

register(
    TrapDef(
        "poison_trap",
        "Poison Trap",
        "A hidden mechanism releases toxic gas.",
        poison_trap_handler,
        detection_difficulty=0.6,  # Harder to spot
        disarm_difficulty=0.7,
    )
)

register(
    TrapDef(
        "fire_trap",
        "Fire Trap",
        "Flammable material ignites when triggered.",
        fire_trap_handler,
        detection_difficulty=0.3,  # Easier to spot (smoke, heat)
        disarm_difficulty=0.6,
    )
)

register(
    TrapDef(
        "weakness_trap",
        "Weakness Trap",
        "A cursed mist weakens those who pass through.",
        weakness_trap_handler,
        detection_difficulty=0.5,
        disarm_difficulty=0.4,  # Easier to disarm (no physical mechanism)
    )
)

register(
    TrapDef(
        "teleport_trap",
        "Teleport Trap",
        "An ancient rune teleports intruders.",
        teleport_trap_handler,
        detection_difficulty=0.7,  # Hard to spot (magical)
        disarm_difficulty=0.8,  # Hard to disarm
    )
)

register(
    TrapDef(
        "gold_trap",
        "Gold Trap",
        "A mechanism that causes you to drop gold.",
        gold_trap_handler,
        detection_difficulty=0.5,
        disarm_difficulty=0.5,
    )
)

