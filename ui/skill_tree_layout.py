"""
Skill tree layout system for visual skill tree rendering.

Organizes skills into a tree structure based on branches and prerequisites.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

from systems import perks as perk_system
from systems.skills import get as get_skill, Skill


@dataclass
class SkillNode:
    """Represents a skill node in the tree."""
    skill_id: str
    skill: Skill
    branch: str  # Which branch this skill belongs to
    tier: int  # Depth in the tree (0 = starting skills, higher = deeper)
    prerequisites: List[str]  # Skill IDs that must be unlocked first
    x: float = 0.0  # Layout position X
    y: float = 0.0  # Layout position Y
    rank: int = 0  # Current rank (set externally)


@dataclass
class SkillTreeLayout:
    """Complete skill tree layout with nodes and connections."""
    nodes: Dict[str, SkillNode]  # skill_id -> node
    branches: Dict[str, List[str]]  # branch -> list of skill_ids
    connections: List[Tuple[str, str]]  # (from_skill_id, to_skill_id) prerequisites


# Branch colors for visual distinction
BRANCH_COLORS = {
    "vitality": (200, 100, 100),  # Red
    "blade": (150, 150, 200),  # Blue
    "ward": (150, 200, 150),  # Green
    "focus": (200, 150, 200),  # Purple
    "mobility": (200, 200, 150),  # Yellow
    "general": (180, 180, 180),  # Gray
}


def get_skill_branch(skill_id: str) -> str:
    """
    Determine which branch a skill belongs to by finding the perk that grants it.
    Returns "general" if no specific branch found.
    
    Also checks starting skills from classes to assign them to appropriate branches.
    """
    # Check perks that grant this skill
    for perk in perk_system.all_perks():
        if skill_id in getattr(perk, "grant_skills", []):
            return perk.branch
    
    # Check if it's a starting skill and assign to a branch based on skill type
    # Universal skills go to "general"
    universal_skills = ["guard", "power_strike"]
    if skill_id in universal_skills:
        return "general"
    
    # Try to infer branch from skill name/type
    skill_id_lower = skill_id.lower()
    if any(word in skill_id_lower for word in ["strike", "cleave", "charge", "lunge", "backstab"]):
        return "blade"
    elif any(word in skill_id_lower for word in ["shield", "taunt", "wall", "guard"]):
        return "ward"
    elif any(word in skill_id_lower for word in ["fire", "lightning", "arcane", "magic", "slow", "focus"]):
        return "focus"
    elif any(word in skill_id_lower for word in ["step", "evade", "shadow", "nimble", "poison"]):
        return "mobility"
    elif any(word in skill_id_lower for word in ["wind", "second", "endurance"]):
        return "vitality"
    
    return "general"


def get_skill_prerequisites(skill_id: str) -> List[str]:
    """
    Get prerequisite skills for a skill.
    Currently, skills are unlocked by perks, so we check perk prerequisites.
    """
    prerequisites: List[str] = []
    
    # Find the perk that grants this skill
    for perk in perk_system.all_perks():
        if skill_id in getattr(perk, "grant_skills", []):
            # Check if prerequisite perks grant skills
            for req_perk_id in perk.requires:
                try:
                    req_perk = perk_system.get(req_perk_id)
                    prerequisites.extend(getattr(req_perk, "grant_skills", []))
                except KeyError:
                    pass
            break
    
    return prerequisites


def calculate_skill_tier(skill_id: str, all_skills: Set[str], visited: Optional[Set[str]] = None) -> int:
    """
    Calculate the tier/depth of a skill in the tree.
    Starting skills are tier 0, skills unlocked by tier 0 perks are tier 1, etc.
    """
    if visited is None:
        visited = set()
    
    if skill_id in visited:
        return 0  # Cycle detection
    
    visited.add(skill_id)
    
    prerequisites = get_skill_prerequisites(skill_id)
    
    if not prerequisites:
        # No prerequisites = starting skill or tier 0
        return 0
    
    # Tier is max prerequisite tier + 1
    max_prereq_tier = 0
    for prereq_id in prerequisites:
        if prereq_id in all_skills:
            prereq_tier = calculate_skill_tier(prereq_id, all_skills, visited.copy())
            max_prereq_tier = max(max_prereq_tier, prereq_tier)
    
    return max_prereq_tier + 1


def build_skill_tree(unlocked_skill_ids: List[str]) -> SkillTreeLayout:
    """
    Build a skill tree layout from a list of unlocked skill IDs.
    
    Args:
        unlocked_skill_ids: List of skill IDs that are unlocked
        
    Returns:
        SkillTreeLayout with nodes organized by branch and tier
    """
    nodes: Dict[str, SkillNode] = {}
    branches: Dict[str, List[str]] = defaultdict(list)
    connections: List[Tuple[str, str]] = []
    
    skill_set = set(unlocked_skill_ids)
    
    # Create nodes for all unlocked skills
    for skill_id in unlocked_skill_ids:
        try:
            skill = get_skill(skill_id)
            branch = get_skill_branch(skill_id)
            tier = calculate_skill_tier(skill_id, skill_set)
            prerequisites = get_skill_prerequisites(skill_id)
            
            node = SkillNode(
                skill_id=skill_id,
                skill=skill,
                branch=branch,
                tier=tier,
                prerequisites=prerequisites,
            )
            
            nodes[skill_id] = node
            branches[branch].append(skill_id)
            
            # Add connections for prerequisites
            for prereq_id in prerequisites:
                if prereq_id in skill_set:
                    connections.append((prereq_id, skill_id))
        except KeyError:
            continue
    
    return SkillTreeLayout(
        nodes=nodes,
        branches=dict(branches),
        connections=connections,
    )


def layout_tree(tree: SkillTreeLayout, node_size: float = 100.0, branch_spacing: float = 300.0, tier_spacing: float = 150.0) -> None:
    """
    Calculate X/Y positions for all nodes in the tree.
    
    Layout strategy:
    - Branches are arranged horizontally (columns)
    - Skills within a branch are arranged vertically by tier
    - Starting skills (tier 0) are at the top
    - Higher tiers go downward
    
    Args:
        tree: SkillTreeLayout to position
        node_size: Size of each node (for spacing)
        branch_spacing: Horizontal spacing between branches
        tier_spacing: Vertical spacing between tiers
    """
    branch_order = ["vitality", "blade", "ward", "focus", "mobility", "general"]
    
    # Group nodes by branch and tier
    branch_tiers: Dict[str, Dict[int, List[str]]] = defaultdict(lambda: defaultdict(list))
    
    for skill_id, node in tree.nodes.items():
        branch_tiers[node.branch][node.tier].append(skill_id)
    
    # Position nodes
    branch_x = 0.0
    for branch_name in branch_order:
        if branch_name not in branch_tiers:
            continue
        
        tiers = branch_tiers[branch_name]
        max_tier = max(tiers.keys()) if tiers else 0
        
        # Center branch vertically
        branch_start_y = -(max_tier * tier_spacing) / 2
        
        # Position nodes in this branch
        for tier in sorted(tiers.keys()):
            skill_ids = tiers[tier]
            tier_y = branch_start_y + (tier * tier_spacing)
            
            # Center skills horizontally within tier
            skill_count = len(skill_ids)
            start_x = branch_x - (skill_count - 1) * node_size / 2
            
            for i, skill_id in enumerate(skill_ids):
                node = tree.nodes[skill_id]
                node.x = start_x + i * node_size
                node.y = tier_y
        
        branch_x += branch_spacing
    
    # Center the entire tree horizontally
    if tree.nodes:
        min_x = min(node.x for node in tree.nodes.values())
        max_x = max(node.x for node in tree.nodes.values())
        center_x = (min_x + max_x) / 2
        
        for node in tree.nodes.values():
            node.x -= center_x
