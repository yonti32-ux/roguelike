# Battle AI System

Modular AI system for enemy decision-making in battle.

## Structure

```
engine/battle/ai/
├── __init__.py          # Main exports
├── core.py              # BattleAI orchestrator class
├── profiles.py          # AI profile system and base classes
├── threat.py            # Threat assessment system
├── skill_priority.py    # Skill evaluation and prioritization
├── coordination.py      # Team coordination and focus fire
├── positioning.py       # Movement and positioning helpers
├── profiles/            # Profile implementations
│   ├── __init__.py      # Profile registration
│   ├── brute.py         # Brute AI profile
│   ├── skirmisher.py    # Skirmisher AI profile
│   ├── caster.py        # Caster AI profile
│   └── support.py        # Support AI profile
└── README.md            # This file
```

## Modules

### Core (`core.py`)
- `BattleAI`: Main orchestrator class
- Coordinates all AI subsystems
- Provides common helper methods

### Profiles (`profiles.py` + `profiles/`)
- `AIProfile`: Protocol for AI behavior
- `BaseAIProfile`: Base implementation
- Profile-specific implementations:
  - `BruteProfile`: Aggressive melee fighters
  - `SkirmisherProfile`: Mobile flankers
  - `CasterProfile`: Ranged spellcasters
  - `SupportProfile`: Healers and buffers

### Threat Assessment (`threat.py`)
- `ThreatAssessment`: Calculates threat values
- `calculate_threat_value()`: Assess unit danger
- `rank_targets_by_threat()`: Sort targets by threat

### Skill Prioritization (`skill_priority.py`)
- `SkillPrioritizer`: Evaluates skill value
- `evaluate_skill_value()`: Score skills situationally
- Considers: cooldowns, resources, context, combos

### Coordination (`coordination.py`)
- `CoordinationManager`: Team tactics
- `should_focus_fire()`: Focus fire logic
- `get_focus_target()`: Best focus target
- Tracks target assignments

### Positioning (`positioning.py`)
- `PositioningHelper`: Movement helpers
- `find_flanking_position()`: Flank opportunities
- `find_optimal_aoe_position()`: AoE positioning
- `find_optimal_range_position()`: Range maintenance

## Usage

```python
from engine.battle.ai import BattleAI

# Initialize AI
ai = BattleAI(scene)

# Execute AI turn
ai.execute_ai_turn(enemy_unit)
```

## Adding New Profiles

1. Create a new profile class in `profiles/`:

```python
from ..profiles import BaseAIProfile
from ..core import BattleAI

class MyProfile(BaseAIProfile):
    def choose_target(self, unit, targets, ai):
        # Custom targeting logic
        pass
    
    def execute_turn(self, unit, ai, hp_ratio):
        # Custom turn logic
        pass
```

2. Register it in `profiles/__init__.py`:

```python
from .my_profile import MyProfile
register_profile("my_profile", MyProfile())
```

## Benefits

1. **Modular**: Each system is separate and testable
2. **Extensible**: Easy to add new profiles and behaviors
3. **Maintainable**: Clear separation of concerns
4. **Organized**: Related functionality grouped together
