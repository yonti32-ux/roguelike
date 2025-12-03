# systems/statuses.py

from dataclasses import dataclass
from typing import List


@dataclass
class StatusEffect:
    """
    Generic status effect that can be used in battle (and later in exploration).

    duration:
        Number of *turns of the affected unit* remaining.
    stacks:
        For effects that can stack (bleed, poison, etc.).
    flat_damage_each_turn:
        Damage applied at the start of the unit's turn (before duration drops).
    """
    name: str
    duration: int
    stacks: int = 1
    outgoing_mult: float = 1.0
    incoming_mult: float = 1.0
    flat_damage_each_turn: int = 0   # poisons, burns
    stunned: bool = False


def tick_statuses(statuses: List[StatusEffect]) -> int:
    """
    Advance all statuses by one 'turn' for the affected unit.

    - Applies any flat damage (DOT) based on stacks.
    - Decrements duration.
    - Removes expired statuses.
    - Returns the total DOT damage to apply to the unit's HP.
    """
    total_dot = 0
    remaining: List[StatusEffect] = []

    for s in statuses:
        if s.flat_damage_each_turn:
            total_dot += s.flat_damage_each_turn * max(1, s.stacks)

        s.duration -= 1
        if s.duration > 0:
            remaining.append(s)

    statuses[:] = remaining
    return total_dot


def has_status(statuses: List[StatusEffect], name: str) -> bool:
    return any(s.name == name for s in statuses)


def is_stunned(statuses: List[StatusEffect]) -> bool:
    return any(s.stunned for s in statuses)


def outgoing_multiplier(statuses: List[StatusEffect]) -> float:
    mult = 1.0
    for s in statuses:
        mult *= s.outgoing_mult
    return mult


def incoming_multiplier(statuses: List[StatusEffect]) -> float:
    mult = 1.0
    for s in statuses:
        mult *= s.incoming_mult
    return mult
