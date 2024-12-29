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
    def __init__(self, name, radius, texture, rotation_speed, **kwargs):
        """
        Initialize a celestial body
        
        Args:
            name (str): Name of the celestial body
            radius (float): Radius of the body
            texture (str): Path to texture file
            rotation_speed (float): Rotation speed in degrees per second
        """
        # Create a higher-poly sphere model with triple the subdivisions
        from assets_manager import AssetsManager
        assets_manager = AssetsManager()
        
        super().__init__(
            model='sphere',
            texture=assets_manager.get_texture(texture),
            scale=radius * 2,
            subdivisions=kwargs.pop('subdivisions', 3),
            **kwargs
        )
        self.name = name
        self.rotation_speed = rotation_speed
        self.position_lock = Lock()
        
    def update_rotation(self):
        """Update rotation each frame using consistent time tracking"""
        current_time = time.time()
        if not hasattr(self, '_last_rotation_update'):
            self._last_rotation_update = current_time
            return
            
        dt = current_time - self._last_rotation_update
        self._last_rotation_update = current_time
        
        self.rotation_y += self.rotation_speed * dt

    def update(self):
        """Default update method - just updates rotation"""
        self.update_rotation()

class Star(CelestialBody):
    """Class representing stars (e.g., the Sun)"""
    def __init__(self, name, radius, texture, rotation_speed, light_manager=None):
        """
        Initialize a star
        
        Args:
            name (str): Name of the star
            radius (float): Radius of the star
            texture (str): Path to texture file
            rotation_speed (float): Rotation speed in degrees per second
            light_manager (LightManager, optional): Light manager instance for handling lighting
        """
        super().__init__(
            name=name,
            radius=radius,
            texture=texture,
            rotation_speed=rotation_speed,
            subdivisions=8
        )
        # Add emissive material for stars
        self.color = color.yellow
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
                self.light.color = color.rgb(255, 253, 208)  # Warm sunlight color
                self.light.intensity = 2.0  # High intensity for star light

class Planet(CelestialBody):
    """Class representing planets"""
    def __init__(self, name, radius, texture, orbit_radius, orbit_speed, rotation_speed):
        """
        Initialize a planet
        
        Args:
            name (str): Name of the planet
            radius (float): Radius of the planet
            texture (str): Path to texture file
            orbit_radius (float): Distance from the star
            orbit_speed (float): Orbital speed in degrees per second
            rotation_speed (float): Rotation speed in degrees per second
        """
        super().__init__(
            name=name,
            radius=radius,
            texture=texture,
            rotation_speed=rotation_speed,
            subdivisions=6
        )
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.orbit_angle = 0
        self.is_clickable = True  # Mark the planet as clickable
        
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
            
    def update(self):
        """Update only rotation - position is handled by ThreadedOrbitController"""
        self.update_rotation()