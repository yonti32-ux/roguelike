"""
Simple NPC stubs used in camps.

These mirror the idea of village NPCs but stay lightweight: mostly used
as hooks for interactions like resting, trading, or giving rumors.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class CampNPC:
    """Base camp NPC."""

    npc_type: Literal["merchant", "guard", "traveler"]
    name: str | None = None


@dataclass
class CampMerchantNPC(CampNPC):
    """Merchant who can open a simple camp shop."""

    npc_type: Literal["merchant"] = "merchant"


@dataclass
class CampGuardNPC(CampNPC):
    """Guard or lookout NPC, mostly flavor for now."""

    npc_type: Literal["guard"] = "guard"


@dataclass
class CampTravelerNPC(CampNPC):
    """Traveler / storyteller NPC, potential hook for rumors and quests."""

    npc_type: Literal["traveler"] = "traveler"



