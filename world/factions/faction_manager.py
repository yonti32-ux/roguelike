"""
Faction manager.

Manages all factions, their relations, and faction-based queries.
"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from world.overworld.party import RoamingParty
    from world.poi.base import PointOfInterest
    from systems.factions import Faction


class FactionManager:
    """
    Manages all factions, relations, and faction-based logic.
    
    Tracks:
    - Faction definitions
    - Global faction relations
    - Faction-controlled POIs
    - Faction-aligned parties
    """
    
    def __init__(
        self,
        world_seed: Optional[int] = None,
        use_random_factions: bool = True,
        faction_counts: Optional[Dict["FactionAlignment", int]] = None,
    ):
        """
        Initialize faction manager.
        
        Args:
            world_seed: Optional world seed for random faction generation
            use_random_factions: If True, generates random factions. If False, uses predefined.
            faction_counts: Optional dict mapping alignment -> count (overrides defaults)
        """
        self.factions: Dict[str, "Faction"] = {}
        
        if use_random_factions:
            # Generate random factions for this world
            from .faction_generator import generate_factions_for_world
            from systems.factions import FactionAlignment
            
            # Use provided counts or defaults
            if faction_counts is None:
                faction_counts = {
                    FactionAlignment.GOOD: 2,
                    FactionAlignment.NEUTRAL: 2,
                    FactionAlignment.EVIL: 2,
                }
            
            # Generate factions with specified counts
            generated = generate_factions_for_world(
                world_seed=world_seed,
                good_count=faction_counts.get(FactionAlignment.GOOD, 2),
                neutral_count=faction_counts.get(FactionAlignment.NEUTRAL, 2),
                evil_count=faction_counts.get(FactionAlignment.EVIL, 2),
                use_predefined=False,
            )
            
            for faction in generated:
                self.factions[faction.id] = faction
        else:
            # Use predefined factions
            from systems.factions import all_factions
            for faction in all_factions():
                self.factions[faction.id] = faction
        
        # Global relations: (faction1_id, faction2_id) -> relation value
        # This allows for dynamic relations that can change during gameplay
        self.global_relations: Dict[Tuple[str, str], int] = {}
        
        # Initialize relations from faction defaults
        self._initialize_relations()
    
    def _initialize_relations(self) -> None:
        """Initialize relations from faction default_relations."""
        for faction in self.factions.values():
            for other_faction_id, relation_value in faction.default_relations.items():
                self.set_relation(faction.id, other_faction_id, relation_value)
    
    def get_faction(self, faction_id: str) -> Optional["Faction"]:
        """Get a faction by ID."""
        return self.factions.get(faction_id)
    
    def get_factions_by_alignment(self) -> Dict["FactionAlignment", List["Faction"]]:
        """
        Get all factions grouped by alignment.
        
        Returns:
            Dictionary mapping alignment -> list of factions (sorted by name)
        """
        from systems.factions import FactionAlignment
        
        result: Dict["FactionAlignment", List["Faction"]] = {
            FactionAlignment.GOOD: [],
            FactionAlignment.NEUTRAL: [],
            FactionAlignment.EVIL: [],
        }
        
        for faction in self.factions.values():
            result[faction.alignment].append(faction)
        
        # Sort each list by name
        for alignment in result:
            result[alignment].sort(key=lambda f: f.name)
        
        return result
    
    def get_all_factions_sorted(self) -> List["Faction"]:
        """
        Get all factions sorted by alignment (Good, Neutral, Evil), then by name.
        
        Returns:
            List of all factions, sorted
        """
        from systems.factions import FactionAlignment
        
        alignment_order = {
            FactionAlignment.GOOD: 0,
            FactionAlignment.NEUTRAL: 1,
            FactionAlignment.EVIL: 2,
        }
        
        factions = list(self.factions.values())
        factions.sort(key=lambda f: (alignment_order[f.alignment], f.name))
        
        return factions
    
    def get_relation(self, faction1_id: str, faction2_id: str) -> int:
        """
        Get the relation between two factions.
        
        Args:
            faction1_id: First faction ID
            faction2_id: Second faction ID
            
        Returns:
            Relation value (-100 to 100)
            -100 = hostile, 0 = neutral, 100 = allied
        """
        # Same faction is always allied
        if faction1_id == faction2_id:
            return 100
        
        # Check global relations (bidirectional)
        key1 = (faction1_id, faction2_id)
        key2 = (faction2_id, faction1_id)
        
        if key1 in self.global_relations:
            return self.global_relations[key1]
        if key2 in self.global_relations:
            return self.global_relations[key2]
        
        # Check faction defaults
        faction1 = self.get_faction(faction1_id)
        if faction1:
            return faction1.default_relations.get(faction2_id, 0)
        
        # Default: neutral
        return 0
    
    def set_relation(self, faction1_id: str, faction2_id: str, value: int) -> None:
        """
        Set the relation between two factions.
        
        Args:
            faction1_id: First faction ID
            faction2_id: Second faction ID
            value: Relation value (-100 to 100)
        """
        # Clamp value
        value = max(-100, min(100, value))
        
        # Store bidirectionally
        key = (faction1_id, faction2_id)
        self.global_relations[key] = value
    
    def modify_relation(self, faction1_id: str, faction2_id: str, delta: int) -> None:
        """
        Modify the relation between two factions by a delta.
        
        Args:
            faction1_id: First faction ID
            faction2_id: Second faction ID
            delta: Change in relation (-100 to 100)
        """
        current = self.get_relation(faction1_id, faction2_id)
        new_value = current + delta
        self.set_relation(faction1_id, faction2_id, new_value)
    
    def are_allies(self, faction1_id: str, faction2_id: str, threshold: int = 50) -> bool:
        """Check if two factions are allies (relation >= threshold)."""
        return self.get_relation(faction1_id, faction2_id) >= threshold
    
    def are_enemies(self, faction1_id: str, faction2_id: str, threshold: int = -50) -> bool:
        """Check if two factions are enemies (relation <= threshold)."""
        return self.get_relation(faction1_id, faction2_id) <= threshold
    
    def get_parties_for_faction(
        self,
        faction_id: str,
        all_parties: List["RoamingParty"],
    ) -> List["RoamingParty"]:
        """Get all parties belonging to a faction."""
        return [p for p in all_parties if getattr(p, "faction_id", None) == faction_id]
    
    def get_pois_for_faction(
        self,
        faction_id: str,
        all_pois: List["PointOfInterest"],
    ) -> List["PointOfInterest"]:
        """Get all POIs controlled by a faction."""
        return [poi for poi in all_pois if getattr(poi, "faction_id", None) == faction_id]
    
    def get_faction_for_poi_type(self, poi_type: str) -> Optional[str]:
        """
        Get the default faction for a POI type.
        
        Returns the faction with the highest spawn_weight that has this POI type
        in their home_poi_types.
        """
        best_faction = None
        best_weight = 0.0
        
        for faction in self.factions.values():
            if poi_type in faction.home_poi_types:
                if faction.spawn_weight > best_weight:
                    best_weight = faction.spawn_weight
                    best_faction = faction.id
        
        return best_faction
    
    def get_faction_for_party_type(self, party_type_id: str) -> Optional[str]:
        """
        Get the default faction for a party type.
        
        Returns the faction with the highest spawn_weight that has this party type
        in their default_party_types.
        """
        best_faction = None
        best_weight = 0.0
        
        for faction in self.factions.values():
            if party_type_id in faction.default_party_types:
                if faction.spawn_weight > best_weight:
                    best_weight = faction.spawn_weight
                    best_faction = faction.id
        
        return best_faction
    
    def get_all_factions(self) -> List["Faction"]:
        """Get all registered factions."""
        return list(self.factions.values())

