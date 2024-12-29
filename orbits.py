"""
orbits.py - Contains orbital mechanics calculations and transformations

This module provides functions and classes for managing orbital mechanics in the
simulation. It includes:
- Orbital position calculations
- Velocity calculations
- Coordinate transformations
"""

import math
from ursina import Vec3
from constants import *

def calculate_orbit_position(orbit_radius, angle):
    """
    Calculate the position of an object in a circular orbit
    
    Args:
        orbit_radius (float): Radius of the orbit
        angle (float): Current angle in degrees
        
    Returns:
        Vec3: Position in 3D space
    """
    rad = math.radians(angle)
    return Vec3(
        math.cos(rad) * orbit_radius,
        0,
        math.sin(rad) * orbit_radius
    )

def calculate_orbital_velocity(orbit_radius, orbital_period):
    """
    Calculate orbital velocity based on orbit radius and period
    
    Args:
        orbit_radius (float): Radius of the orbit
        orbital_period (float): Time for one complete orbit (in seconds)
        
    Returns:
        float: Orbital speed in degrees per second
    """
    if orbital_period == 0:
        return 0
    return 360 / orbital_period

class OrbitController:
    """Manages orbital mechanics for multiple bodies"""
    def __init__(self):
        self.bodies = []

    def add_body(self, body):
        """Add a celestial body to be managed"""
        self.bodies.append(body)

    def update(self):
        """Update orbital positions for all managed bodies"""
        for body in self.bodies:
            body.update_orbit()