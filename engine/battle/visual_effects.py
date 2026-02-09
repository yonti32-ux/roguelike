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


class OrbitalGlow:
    """An orbital glow effect that rotates around a point."""
    
    def __init__(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (100, 150, 255),
        radius: float = 30.0,
        num_orbs: int = 3,
        lifetime: float = 1.5,
        rotation_speed: float = 3.0,
    ):
        self.x = x
        self.y = y
        self.color = color
        self.radius = radius
        self.num_orbs = num_orbs
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.rotation_speed = rotation_speed
        self.angle = 0.0
    
    def update(self, dt: float) -> bool:
        """Update orbital glow. Returns False if effect should be removed."""
        self.angle += self.rotation_speed * dt
        self.lifetime -= dt
        return self.lifetime > 0
    
    def get_alpha(self) -> int:
        """Get alpha value based on remaining lifetime."""
        ratio = self.lifetime / self.max_lifetime if self.max_lifetime > 0 else 0.0
        # Fade in quickly, fade out slowly
        if ratio > 0.3:
            alpha_ratio = 1.0 - ((1.0 - ratio) / 0.7)
        else:
            alpha_ratio = ratio / 0.3
        return int(255 * max(0.0, min(1.0, alpha_ratio)))


class AuraEffect:
    """A pulsing aura effect around a point."""
    
    def __init__(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (255, 255, 255),
        base_radius: float = 20.0,
        pulse_amount: float = 10.0,
        lifetime: float = 1.0,
        pulse_speed: float = 5.0,
    ):
        self.x = x
        self.y = y
        self.color = color
        self.base_radius = base_radius
        self.pulse_amount = pulse_amount
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.pulse_speed = pulse_speed
        self.pulse_time = 0.0
    
    def update(self, dt: float) -> bool:
        """Update aura effect. Returns False if effect should be removed."""
        self.pulse_time += dt * self.pulse_speed
        self.lifetime -= dt
        return self.lifetime > 0
    
    def get_radius(self) -> float:
        """Get current radius with pulse effect."""
        pulse = math.sin(self.pulse_time) * self.pulse_amount
        return self.base_radius + pulse
    
    def get_alpha(self) -> int:
        """Get alpha value based on remaining lifetime."""
        ratio = self.lifetime / self.max_lifetime if self.max_lifetime > 0 else 0.0
        return int(180 * ratio)  # Max alpha of 180 for subtle effect


class ShockwaveEffect:
    """A shockwave effect expanding outward."""
    
    def __init__(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (255, 200, 100),
        max_radius: float = 60.0,
        lifetime: float = 0.6,
        speed: float = 100.0,
    ):
        self.x = x
        self.y = y
        self.color = color
        self.max_radius = max_radius
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.speed = speed
        self.current_radius = 0.0
    
    def update(self, dt: float) -> bool:
        """Update shockwave effect. Returns False if effect should be removed."""
        self.current_radius += self.speed * dt
        self.lifetime -= dt
        return self.lifetime > 0 and self.current_radius < self.max_radius
    
    def get_alpha(self) -> int:
        """Get alpha value based on radius progress."""
        if self.max_radius <= 0:
            return 0
        progress = self.current_radius / self.max_radius
        # Fade out as it expands
        return int(200 * (1.0 - progress))


class ShieldBarrierEffect:
    """
    A shield-barrier effect for the Guard skill: a shield shape that raises
    in front of the unit, then holds and fades. Distinct from orbital orbs.
    """
    
    def __init__(
        self,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (80, 140, 220),
        size: float = 28.0,
        lifetime: float = 1.2,
        raise_time: float = 0.2,
    ):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.raise_time = raise_time
        self.elapsed = 0.0
    
    def update(self, dt: float) -> bool:
        """Update shield barrier. Returns False if effect should be removed."""
        self.elapsed += dt
        self.lifetime -= dt
        return self.lifetime > 0
    
    def get_scale(self) -> float:
        """Scale from 0 to 1 during raise, then 1."""
        if self.raise_time <= 0:
            return 1.0
        if self.elapsed >= self.raise_time:
            return 1.0
        return self.elapsed / self.raise_time
    
    def get_alpha(self) -> int:
        """Fade in during raise, hold, then fade out in last 40% of lifetime."""
        ratio = self.lifetime / self.max_lifetime if self.max_lifetime > 0 else 0.0
        if ratio > 0.6:
            return 220  # Full visibility after raise
        if ratio > 0.2:
            # Linear fade out in middle segment
            return int(220 * (ratio - 0.2) / 0.4)
        return int(220 * ratio / 0.2)  # Fade out at end


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
        
        # Skill effects (orbital glows, auras, shockwaves, shield barriers)
        self.orbital_glows: List[OrbitalGlow] = []
        self.auras: List[AuraEffect] = []
        self.shockwaves: List[ShockwaveEffect] = []
        self.shield_barriers: List[ShieldBarrierEffect] = []
    
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
        """Add skill visual effects based on skill type (replaces old particle system)."""
        # Map skill IDs to effect types
        skill_effect_map = {
            # Guard - dedicated shield barrier (distinct from other defensive skills)
            "guard": "shield_barrier",
            # Defensive skills - orbital glow
            "nimble_step": "orbital_glow_green",
            "shield_wall": "orbital_glow_blue",
            "magic_shield": "orbital_glow_purple",
            "evade": "orbital_glow_yellow",
            
            # Offensive melee skills - shockwave
            "power_strike": "shockwave_orange",
            "lunge": "shockwave_red",
            "shield_bash": "shockwave_blue",
            "backstab": "shockwave_dark",
            "shadow_strike": "shockwave_purple",
            "charge": "shockwave_orange",
            "crippling_blow": "shockwave_red",
            "heavy_slam": "shockwave_brown",
            
            # AoE skills - larger shockwave
            "cleave": "shockwave_large_orange",
            "whirlwind": "shockwave_large_red",
            "ground_slam": "shockwave_large_brown",
            "fireball": "shockwave_large_fire",
            "lightning_bolt": "shockwave_large_lightning",
            "frost_nova": "shockwave_large_ice",
            "meteor_strike": "shockwave_large_fire",
            "blizzard": "shockwave_large_ice",
            
            # Magic/ranged skills - aura
            "focus_blast": "aura_purple",
            "arcane_missile": "aura_blue",
            "ice_bolt": "aura_cyan",
            "chain_lightning": "aura_yellow",
            "shadow_bolt": "aura_dark",
            "fireball": "aura_fire",  # Can have both shockwave and aura
            
            # Healing/support - aura
            "heal_ally": "aura_green",
            "second_wind": "aura_green",
            "regeneration": "aura_green",
            
            # Buffs - aura
            "war_cry": "aura_red",
            "berserker_rage": "aura_red",
            "buff_ally": "aura_yellow",
            
            # Debuffs/DoT - aura
            "poison_strike": "aura_green_dark",
            "poison_blade": "aura_green_dark",
            "dark_hex": "aura_purple_dark",
            "feral_claws": "aura_red_dark",
            "disease_strike": "aura_dark",
            "mark_target": "aura_dark",
            "slow": "aura_cyan",
            "taunt": "aura_orange",
            "fear_scream": "aura_dark",
        }
        
        effect_type = skill_effect_map.get(skill_type, "shockwave_default")
        
        # Create appropriate effect based on type
        if effect_type == "shield_barrier":
            barrier = ShieldBarrierEffect(
                x=x,
                y=y,
                color=(80, 140, 220),
                size=28.0,
                lifetime=1.2,
                raise_time=0.2,
            )
            self.shield_barriers.append(barrier)
        elif effect_type.startswith("orbital_glow"):
            color_map = {
                "orbital_glow_blue": (100, 150, 255),
                "orbital_glow_green": (100, 255, 150),
                "orbital_glow_purple": (200, 100, 255),
                "orbital_glow_yellow": (255, 255, 150),
            }
            color = color_map.get(effect_type, (100, 150, 255))
            glow = OrbitalGlow(
                x=x,
                y=y,
                color=color,
                radius=35.0,
                num_orbs=3,
                lifetime=1.5,
                rotation_speed=3.0,
            )
            self.orbital_glows.append(glow)
            
        elif effect_type.startswith("shockwave"):
            color_map = {
                "shockwave_orange": (255, 150, 50),
                "shockwave_red": (255, 100, 100),
                "shockwave_blue": (100, 150, 255),
                "shockwave_dark": (80, 80, 100),
                "shockwave_purple": (200, 100, 255),
                "shockwave_brown": (150, 100, 50),
                "shockwave_large_orange": (255, 150, 50),
                "shockwave_large_red": (255, 100, 100),
                "shockwave_large_brown": (150, 100, 50),
                "shockwave_large_fire": (255, 100, 50),
                "shockwave_large_lightning": (200, 200, 255),
                "shockwave_large_ice": (150, 200, 255),
                "shockwave_default": (200, 200, 255),
            }
            color = color_map.get(effect_type, (200, 200, 255))
            is_large = "large" in effect_type
            shockwave = ShockwaveEffect(
                x=x,
                y=y,
                color=color,
                max_radius=80.0 if is_large else 50.0,
                lifetime=0.8 if is_large else 0.6,
                speed=120.0 if is_large else 100.0,
            )
            self.shockwaves.append(shockwave)
            
        elif effect_type.startswith("aura"):
            color_map = {
                "aura_purple": (200, 100, 255),
                "aura_blue": (100, 150, 255),
                "aura_cyan": (100, 255, 255),
                "aura_yellow": (255, 255, 150),
                "aura_dark": (100, 80, 120),
                "aura_fire": (255, 150, 50),
                "aura_green": (100, 255, 150),
                "aura_green_dark": (50, 150, 50),
                "aura_red": (255, 100, 100),
                "aura_red_dark": (150, 50, 50),
                "aura_purple_dark": (150, 50, 200),
                "aura_orange": (255, 150, 50),
            }
            color = color_map.get(effect_type, (200, 200, 255))
            aura = AuraEffect(
                x=x,
                y=y,
                color=color,
                base_radius=25.0,
                pulse_amount=8.0,
                lifetime=1.2,
                pulse_speed=6.0,
            )
            self.auras.append(aura)
    
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
        
        # Update skill effects
        self.orbital_glows = [g for g in self.orbital_glows if g.update(dt)]
        self.auras = [a for a in self.auras if a.update(dt)]
        self.shockwaves = [s for s in self.shockwaves if s.update(dt)]
        self.shield_barriers = [b for b in self.shield_barriers if b.update(dt)]
    
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
    
    def draw_skill_effects(self, surface: pygame.Surface) -> None:
        """Draw all skill visual effects (orbital glows, auras, shockwaves, shield barriers)."""
        # Draw shield barriers (Guard skill) - distinct shield shape that raises and fades
        for barrier in self.shield_barriers:
            alpha = barrier.get_alpha()
            if alpha <= 0:
                continue
            scale = barrier.get_scale()
            s = barrier.size * scale
            cx, cy = int(barrier.x), int(barrier.y)
            # Shield polygon in local coords (centered); then we offset by (cx, cy)
            local_points = [
                (0, -s),
                (-s, -s * 0.4),
                (-s, s * 0.4),
                (0, s),
                (s, s * 0.4),
                (s, -s * 0.4),
            ]
            w = int(s * 2.5)
            h = int(s * 2.5)
            barrier_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            ox, oy = w // 2, h // 2
            screen_points = [(ox + int(p[0]), oy + int(p[1])) for p in local_points]
            color_with_alpha = (*barrier.color, alpha)
            outline_rgba = (min(255, barrier.color[0] + 60), min(255, barrier.color[1] + 70), min(255, barrier.color[2] + 50), alpha)
            pygame.draw.polygon(barrier_surf, color_with_alpha, screen_points)
            pygame.draw.polygon(barrier_surf, outline_rgba, screen_points, width=2)
            surface.blit(barrier_surf, (cx - w // 2, cy - h // 2))
        # Draw orbital glows
        for glow in self.orbital_glows:
            alpha = glow.get_alpha()
            if alpha <= 0:
                continue
            
            color_with_alpha = (*glow.color, alpha)
            angle_step = (2 * math.pi) / glow.num_orbs
            
            for i in range(glow.num_orbs):
                orb_angle = glow.angle + (i * angle_step)
                orb_x = glow.x + math.cos(orb_angle) * glow.radius
                orb_y = glow.y + math.sin(orb_angle) * glow.radius
                
                # Draw glowing orb
                orb_size = 8
                orb_surf = pygame.Surface((orb_size * 2 + 4, orb_size * 2 + 4), pygame.SRCALPHA)
                # Outer glow
                pygame.draw.circle(
                    orb_surf,
                    color_with_alpha,
                    (orb_size + 2, orb_size + 2),
                    orb_size + 2,
                )
                # Inner bright core
                core_alpha = min(255, alpha + 50)
                core_color = (*glow.color, core_alpha)
                pygame.draw.circle(
                    orb_surf,
                    core_color,
                    (orb_size + 2, orb_size + 2),
                    orb_size // 2,
                )
                surface.blit(orb_surf, (int(orb_x) - orb_size - 2, int(orb_y) - orb_size - 2))
        
        # Draw auras
        for aura in self.auras:
            alpha = aura.get_alpha()
            if alpha <= 0:
                continue
            
            radius = aura.get_radius()
            color_with_alpha = (*aura.color, alpha)
            
            # Draw pulsing circle
            aura_surf = pygame.Surface((int(radius * 2 + 4), int(radius * 2 + 4)), pygame.SRCALPHA)
            pygame.draw.circle(
                aura_surf,
                color_with_alpha,
                (int(radius + 2), int(radius + 2)),
                int(radius),
                width=3,
            )
            # Inner glow
            inner_alpha = alpha // 2
            inner_color = (*aura.color, inner_alpha)
            pygame.draw.circle(
                aura_surf,
                inner_color,
                (int(radius + 2), int(radius + 2)),
                int(radius * 0.6),
            )
            surface.blit(aura_surf, (int(aura.x) - int(radius) - 2, int(aura.y) - int(radius) - 2))
        
        # Draw shockwaves
        for shockwave in self.shockwaves:
            alpha = shockwave.get_alpha()
            if alpha <= 0:
                continue
            
            radius = shockwave.current_radius
            color_with_alpha = (*shockwave.color, alpha)
            
            # Draw expanding circle
            shockwave_surf = pygame.Surface((int(radius * 2 + 4), int(radius * 2 + 4)), pygame.SRCALPHA)
            pygame.draw.circle(
                shockwave_surf,
                color_with_alpha,
                (int(radius + 2), int(radius + 2)),
                int(radius),
                width=2,
            )
            surface.blit(shockwave_surf, (int(shockwave.x) - int(radius) - 2, int(shockwave.y) - int(radius) - 2))
    
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
        self.orbital_glows.clear()
        self.auras.clear()
        self.shockwaves.clear()
        self.shield_barriers.clear()

