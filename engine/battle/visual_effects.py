"""
Visual effects manager for battle system.

Handles screen shake, particle effects, screen flashes, and other visual polish.
"""

from typing import List, Dict, Optional, Tuple
import math
import random
import pygame


class Particle:
    """A single particle for visual effects."""
    
    def __init__(
        self,
        x: float,
        y: float,
        vx: float = 0.0,
        vy: float = 0.0,
        color: Tuple[int, int, int] = (255, 255, 255),
        size: float = 2.0,
        lifetime: float = 1.0,
        gravity: float = 0.0,
        fade_out: bool = True,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.fade_out = fade_out
    
    def update(self, dt: float) -> bool:
        """Update particle position and lifetime. Returns False if particle should be removed."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.lifetime -= dt
        return self.lifetime > 0
    
    def get_alpha(self) -> int:
        """Get alpha value based on remaining lifetime."""
        if not self.fade_out:
            return 255
        ratio = self.lifetime / self.max_lifetime if self.max_lifetime > 0 else 1.0
        return int(255 * ratio)


class VisualEffectsManager:
    """Manages all visual effects for the battle scene."""
    
    def __init__(self):
        # Screen shake
        self.shake_intensity: float = 0.0
        self.shake_duration: float = 0.0
        self.shake_offset_x: float = 0.0
        self.shake_offset_y: float = 0.0
        
        # Screen flash
        self.flash_color: Optional[Tuple[int, int, int]] = None
        self.flash_alpha: float = 0.0
        self.flash_duration: float = 0.0
        
        # Particles
        self.particles: List[Particle] = []
        
        # Health bar smooth animations (using id() as key since BattleUnit is not hashable)
        self.health_bar_targets: Dict[int, float] = {}  # unit_id -> target_ratio
        self.health_bar_current: Dict[int, float] = {}  # unit_id -> current_ratio
        
        # Movement trails
        self.movement_trails: List[Dict] = []
    
    def add_screen_shake(self, intensity: float, duration: float = 0.3) -> None:
        """Add screen shake effect."""
        # Use maximum intensity if already shaking
        if self.shake_duration > 0:
            self.shake_intensity = max(self.shake_intensity, intensity)
            self.shake_duration = max(self.shake_duration, duration)
        else:
            self.shake_intensity = intensity
            self.shake_duration = duration
    
    def add_screen_flash(
        self,
        color: Tuple[int, int, int] = (255, 255, 255),
        duration: float = 0.15,
        alpha: float = 100.0,
    ) -> None:
        """Add screen flash effect."""
        self.flash_color = color
        self.flash_alpha = alpha
        self.flash_duration = duration
    
    def add_hit_particles(
        self,
        x: float,
        y: float,
        count: int = 8,
        color: Tuple[int, int, int] = (255, 200, 100),
        is_crit: bool = False,
    ) -> None:
        """Add particle burst for hit effects."""
        if is_crit:
            count = count * 2
            color = (255, 255, 150)
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150) if is_crit else random.uniform(30, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(20, 50)  # Slight upward bias
            
            particle = Particle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                color=color,
                size=random.uniform(2, 4) if is_crit else random.uniform(1.5, 3),
                lifetime=random.uniform(0.3, 0.6),
                gravity=100.0,
                fade_out=True,
            )
            self.particles.append(particle)
    
    def add_skill_particles(
        self,
        x: float,
        y: float,
        skill_type: str = "default",
        count: int = 15,
    ) -> None:
        """Add particles for skill effects."""
        # Different particle effects based on skill type
        if skill_type in ["power_strike", "strike", "attack"]:
            color = (255, 150, 50)
        elif skill_type in ["heal", "restore"]:
            color = (100, 255, 150)
        elif skill_type in ["buff", "shield", "guard"]:
            color = (150, 200, 255)
        elif skill_type in ["debuff", "curse"]:
            color = (200, 100, 255)
        else:
            color = (200, 200, 255)
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 120)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            particle = Particle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                color=color,
                size=random.uniform(2, 4),
                lifetime=random.uniform(0.4, 0.8),
                gravity=50.0,
                fade_out=True,
            )
            self.particles.append(particle)
    
    def add_movement_trail(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        color: Tuple[int, int, int] = (150, 200, 255),
        duration: float = 0.5,
    ) -> None:
        """Add a movement trail effect."""
        self.movement_trails.append({
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "color": color,
            "timer": duration,
            "max_timer": duration,
        })
    
    def set_health_bar_target(self, unit: object, target_ratio: float) -> None:
        """Set target health ratio for smooth animation."""
        unit_id = id(unit)
        self.health_bar_targets[unit_id] = max(0.0, min(1.0, target_ratio))
        if unit_id not in self.health_bar_current:
            self.health_bar_current[unit_id] = target_ratio
    
    def get_health_bar_ratio(self, unit: object) -> float:
        """Get current animated health bar ratio."""
        unit_id = id(unit)
        return self.health_bar_current.get(unit_id, 1.0)
    
    def update(self, dt: float) -> None:
        """Update all visual effects."""
        # Update screen shake
        if self.shake_duration > 0:
            self.shake_duration -= dt
            if self.shake_duration > 0:
                # Random shake offset
                self.shake_offset_x = random.uniform(-self.shake_intensity, self.shake_intensity)
                self.shake_offset_y = random.uniform(-self.shake_intensity, self.shake_intensity)
                # Decay intensity over time
                self.shake_intensity *= 0.9
            else:
                self.shake_intensity = 0.0
                self.shake_offset_x = 0.0
                self.shake_offset_y = 0.0
        
        # Update screen flash
        if self.flash_duration > 0:
            self.flash_duration -= dt
            if self.flash_duration <= 0:
                self.flash_color = None
                self.flash_alpha = 0.0
        
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Update health bar animations (smooth interpolation)
        for unit_id, target_ratio in self.health_bar_targets.items():
            current = self.health_bar_current.get(unit_id, target_ratio)
            if abs(current - target_ratio) > 0.01:
                # Smooth interpolation
                speed = 5.0  # Animation speed
                diff = target_ratio - current
                self.health_bar_current[unit_id] = current + diff * min(1.0, speed * dt)
            else:
                self.health_bar_current[unit_id] = target_ratio
        
        # Update movement trails
        for trail in self.movement_trails[:]:
            trail["timer"] -= dt
            if trail["timer"] <= 0:
                self.movement_trails.remove(trail)
    
    def get_shake_offset(self) -> Tuple[float, float]:
        """Get current screen shake offset."""
        return (self.shake_offset_x, self.shake_offset_y)
    
    def draw_particles(self, surface: pygame.Surface) -> None:
        """Draw all particles."""
        for particle in self.particles:
            alpha = particle.get_alpha()
            if alpha <= 0:
                continue
            
            # Create colored surface with alpha
            color_with_alpha = (*particle.color, alpha)
            size = max(1, int(particle.size))
            
            # Draw particle as a circle
            particle_surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(
                particle_surf,
                color_with_alpha,
                (size + 1, size + 1),
                size,
            )
            surface.blit(particle_surf, (int(particle.x) - size - 1, int(particle.y) - size - 1))
    
    def draw_movement_trails(self, surface: pygame.Surface) -> None:
        """Draw movement trail effects."""
        for trail in self.movement_trails:
            progress = 1.0 - (trail["timer"] / trail["max_timer"])
            alpha = int(255 * (1.0 - progress))  # Fade out
            
            # Interpolate position
            x = trail["start_x"] + (trail["end_x"] - trail["start_x"]) * progress
            y = trail["start_y"] + (trail["end_y"] - trail["start_y"]) * progress
            
            # Draw trail line
            color_with_alpha = (*trail["color"], alpha)
            trail_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, color_with_alpha, (10, 10), 8)
            surface.blit(trail_surf, (int(x) - 10, int(y) - 10))
    
    def draw_screen_flash(self, surface: pygame.Surface) -> None:
        """Draw screen flash overlay."""
        if self.flash_color is None or self.flash_alpha <= 0:
            return
        
        # Calculate current flash alpha
        if self.flash_duration > 0:
            # Fade out over duration
            current_alpha = int(self.flash_alpha * (self.flash_duration / 0.15))
        else:
            current_alpha = 0
        
        if current_alpha > 0:
            flash_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash_surf.fill((*self.flash_color, current_alpha))
            surface.blit(flash_surf, (0, 0))
    
    def clear(self) -> None:
        """Clear all effects."""
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0
        self.flash_color = None
        self.flash_alpha = 0.0
        self.flash_duration = 0.0
        self.particles.clear()
        self.movement_trails.clear()
        self.health_bar_targets.clear()
        self.health_bar_current.clear()

