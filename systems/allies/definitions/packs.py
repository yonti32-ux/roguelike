"""
Ally pack templates.

Defines groups of allies that can join together in battle, providing
tactical variety and synergy bonuses.
"""

from ..types import AllyPackTemplate
from ..registry import register_pack


def register_all_ally_packs() -> None:
    """Register all ally pack templates."""
    
    # --- Guard Patrols -----------------------------------------------------
    
    # Standard guard patrol: 2 guards
    register_pack(
        AllyPackTemplate(
            id="guard_patrol",
            name="Guard Patrol",
            member_arch_ids=[
                "town_guard",
                "town_guard",
            ],
            party_type_ids=["guard"],
            weight=1.5,
            synergy_bonus="Guard Formation: +10% defense when 2+ guards together",
        )
    )
    
    # Elite guard patrol: 1 knight + 1 guard
    register_pack(
        AllyPackTemplate(
            id="elite_guard_patrol",
            name="Elite Guard Patrol",
            member_arch_ids=[
                "knight",
                "town_guard",
            ],
            party_type_ids=["knight", "guard"],
            weight=0.8,
            synergy_bonus="Elite Formation: Knight provides +15% attack to nearby guards",
        )
    )
    
    # --- Ranger Teams -------------------------------------------------------
    
    # Ranger team: 2 rangers
    register_pack(
        AllyPackTemplate(
            id="ranger_team",
            name="Ranger Team",
            member_arch_ids=[
                "ranger",
                "ranger",
            ],
            party_type_ids=["ranger"],
            weight=1.2,
            synergy_bonus="Ranger Coordination: +15% attack when flanking together",
        )
    )
    
    # Scout team: 2 scouts
    register_pack(
        AllyPackTemplate(
            id="scout_team",
            name="Scout Team",
            member_arch_ids=[
                "scout",
                "scout",
            ],
            party_type_ids=["scout"],
            weight=1.0,
            synergy_bonus="Scout Network: +1 movement points when together",
        )
    )
    
    # --- Merchant Caravans -------------------------------------------------
    
    # Merchant caravan: 2 merchant guards
    register_pack(
        AllyPackTemplate(
            id="merchant_caravan",
            name="Merchant Caravan",
            member_arch_ids=[
                "merchant_guard",
                "merchant_guard",
            ],
            party_type_ids=["merchant", "trader"],
            weight=1.3,
            synergy_bonus="Caravan Defense: +10% HP when protecting merchants",
        )
    )
    
    # --- Military Units -----------------------------------------------------
    
    # Mercenary company: 2 mercenaries
    register_pack(
        AllyPackTemplate(
            id="mercenary_company",
            name="Mercenary Company",
            member_arch_ids=[
                "mercenary",
                "mercenary",
            ],
            party_type_ids=["mercenary"],
            weight=1.0,
            synergy_bonus="Professional Teamwork: +10% attack and +5% defense",
        )
    )
    
    # Adventuring party: 2 adventurers
    register_pack(
        AllyPackTemplate(
            id="adventuring_party",
            name="Adventuring Party",
            member_arch_ids=[
                "adventurer",
                "adventurer",
            ],
            party_type_ids=["adventurer"],
            weight=0.7,
            synergy_bonus="Adventurer Synergy: +15% skill power and +1 initiative",
        )
    )
    
    # --- Mixed Formations ---------------------------------------------------
    
    # Guard + Ranger: Combined patrol
    register_pack(
        AllyPackTemplate(
            id="combined_patrol",
            name="Combined Patrol",
            member_arch_ids=[
                "town_guard",
                "ranger",
            ],
            party_type_ids=["guard", "ranger"],
            weight=0.5,
            synergy_bonus="Combined Tactics: Guard protects, Ranger flanks",
        )
    )
    
    # Knight + Mercenary: Elite fighting force
    register_pack(
        AllyPackTemplate(
            id="elite_force",
            name="Elite Force",
            member_arch_ids=[
                "knight",
                "mercenary",
            ],
            party_type_ids=["knight", "mercenary"],
            weight=0.4,
            synergy_bonus="Elite Coordination: +20% attack and +10% defense",
        )
    )
