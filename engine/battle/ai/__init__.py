"""
Battle AI system.

Modular AI system for enemy decision-making in battle.
Organized into separate modules for maintainability and extensibility.
"""

from .core import BattleAI
from .profiles import AIProfile, get_ai_profile_handler
from .threat import ThreatAssessment, calculate_threat_value
from .skill_priority import SkillPrioritizer, evaluate_skill_value
from .coordination import CoordinationManager, should_focus_fire
from .positioning import PositioningHelper, find_optimal_position

# Import profile implementations to register them
# This must be done after the profile system is set up
from .profiles import *  # noqa: F401, F403

__all__ = [
    # Core
    "BattleAI",
    # Profiles
    "AIProfile",
    "get_ai_profile_handler",
    # Threat
    "ThreatAssessment",
    "calculate_threat_value",
    # Skills
    "SkillPrioritizer",
    "evaluate_skill_value",
    # Coordination
    "CoordinationManager",
    "should_focus_fire",
    # Positioning
    "PositioningHelper",
    "find_optimal_position",
]
