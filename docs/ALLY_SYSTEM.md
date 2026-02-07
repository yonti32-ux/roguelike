# Ally System Documentation

## Overview

The ally system provides a comprehensive framework for friendly units that join the player in battle, similar to the enemy archetype system but designed for allies. Allies are AI-controlled units that fight on the player's side.

## Architecture

### Core Components

1. **Ally Archetypes** (`systems/allies/types.py`)
   - Defines different types of allies (guards, rangers, merchants, etc.)
   - Each archetype has:
     - Role and AI profile
     - Base stats and per-level scaling
     - Skill lists
     - Party type associations

2. **Ally Registry** (`systems/allies/registry.py`)
   - Manages global registry of ally archetypes
   - Provides lookup functions

3. **Ally Scaling** (`systems/allies/scaling.py`)
   - Scales ally stats based on player level
   - Ensures allies are balanced relative to the player

4. **Ally Definitions** (`systems/allies/definitions/`)
   - Organized by category:
     - `guardians.py`: Guards, knights, defensive allies
     - `rangers.py`: Rangers, scouts, mobile allies
     - `merchants.py`: Merchant guards, villagers
     - `military.py`: Mercenaries, adventurers
     - `specialists.py`: Support, casters (for future expansion)

## How It Works

### Party Type Matching

Allies are matched to party types via the `party_type_ids` field in ally archetypes:

```python
AllyArchetype(
    id="town_guard",
    party_type_ids=["guard"],  # Matches party type with id="guard"
    ...
)
```

When an allied party joins battle:
1. System looks up ally archetype by party type ID
2. If found, creates ally using archetype stats and skills
3. If not found, falls back to legacy companion-based system

### Stat Scaling

Allies scale with player level using the `compute_scaled_stats()` function:

```python
max_hp, attack, defense, skill_power, initiative = compute_scaled_stats(
    ally_archetype, player_level
)
```

Allies are typically slightly weaker than the player to maintain the player as the primary combatant.

### AI Profiles

Each ally archetype has an `ai_profile` that determines behavior:
- `defender`: Protects allies, uses guard, bodyblocks
- `skirmisher`: Mobile, flanks enemies, hit-and-run
- `tactician`: Smart positioning, combos, focus fire
- `support`: Heals and buffs allies
- `brute`: Aggressive melee (default fallback)

The AI profile is automatically assigned based on the ally's archetype.

### Skills

Allies receive skills from their archetype's `skill_ids` list. Common skills:
- `guard`: Defensive stance
- `heavy_slam`: Melee attack
- `crippling_blow`: Debuff attack
- `nimble_step`: Movement skill
- `war_cry`: Buff skill
- `mark_target`: Support skill

## Current Ally Archetypes

### Guardians (7 archetypes)
- **Town Guard**: Basic defensive ally (guard parties) - `defender` AI
- **Knight**: Elite defensive ally (knight parties) - `defender` AI
- **Noble Guard**: Protective escort (noble parties) - `defender` AI
- **Shield Bearer**: Heavy defensive specialist (guard, knight parties) - `defender` AI - High defense, tanky
- **Sentinel**: Elite watchman (guard, knight parties) - `defender` AI - Elite variant
- **Watchman**: Light guard (guard parties) - `defender` AI - Basic patrol unit

### Rangers (6 archetypes)
- **Ranger**: Mobile skirmisher (ranger parties) - `skirmisher` AI
- **Scout**: Fast reconnaissance (scout parties) - `skirmisher` AI
- **Tracker**: Specialized hunter (ranger, scout parties) - `skirmisher` AI - Marks targets
- **Hunter**: Ranged specialist (ranger parties) - `skirmisher` AI - High attack
- **Pathfinder**: Explorer guide (ranger, scout parties) - `skirmisher` AI - Balanced
- **Archer**: Ranged specialist (ranger, scout parties) - `skirmisher` AI - Deadly aim

### Military (6 archetypes)
- **Mercenary**: Professional fighter (mercenary parties) - `tactician` AI
- **Adventurer**: Skilled explorer (adventurer parties) - `tactician` AI
- **Veteran**: Experienced fighter (mercenary, adventurer parties) - `tactician` AI - Battle-hardened
- **Captain**: Military leader (knight, mercenary parties) - `commander` AI - Elite leader
- **Soldier**: Basic military unit (guard, mercenary parties) - `brute` AI - Disciplined
- **Champion**: Elite fighter (knight, adventurer parties) - `tactician` AI - Legendary hero

### Merchants & Civilians (5 archetypes)
- **Merchant Guard**: Protects caravans (merchant, trader parties) - `defender` AI
- **Villager**: Basic civilian ally (villager, pilgrim parties) - `brute` AI
- **Trader**: Merchant variant (merchant, trader parties) - `brute` AI - Knows how to fight
- **Pilgrim**: Religious traveler (pilgrim parties) - `brute` AI - Holy journey
- **Farmer**: Civilian fighter (villager parties) - `brute` AI - Protects home

### Support (7 archetypes)
- **Cleric**: Support healer - `support` AI - Heals and buffs
- **Paladin**: Support guardian hybrid - `defender` AI - Holy warrior
- **Bard**: Support buffer - `support` AI - Inspires allies
- **Druid**: Nature support - `support` AI - Nature magic
- **Priest**: Healer variant - `support` AI - Divine power
- **Shaman**: Tribal support - `support` AI - Spiritual energy

### Specialists (6 archetypes)
- **Assassin**: Stealth ally - `assassin` AI - Deadly strikes
- **Mage**: Caster ally - `caster` AI - Powerful magic
- **Archer**: Ranged specialist (ranger, scout parties) - `skirmisher` AI - Deadly aim
- **Berserker**: Aggressive fighter - `berserker` AI - Reckless fury
- **Duelist**: Skilled fighter (mercenary, adventurer parties) - `tactician` AI - One-on-one combat
- **Warden**: Protective specialist (guard, knight parties) - `defender` AI - Enforces order

**Total: 37 ally archetypes** across all categories!

## Ally Packs

Similar to enemy packs, allies can join in themed groups that provide tactical variety:

### Guard Patrols
- **Guard Patrol**: 2 Town Guards (Guard Formation: +10% defense)
- **Elite Guard Patrol**: 1 Knight + 1 Guard (Elite Formation: +15% attack to guards)

### Ranger Teams
- **Ranger Team**: 2 Rangers (Ranger Coordination: +15% attack when flanking)
- **Scout Team**: 2 Scouts (Scout Network: +1 movement points)

### Merchant Caravans
- **Merchant Caravan**: 2 Merchant Guards (Caravan Defense: +10% HP)

### Military Units
- **Mercenary Company**: 2 Mercenaries (Professional Teamwork: +10% attack, +5% defense)
- **Adventuring Party**: 2 Adventurers (Adventurer Synergy: +15% skill power, +1 initiative)

### Mixed Formations
- **Combined Patrol**: Guard + Ranger (Combined Tactics: Guard protects, Ranger flanks)
- **Elite Force**: Knight + Mercenary (Elite Coordination: +20% attack, +10% defense)

## Ally Synergies

When multiple allies fight together, they gain synergy bonuses based on their tags:

### Tag-Based Synergies
- **Guard Formation** (2+ guardians): +10% defense
- **Ranger Coordination** (2+ rangers): +15% attack (flanking bonus)
- **Military Discipline** (2+ military): +10% attack, +5% defense
- **Caravan Defense** (2+ merchant guards): +10% HP
- **Elite Coordination** (1+ elite): +5% all stats per elite (max +15%)
- **Support Network** (1+ support): +20% skill power
- **Combined Tactics** (guardian + ranger): +1 movement
- **Professional Teamwork** (2+ military/mercenary): +1 initiative

Synergies are automatically calculated and applied when allies join battle.

## Integration Points

### Battle Conversion
- `world/overworld/battle_conversion.py::allied_party_to_battle_units()`
  - Converts allied parties to battle units
  - Uses ally archetypes when available
  - Selects ally packs when multiple allies join
  - Applies pack member archetypes

### Battle AI
- `engine/battle/ai/core.py::get_ai_profile()`
  - Gets AI profile from ally archetype
  - Falls back to "brute" if no archetype

### Battle Scene
- `engine/core/game.py::_add_allied_parties_to_battle()`
  - Adds allies to battle
  - Assigns skills from archetype
  - Applies synergy bonuses to ally groups

## Adding New Ally Archetypes

1. Create archetype in appropriate definition file:
```python
register_archetype(
    AllyArchetype(
        id="new_ally",
        name="New Ally",
        role="Role Name",
        ai_profile="defender",  # or skirmisher, tactician, support, etc.
        base_hp=35,
        hp_per_level=6,
        base_attack=7,
        atk_per_level=1.3,
        base_defense=3,
        def_per_level=0.5,
        skill_ids=["guard", "heavy_slam"],
        party_type_ids=["party_type_id"],  # Match party type
        tags=["guardian", "military"],  # For synergies
        description="Description for UI",
    )
)
```

2. Register in `systems/allies/definitions/__init__.py` if creating new category

3. Ensure party type IDs match in `world/overworld/party_types.py`

## Adding New Ally Packs

1. Create pack in `systems/allies/definitions/packs.py`:
```python
register_pack(
    AllyPackTemplate(
        id="new_pack",
        name="New Pack",
        member_arch_ids=[
            "ally_archetype_1",
            "ally_archetype_2",
        ],
        party_type_ids=["party_type_id"],
        weight=1.0,  # Selection weight
        synergy_bonus="Pack synergy description",
    )
)
```

2. Packs are automatically registered when module loads

3. Packs are selected when multiple allies join (2+ allies)

## System Features

### Pack System
- Allies can join in themed packs when multiple allies are present
- Packs provide variety and tactical combinations
- Weighted random selection for pack variety

### Synergy System
- Automatic bonuses when allies fight together
- Tag-based synergy detection
- Stat multipliers and flat bonuses
- Applied automatically when allies join battle

### AI Profiles
- Each archetype has appropriate AI behavior
- Defender: Protects and bodyblocks
- Skirmisher: Flanks and hit-and-run
- Tactician: Smart positioning and combos
- Support: Heals and buffs allies
- Brute: Aggressive melee (fallback)

## Future Enhancements

- Support/caster allies in actual party types (currently defined but not used)
- Unique mechanics per archetype (auras, special abilities)
- Ally-specific perks/traits
- Dynamic ally recruitment
- Ally equipment/upgrades
- More pack combinations
- Pack-specific unique abilities