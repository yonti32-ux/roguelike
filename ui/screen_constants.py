"""
UI constants for fullscreen screens.

This module contains all color, spacing, layout, and display constants
used by the fullscreen UI screens (inventory, character sheet, shop, etc.).
"""

# ============================================================================
# Base Colors
# ============================================================================
COLOR_TITLE = (255, 255, 210)
COLOR_SUBTITLE = (230, 230, 190)
COLOR_TEXT = (230, 230, 230)
COLOR_TEXT_DIM = (210, 210, 210)
COLOR_TEXT_DIMMER = (190, 190, 190)
COLOR_TEXT_DIMMEST = (170, 170, 170)
COLOR_GOLD = (255, 220, 130)
COLOR_CATEGORY = (220, 220, 170)
COLOR_STATUS = (190, 210, 230)
COLOR_SELECTED_BG = (70, 70, 100, 220)
COLOR_SELECTED_TEXT = (255, 255, 210)
COLOR_TAB_ACTIVE = (255, 255, 210)
COLOR_TAB_INACTIVE = (160, 160, 160)
COLOR_FOOTER = (170, 170, 170)

# ============================================================================
# Enhanced Colors for Visual Polish
# ============================================================================
# Background colors
COLOR_BG_PANEL = (25, 25, 35, 240)  # Semi-transparent panel background
COLOR_BG_PANEL_DARK = (15, 15, 25, 250)  # Darker panel background
COLOR_BG_OVERLAY = (0, 0, 0, 200)  # Overlay background

# Border colors
COLOR_BORDER = (100, 120, 150)
COLOR_BORDER_BRIGHT = (150, 170, 200)
COLOR_BORDER_DIM = (60, 70, 85)
COLOR_BORDER_GOLD = (200, 180, 100)

# Shadow colors
COLOR_SHADOW = (0, 0, 0, 180)
COLOR_SHADOW_LIGHT = (0, 0, 0, 100)

# Selection and hover colors
COLOR_SELECTED_BG_BRIGHT = (90, 100, 130, 240)
COLOR_HOVER_BG = (50, 55, 70, 200)
COLOR_HOVER_BORDER = (120, 140, 170)

# Accent colors
COLOR_ACCENT_PRIMARY = (100, 150, 255)
COLOR_ACCENT_SECONDARY = (255, 180, 100)
COLOR_ACCENT_SUCCESS = (100, 220, 100)
COLOR_ACCENT_WARNING = (255, 200, 100)
COLOR_ACCENT_DANGER = (255, 120, 120)

# Gradient colors (for backgrounds)
COLOR_GRADIENT_START = (30, 35, 50)
COLOR_GRADIENT_END = (20, 25, 35)

# Spacing
MARGIN_X = 40
MARGIN_Y_TOP = 30
MARGIN_Y_START = 90
MARGIN_Y_FOOTER = 50
LINE_HEIGHT_SMALL = 22
LINE_HEIGHT_MEDIUM = 24
LINE_HEIGHT_LARGE = 26
LINE_HEIGHT_TITLE = 28
LINE_HEIGHT_ITEM = 38
SPACING_SECTION = 30

# Layout
# Tab spacing and starting X for the header tabs.
TAB_SPACING = 130
TAB_X_OFFSET = 520
INDENT_DEFAULT = 20
INDENT_INFO = 24

# Item display
MAX_DESC_LENGTH = 80
ITEM_NAME_HEIGHT = 22
ITEM_INFO_HEIGHT = 20
ITEM_MIN_SPACING = 8
ITEM_SPACING_BETWEEN = 6  # Extra spacing between items
ITEM_PADDING_VERTICAL = 6  # Vertical padding inside item card
ITEM_PADDING_HORIZONTAL = 4  # Horizontal padding inside item card

# ============================================================================
# Visual Effects Constants
# ============================================================================
# Shadow offsets
SHADOW_OFFSET_X = 2
SHADOW_OFFSET_Y = 2
SHADOW_BLUR = 3

# Border widths
BORDER_WIDTH_THIN = 1
BORDER_WIDTH_MEDIUM = 2
BORDER_WIDTH_THICK = 3

# Panel properties
PANEL_PADDING = 12
PANEL_BORDER_RADIUS = 4  # For visual reference (simulated with rectangles)
PANEL_SHADOW_SIZE = 4

