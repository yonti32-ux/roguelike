# settings.py

# Window / display
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
TITLE = "Roguelike v2"

# Colors
COLOR_BG = (15, 15, 20)
COLOR_PLAYER = (220, 210, 90)
COLOR_ENEMY = (200, 80, 80)

# World
TILE_SIZE = 32

# Battle settings
BATTLE_GRID_WIDTH = 15  # Increased for larger parties and tactical positioning
BATTLE_GRID_HEIGHT = 7  # Increased for more vertical space
BATTLE_CELL_SIZE = 70  # Slightly smaller to fit larger grid on screen
BATTLE_ENEMY_TIMER = 0.6
MAX_BATTLE_ENEMIES = 6  # Increased to match larger grid
BATTLE_AI_DEFENSIVE_HP_THRESHOLD = 0.4
BATTLE_AI_SKILL_CHANCE = 0.4
BATTLE_AI_DEFENSIVE_SKILL_CHANCE = 0.5

# Skill system
MAX_SKILL_SLOTS = 4  # SKILL_1 to SKILL_4

# Companion skill point allocation
# If True, companions automatically allocate skill points based on their role
# If False, player manually allocates skill points for companions
AUTO_ALLOCATE_COMPANION_SKILL_POINTS = False

# Default stats (fallback values)
DEFAULT_PLAYER_MAX_HP = 24
DEFAULT_PLAYER_ATTACK = 5
DEFAULT_PLAYER_STAMINA = 6  # Legacy fallback (classes override this)
DEFAULT_PLAYER_MANA = 0  # Legacy fallback (classes override this)
DEFAULT_COMPANION_STAMINA = 4  # Legacy fallback (companions use class-based)
DEFAULT_COMPANION_MANA = 0  # Legacy fallback (companions use class-based)
DEFAULT_ENEMY_STAMINA = 12  # Increased: enemies should be able to use skills
DEFAULT_ENEMY_MANA = 8  # For caster enemies
DEFAULT_COMPANION_HP_FACTOR = 0.8
DEFAULT_COMPANION_ATTACK_FACTOR = 0.7

# Skill power defaults
DEFAULT_MIN_SKILL_POWER = 0.5

# Battle grid positioning
BATTLE_ENEMY_START_COL_OFFSET = 3  # Enemies start this many columns from right edge

# Critical hit settings
BASE_CRIT_CHANCE = 0.10  # 10% base critical hit chance
CRIT_DAMAGE_MULTIPLIER = 1.75  # Critical hits deal 1.75x damage

# Battle terrain settings
COVER_DAMAGE_REDUCTION = 0.5  # Cover reduces ranged damage by 50%
FLANKING_DAMAGE_BONUS = 1.25  # Flanking attacks deal +25% damage
TERRAIN_SPAWN_CHANCE = 0.3  # 30% chance each cell spawns terrain

# Movement system
BASE_MOVEMENT_POINTS = 3  # Base movement points per turn
HAZARD_MOVEMENT_COST = 2  # Hazards cost extra movement (1 + 1 = 2 total)
DIAGONAL_MOVEMENT_COST = 1.5  # Diagonal movement costs 1.5x more (rounded up)