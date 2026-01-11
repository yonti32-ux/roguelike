"""
Extract individual 32x32 sprites from 32rogues sprite sheets.

This script extracts sprites from the sprite sheets in the 32rogues pack
and saves them as individual PNG files organized by category.
"""

import pygame
from pathlib import Path
from typing import Tuple, List, Dict

# Initialize pygame (required for image loading)
pygame.init()

# Sprite size (32x32 pixels)
SPRITE_SIZE = 32

# Mapping of sprite sheet files to their grid dimensions
# Format: (sheet_file, rows, cols)
SPRITE_SHEETS = {
    "rogues.png": (7, 7),        # 224x224 = 7x7 grid
    "monsters.png": (13, 12),    # 416x384 = 13x12 grid (actually 384x416, so 12x13)
    "items.png": (26, 11),       # 832x352 = 26x11 grid
    "tiles.png": (26, 17),       # 832x544 = 26x17 grid
    "animals.png": (16, 9),      # 512x288 = 16x9 grid
    "animated-tiles.png": (12, 11),  # 384x352 = 12x11 grid
    "autotiles.png": (8, 12),    # 256x384 = 8x12 grid
}

# Output directories by category
OUTPUT_DIRS = {
    "rogues.png": "entity",
    "monsters.png": "entity",
    "items.png": "item",
    "tiles.png": "tile",
    "animals.png": "entity",
    "animated-tiles.png": "effect",
    "autotiles.png": "tile",
}

# Mapping of sheet positions to sprite names (optional - if None, uses position-based naming)
# Format: {sheet_file: {(row, col): "sprite_name"}}
SPRITE_NAMES = {
    # Will be populated based on metadata from .txt files or manual mapping
}


def extract_sprite(sheet: pygame.Surface, row: int, col: int, sprite_size: int = SPRITE_SIZE) -> pygame.Surface:
    """Extract a single sprite from a sprite sheet."""
    x = col * sprite_size
    y = row * sprite_size
    rect = pygame.Rect(x, y, sprite_size, sprite_size)
    sprite = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    sprite.blit(sheet, (0, 0), rect)
    return sprite


def extract_sprites_from_sheet(
    sheet_path: Path,
    output_dir: Path,
    rows: int,
    cols: int,
    sprite_names: Dict[Tuple[int, int], str] = None,
    prefix: str = "",
) -> List[Path]:
    """Extract all sprites from a sprite sheet and save them as individual files."""
    if not sheet_path.exists():
        print(f"Warning: Sheet not found: {sheet_path}")
        return []
    
    print(f"Processing {sheet_path.name} ({rows}x{cols} grid)...")
    sheet = pygame.image.load(str(sheet_path)).convert_alpha()
    sheet_width, sheet_height = sheet.get_size()
    
    # Verify dimensions match expected grid
    expected_width = cols * SPRITE_SIZE
    expected_height = rows * SPRITE_SIZE
    if sheet_width != expected_width or sheet_height != expected_height:
        print(f"  Warning: Sheet dimensions {sheet_width}x{sheet_height} don't match expected {expected_width}x{expected_height}")
        # Try to calculate actual grid size
        actual_cols = sheet_width // SPRITE_SIZE
        actual_rows = sheet_height // SPRITE_SIZE
        print(f"  Adjusting to {actual_rows}x{actual_cols} grid")
        rows, cols = actual_rows, actual_cols
    
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_files = []
    
    for row in range(rows):
        for col in range(cols):
            sprite = extract_sprite(sheet, row, col)
            
            # Check if sprite is not empty (has non-transparent pixels)
            if sprite.get_width() == 0 or sprite.get_height() == 0:
                continue
            
            # Generate filename
            if sprite_names and (row, col) in sprite_names:
                filename = f"{prefix}{sprite_names[(row, col)]}.png"
            else:
                # Use position-based naming: sheetname_row_col.png
                sheet_basename = sheet_path.stem
                filename = f"{prefix}{sheet_basename}_{row}_{col}.png"
            
            output_path = output_dir / filename
            pygame.image.save(sprite, str(output_path))
            extracted_files.append(output_path)
    
    print(f"  Extracted {len(extracted_files)} sprites to {output_dir}")
    return extracted_files


def load_sprite_names_from_txt(txt_path: Path) -> Dict[Tuple[int, int], str]:
    """Load sprite name mappings from .txt metadata files."""
    sprite_names = {}
    if not txt_path.exists():
        return sprite_names
    
    # Parse format like "1.a. dwarf", "1.b. elf", etc.
    # Converts to row/col indices
    with txt_path.open('r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line or '.' not in line:
            continue
        
        # Parse format: "row.letter. name"
        parts = line.split('.', 2)
        if len(parts) >= 3:
            try:
                row_idx = int(parts[0]) - 1  # Convert to 0-based
                letter = parts[1].strip().lower()
                name = parts[2].strip().lower().replace(' ', '_').replace("'", "")
                
                # Convert letter to column (a=0, b=1, etc.)
                col_idx = ord(letter) - ord('a')
                
                sprite_names[(row_idx, col_idx)] = name
            except (ValueError, IndexError):
                continue
    
    return sprite_names


def main():
    """Main extraction function."""
    project_root = Path(__file__).parent.parent
    source_dir = project_root / "32rogues"
    sprites_dir = project_root / "sprites"
    
    if not source_dir.exists():
        print(f"Error: 32rogues directory not found at {source_dir}")
        return
    
    print(f"Extracting sprites from {source_dir}")
    print(f"Output directory: {sprites_dir}")
    print()
    
    all_extracted = []
    
    for sheet_file, (rows, cols) in SPRITE_SHEETS.items():
        sheet_path = source_dir / sheet_file
        txt_path = source_dir / sheet_file.replace('.png', '.txt')
        
        if not sheet_path.exists():
            print(f"Skipping {sheet_file} (not found)")
            continue
        
        # Determine output category
        category = OUTPUT_DIRS.get(sheet_file, "entity")
        output_dir = sprites_dir / category
        
        # Try to load sprite name mappings from .txt file
        sprite_names = load_sprite_names_from_txt(txt_path)
        
        # Extract sprites
        extracted = extract_sprites_from_sheet(
            sheet_path,
            output_dir,
            rows,
            cols,
            sprite_names if sprite_names else None,
            prefix=""  # No prefix, use the names from mapping or position-based
        )
        
        all_extracted.extend(extracted)
        print()
    
    print(f"\nDone! Extracted {len(all_extracted)} sprites total.")
    print(f"Sprites saved to: {sprites_dir}")
    
    # Create a summary file with sprite mappings
    summary_path = project_root / "docs" / "32ROGUES_SPRITE_MAPPINGS.md"
    summary_path.parent.mkdir(exist_ok=True)
    
    with summary_path.open('w', encoding='utf-8') as f:
        f.write("# 32rogues Sprite Extraction Summary\n\n")
        f.write(f"Extracted {len(all_extracted)} sprites from sprite sheets.\n\n")
        f.write("## Sprite Locations\n\n")
        f.write("Sprites are organized in the following directories:\n\n")
        for category in OUTPUT_DIRS.values():
            cat_dir = sprites_dir / category
            if cat_dir.exists():
                count = len(list(cat_dir.glob("*.png")))
                f.write(f"- `sprites/{category}/` - {count} sprites\n")
        f.write("\n## Next Steps\n\n")
        f.write("1. Review extracted sprites\n")
        f.write("2. Rename sprites to match game entity/item IDs if needed\n")
        f.write("3. Update sprite registry in `engine/sprites/sprite_registry.py`\n")
        f.write("4. Update preload list in `engine/sprites/init_sprites.py`\n")
    
    print(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
