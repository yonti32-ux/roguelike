# systems/events.py

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from systems import perks as perk_system


@dataclass
class EventResult:
    text: str
    xp_gain: int = 0
    gold_gain: int = 0


class EventDef:
    """
    Represents a map event (Shrine, Lore Stone, Cache).
    Handles its interaction and outcome.
    """

    def __init__(
        self,
        event_id: str,
        name: str,
        description: str,
        handler: Callable[["Game"], EventResult],
    ) -> None:
        self.event_id = event_id
        self.name = name
        self.description = description
        self.handler = handler


# Registry
EVENTS: Dict[str, EventDef] = {}


def register(event: EventDef) -> None:
    EVENTS[event.event_id] = event


def get_event_def(event_id: str) -> Optional[EventDef]:
    return EVENTS.get(event_id)


# -------------------------------------------------------------
# Event handlers
# -------------------------------------------------------------

def shrine_of_power_handler(game) -> EventResult:
    """
    Shrine: random buff – XP, gold, or a perk.
    """
    roll = random.random()
    # ~40% XP, ~40% gold, ~20% perk
    if roll < 0.4:
        xp = random.randint(20, 50)
        msg_list = game.gain_xp_from_event(xp)
        text = "You kneel and feel energy surge through you."
        if msg_list:
            text += " " + " ".join(msg_list)
        return EventResult(text=text, xp_gain=xp)

    if roll < 0.8:
        gold = random.randint(25, 80)
        gained = game.hero_stats.add_gold(gold)
        text = f"The shrine radiates golden light. You gain {gained} gold."
        return EventResult(text=text, gold_gain=gained)

    # Perk: pick 1 perk and auto-apply, similar to level-up
    choices = perk_system.pick_perk_choices(game.hero_stats, max_choices=1)
    if choices:
        chosen = choices[0]
        chosen.apply(game.hero_stats)

        # Register as learned (same pattern as in perk choice handler)
        if not hasattr(game.hero_stats, "perks"):
            game.hero_stats.perks = []
        if chosen.id not in game.hero_stats.perks:
            game.hero_stats.perks.append(chosen.id)

        text = f"The shrine imparts a fragment of knowledge. You learn {chosen.name}."
        return EventResult(text=text)

    return EventResult(text="The shrine is silent.")


def lore_stone_handler(game) -> EventResult:
    """
    Lore Stone: flavor text + small XP.
    """
    lore_lines = [
        "“In the Age of Ash, even light had a cost.”",
        "Ancient etchings hint at a kingdom swallowed by its own greed.",
        "You glimpse your reflection — older, crowned, and broken.",
    ]
    msg = random.choice(lore_lines)
    xp = random.randint(10, 20)
    game.gain_xp_from_event(xp)
    return EventResult(text=msg, xp_gain=xp)


def risky_cache_handler(game) -> EventResult:
    """
    Risky Cache: gold vs small trap damage.
    """
    if random.random() < 0.65:
        gold = random.randint(30, 90)
        gained = game.hero_stats.add_gold(gold)
        text = f"You open the cache and find {gained} gold!"
        return EventResult(text=text, gold_gain=gained)

    dmg = random.randint(5, 15)
    if game.player is not None:
        game.player.hp = max(0, game.player.hp - dmg)
    text = f"A gas trap! You cough violently and lose {dmg} HP."
    return EventResult(text=text)


def sanctuary_font_handler(game) -> EventResult:
    """
    Sanctuary Font: restores HP to the party and sometimes cures debuffs.
    Intended to appear more often in 'sanctum' rooms.
    """
    heal_amount = random.randint(15, 30)

    # Heal hero
    if game.player is not None:
        # Player stores current and max HP on the hero stats
        if hasattr(game.hero_stats, "max_hp"):
            max_hp = getattr(game.hero_stats, "max_hp")
            new_hp = min(max_hp, game.player.hp + heal_amount)
            delta = new_hp - game.player.hp
            game.player.hp = new_hp
        else:
            # Fallback if max_hp is not tracked here
            delta = heal_amount
            game.player.hp += heal_amount
    else:
        delta = 0

    # Light XP bonus
    xp = random.randint(10, 20)
    game.gain_xp_from_event(xp)

    text = "A soothing light washes over you. "
    if delta > 0:
        text += f"You recover {delta} HP. "
    text += "You feel renewed and ready to press on."

    return EventResult(text=text, xp_gain=xp)


def cursed_tomb_handler(game) -> EventResult:
    """
    Cursed Tomb: graveyard-style high risk / high reward interaction.
    """
    roll = random.random()

    # 40%: good loot
    if roll < 0.4:
        gold = random.randint(40, 120)
        gained = game.hero_stats.add_gold(gold)
        text = f"You pry open the tomb and uncover {gained} gold."
        return EventResult(text=text, gold_gain=gained)

    # 40%: XP + small damage
    if roll < 0.8:
        dmg = random.randint(5, 15)
        if game.player is not None:
            game.player.hp = max(0, game.player.hp - dmg)
        xp = random.randint(15, 35)
        game.gain_xp_from_event(xp)
        text = (
            f"A vengeful spirit lashes out, dealing {dmg} damage, "
            f"but you resist and gain insight ({xp} XP)."
        )
        return EventResult(text=text, xp_gain=xp)

    # 20%: mostly bad
    dmg = random.randint(10, 25)
    if game.player is not None:
        game.player.hp = max(0, game.player.hp - dmg)
    text = "The tomb erupts with cursed energy, searing your flesh."
    return EventResult(text=text)


# -------------------------------------------------------------
# Register events
# -------------------------------------------------------------

register(
    EventDef(
        "shrine_of_power",
        "Shrine of Power",
        "An ancient altar hums with dormant energy.",
        shrine_of_power_handler,
    )
)

register(
    EventDef(
        "sanctuary_font",
        "Sanctuary Font",
        "A radiant pool of light shimmers quietly here.",
        sanctuary_font_handler,
    )
)

register(
    EventDef(
        "cursed_tomb",
        "Cursed Tomb",
        "An ominous stone sarcophagus radiates cold dread.",
        cursed_tomb_handler,
    )
)

register(
    EventDef(
        "lore_stone",
        "Lore Stone",
        "A monolith carved with glowing runes.",
        lore_stone_handler,
    )
)

register(
    EventDef(
        "risky_cache",
        "Ancient Cache",
        "A sealed cache marked with warning sigils.",
        risky_cache_handler,
    )
)
