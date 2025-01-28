"""
celestial_bodies.py - Contains classes for celestial bodies

This module defines the base CelestialBody class and specialized classes for
different types of celestial bodies (Star, Planet, Moon).

Classes:
    CelestialBody: Base class for all celestial bodies
    Star: Represents stars (e.g., the Sun)
    Planet: Represents planets
    Moon: Represents moons (optional)
"""

from ursina import *
from ursina import Mesh
from constants import *
from threading import Lock

class CelestialBody(Entity):
    """Base class for all celestial bodies"""
    def __init__(self, name, radius, color, rotation_speed, buffer_manager=None, **kwargs):
        """
        Initialize a celestial body
        
        Args:
            name (str): Name of the celestial body
            radius (float): Radius of the body
            color (color): Color of the body
            rotation_speed (float): Rotation speed in degrees per second
            buffer_manager (BufferManager): Position buffer system manager
        """
        super().__init__(
            model='icosphere',
            color=color,
            scale=radius * 2,
            subdivisions=kwargs.pop('subdivisions', 1),
            **kwargs
        )
        self.name = name
        self.rotation_speed = rotation_speed
        self.buffer_manager = buffer_manager
        if buffer_manager:
            self.buffer_manager.register_entity(self.name)
        
    def update_rotation(self):
        """Update rotation each frame using consistent time tracking"""
        self.rotation_y += self.rotation_speed * time.dt
        
    def update(self):
        """Default update method - just updates rotation"""
        self.update_orbit()

    def update_orbit(self):
        """Update the orbital position of the celestial body"""
        pass  # To be implemented in subclasses


class Star(CelestialBody):
    """Class representing stars (e.g., the Sun)"""
    def __init__(self, name, radius, color, rotation_speed, light_manager=None, **kwargs):
        """
        Initialize a star
        
        Args:
            name (str): Name of the star
            radius (float): Radius of the star
            color (color): Color of the star
            rotation_speed (float): Rotation speed in degrees per second
            light_manager (LightManager, optional): Light manager instance for handling lighting
            **kwargs: Additional arguments passed to parent Entity class
        """
        super().__init__(
            name=name,
            radius=radius,
            color=color,
            rotation_speed=rotation_speed,
            subdivisions=2,
            **kwargs
        )
        self.shader = 'lit_with_shadows_shader'  # Using built-in Ursina shader
        
        # Add sunlight for star illumination
        if light_manager:
            # Create sunlight with directional illumination
            self.light = light_manager.add_sun_light(
                direction=Vec3(1, -1, -1),  # Default sunlight direction
                shadows=True  # Enable shadows for realism
            )
            if self.light:
                light_manager.attach_to_entity(self.light, self)
                # Configure sunlight properties
                self.light.color = self.color  # Warm sunlight color
                self.light.intensity = 2.0  # High intensity for star light

    def update(self):
        """Update the star's rotation."""
        self.update_rotation()

class Planet(CelestialBody):
    """Class representing planets"""
    def __init__(self, name, radius, color, orbit_radius, orbit_speed, rotation_speed, **kwargs):
        """
        Initialize a planet
        
        Args:
            name (str): Name of the planet
            radius (float): Radius of the planet
            color (color): Color of the planet
            orbit_radius (float): Distance from the star
            orbit_speed (float): Orbital speed in degrees per second
            rotation_speed (float): Rotation speed in degrees per second
            **kwargs: Additional keyword arguments passed to the CelestialBody
        """
        super().__init__(
            name=name,
            radius=radius,
            color=color,
            rotation_speed=rotation_speed,
            subdivisions=2,
            **kwargs
        )
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.orbit_angle = 0
        self.is_clickable = True
        
    def set_position_threaded(self, new_position):
        """
        Thread-safe method to update the planet's position
        
        Args:
            new_position (Vec3): New position for the planet
        """
        with self.position_lock:
            self.position = new_position
            
    def get_position_threaded(self):
        """
        Thread-safe method to get the planet's position
        
        Returns:
            Vec3: Current position of the planet
        """
        with self.position_lock:
            return self.position.copy()
        
    def update_orbit(self):
        """Update the planet's position based on its orbit"""
        if hasattr(self, '_frame_dt'):
            dt = self._frame_dt
        else:
            dt = time.dt
            
        self.orbit_angle = (self.orbit_angle + self.orbit_speed * dt) % 360
        orbit_pos = calculate_orbit_position(self.orbit_radius, self.orbit_angle)
        self.position = orbit_pos
        
        # Only update rotation if position changed significantly
        if (orbit_pos - self.position).length() > 0.1:
            self.position = orbit_pos

    def update(self):
        """Update only rotation - position is handled by ThreadedOrbitController"""
