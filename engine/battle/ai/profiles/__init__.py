"""
AI Profile system.

Defines different AI behavior profiles and their decision-making logic.
Each profile represents a different combat style and tactical approach.
"""

from typing import List, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import BattleAI

from engine.battle.types import BattleUnit


class AIProfile(Protocol):
    """Protocol for AI profile handlers."""
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Choose a target from the available targets."""
        ...
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Execute the AI turn for this unit."""
        ...


class BaseAIProfile:
    """Base class for AI profiles with common functionality."""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
    
    def choose_target(self, unit: BattleUnit, targets: List[BattleUnit], ai: "BattleAI") -> Optional[BattleUnit]:
        """Default target selection - can be overridden by subclasses."""
        if not targets:
            return None
        # Default: nearest target
        return min(targets, key=lambda t: abs(t.gx - unit.gx) + abs(t.gy - unit.gy))
    
    def execute_turn(self, unit: BattleUnit, ai: "BattleAI", hp_ratio: float) -> None:
        """Default turn execution - delegates to specialized handlers."""
        # This will be implemented by specific profile classes
        pass


# Profile registry
_PROFILE_HANDLERS: dict[str, AIProfile] = {}


def register_profile(profile_name: str, handler: AIProfile) -> None:
    """Register an AI profile handler."""
    _PROFILE_HANDLERS[profile_name] = handler


def get_ai_profile_handler(profile_name: str) -> AIProfile:
    """Get the handler for an AI profile."""
    return _PROFILE_HANDLERS.get(profile_name, _PROFILE_HANDLERS.get("brute", _default_handler))


# Default handler (will be replaced with proper implementations)
_default_handler = BaseAIProfile("brute")

# Import profile implementations
from .brute import BruteProfile
from .skirmisher import SkirmisherProfile
from .caster import CasterProfile
from .support import SupportProfile
from .tactician import TacticianProfile
from .berserker import BerserkerProfile
from .defender import DefenderProfile
from .controller import ControllerProfile
from .assassin import AssassinProfile
from .commander import CommanderProfile

# Register all profiles
register_profile("brute", BruteProfile())
register_profile("skirmisher", SkirmisherProfile())
register_profile("caster", CasterProfile())
register_profile("support", SupportProfile())
register_profile("tactician", TacticianProfile())
register_profile("berserker", BerserkerProfile())
register_profile("defender", DefenderProfile())
register_profile("controller", ControllerProfile())
register_profile("assassin", AssassinProfile())
register_profile("commander", CommanderProfile())

# Default fallback
register_profile("default", BaseAIProfile("default"))
