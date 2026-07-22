# Status Visual Effects - Ideas & Considerations

## Overview

This document explores ideas for enhancing status effects with visual feedback beyond the current text-based icons.

---

## Current Status Display

- Text icons: `[`, `v`, `P`, `B`, `*`, etc.
- Color-coded by status type
- Timers and stack counts shown
- Positioned above/next to units

---

## Visual Enhancement Ideas

### 1. **Pulsing/Flashing Effects**

**Concept**: Status icons pulse or flash to draw attention, especially for:
- Expiring statuses (low duration)
- Important buffs/debuffs
- Stacking statuses

**Implementation Approaches**:
- Alpha animation: Fade in/out over time
- Scale animation: Slightly grow/shrink
- Color animation: Brighten/darken the icon color

**When to Use**:
- **Expiring**: When duration ≤ 1 turn (warning before expiration)
- **Critical**: For important statuses (stun, guard, major buffs)
- **Stacking**: When stacks increase (brief pulse on application)

**Code Approach**:
```python
# In draw_single_status():
pulse_phase = (timer * 2 * math.pi) % (2 * math.pi)
alpha_mult = 1.0 + 0.2 * math.sin(pulse_phase)  # 20% pulse
color = tuple(int(c * alpha_mult) for c in base_color)
```

---

### 2. **Glow Effects**

**Concept**: Status icons glow with a colored aura, matching status type.

**Visual Effect**:
- Subtle colored shadow/halo around status icon
- Intensity based on importance (stacks, duration)
- Color matches status type (blue for buffs, red for debuffs)

**Implementation**:
- Draw multiple semi-transparent copies of icon with blur
- Or: Draw colored circle/rectangle behind icon with transparency

**When to Use**:
- **Always**: All statuses get a subtle glow
- **Intense**: Important statuses get brighter glow
- **Multi-color**: Statuses with stacks could have glow intensity scale with stacks

**Code Approach**:
```python
# Draw glow behind icon
glow_surf = pygame.Surface((icon_size + 4, icon_size + 4), pygame.SRCALPHA)
glow_color = (*color, 60)  # 60 alpha for subtle glow
pygame.draw.circle(glow_surf, glow_color, (icon_size//2 + 2, icon_size//2 + 2), icon_size//2 + 2)
surface.blit(glow_surf, (x - 2, y - 2))
```

---

### 3. **Animated Status Icons**

**Concept**: Replace static text icons with simple animated shapes.

**Examples**:
- **Guard**: Pulsing shield shape `[→]→[→]`
- **Poison**: Dripping droplet `●↓ ●↓`
- **Stun**: Spinning stars `* * * *`
- **Regeneration**: Rising sparkles `+↑ +↑`

**Implementation**:
- Frame-based animation: Cycle through different character sets
- Or: Draw simple shapes with pygame.draw (circles, lines, etc.)

**Trade-offs**:
- More visually interesting
- May be distracting if too animated
- Requires more code/complexity

---

### 4. **Status Bar/Indicator on Unit**

**Concept**: Visual indicator directly on the unit sprite/model showing active statuses.

**Approaches**:
- **Colored Border**: Border color changes based on primary status
  - Blue = buffs active
  - Red = debuffs active
  - Yellow = mixed
- **Status Ribbons**: Small colored ribbons/banners on unit
- **Status Particles**: Small particles floating around unit
  - Green for regen
  - Red for DoT
  - Blue for buffs

**Pros**:
- Very visible
- Doesn't clutter UI
- Integrates with unit display

**Cons**:
- May obscure unit appearance
- Harder to see specific statuses

---

### 5. **Combined Status Display**

**Concept**: Show multiple statuses in a compact visual way.

**Options**:
- **Status Stack**: Icons stacked in a vertical/horizontal bar
- **Status Wheel**: Icons arranged in a circle around unit
- **Status Panel**: Dedicated panel showing all statuses with details

---

### 6. **Expiration Warning**

**Concept**: Visual cue when status is about to expire.

**Methods**:
- **Color Change**: Icon turns red/yellow when duration ≤ 1
- **Flashing**: Icon flashes rapidly before expiring
- **Size Change**: Icon shrinks as duration decreases
- **Opacity**: Icon fades out as duration decreases

**Implementation**:
```python
# Warn when duration is low
if duration <= 1:
    # Flash between normal and warning color
    warning_color = (255, 100, 100) if timer % 0.5 < 0.25 else normal_color
    icon_surf = font.render(icon_text, True, warning_color)
```

---

### 7. **Stack Visualization**

**Concept**: Visual representation of stack count beyond text.

**Options**:
- **Icon Duplication**: Draw multiple icons (side-by-side or overlapping)
- **Border Thickness**: Thicker border = more stacks
- **Icon Size**: Larger icon = more stacks
- **Particle Count**: More particles around icon = more stacks

**Current**: Text `×N` works well, but could enhance with visual feedback

---

### 8. **Status Application Feedback**

**Concept**: Brief visual effect when status is applied.

**Effects**:
- **Flash**: Brief bright flash when status appears
- **Pop**: Icon "pops in" with scale animation
- **Sound**: Audio cue (if audio system exists)
- **Text Popup**: Floating text "Guard Applied!" (like damage numbers)

---

## Recommended Implementation Priority

### Phase 1: Simple Enhancements (Easy, High Impact)
1. **Expiration Warning**: Flash/color change when duration ≤ 1
2. **Subtle Glow**: Light colored halo around status icons
3. **Application Flash**: Brief brightness increase when status applied

### Phase 2: Polish (Medium Effort)
4. **Pulsing Animation**: Gentle pulse for important statuses
5. **Stack Visualization**: Enhanced visual for stacking statuses
6. **Status Bar Integration**: Visual indicator on unit sprite

### Phase 3: Advanced (More Complex)
7. **Animated Icons**: Frame-based icon animations
8. **Particle Effects**: Particles around units with statuses
9. **Status Wheel/Panel**: Dedicated status display UI

---

## Technical Considerations

### Performance
- **Animation Cost**: Pulsing/glowing for many units could impact FPS
- **Optimization**: Only animate visible statuses, limit animation frequency
- **Caching**: Pre-render animated frames if using frame-based animation

### Visual Clarity
- **Don't Overdo**: Too many effects can be distracting
- **Prioritize**: Only animate important/expiring statuses
- **Consistency**: Use same effects across similar status types

### Code Structure
- **Renderer Separation**: Keep visual effects in renderer module
- **Configurable**: Make effects optional/configurable
- **Modular**: Each effect type should be independent

---

## Example Code Structure

```python
# ui/status_display.py
def draw_status_with_effects(
    surface: pygame.Surface,
    font: pygame.font.Font,
    x: int, y: int,
    status: StatusEffect,
    info: Dict,
    timer: float,  # Animation timer
    enable_glow: bool = True,
    enable_pulse: bool = True,
):
    """Draw status with optional visual effects."""
    
    # Base icon
    icon_text = info["icon"]
    base_color = info["color"]
    
    # Apply pulse effect
    if enable_pulse and status.duration <= 1:
        pulse = 1.0 + 0.3 * math.sin(timer * 8)  # Fast pulse for expiring
        color = tuple(int(c * pulse) for c in base_color)
    else:
        color = base_color
    
    # Draw glow
    if enable_glow:
        _draw_status_glow(surface, x, y, color, info["is_buff"])
    
    # Draw icon
    icon_surf = font.render(icon_text, True, color)
    surface.blit(icon_surf, (x, y))
```

---

## Conclusion

**Recommended Starting Point**:
1. Add expiration warning (flash when duration ≤ 1)
2. Add subtle glow for all statuses
3. Test and iterate based on feedback

These provide significant visual improvement with minimal complexity. More advanced effects can be added later if desired.

