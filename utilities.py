"""
utilities.py - Contains helper functions and utility methods

This module provides various utility functions that can be used throughout
the simulation. These include:
- Math helper functions
- Color manipulation
- General utility functions
"""

import math
from ursina import Vec3, color

def lerp(a, b, t):
    """
    Linear interpolation between two values
    
    Args:
        a (float): Start value
        b (float): End value
        t (float): Interpolation factor (0-1)
        
    Returns:
        float: Interpolated value
    """
    return a + (b - a) * t

def clamp(value, min_val, max_val):
    """
    Clamp a value between a minimum and maximum
    
    Args:
        value (float): Value to clamp
        min_val (float): Minimum value
        max_val (float): Maximum value
        
    Returns:
        float: Clamped value
    """
    return max(min_val, min(value, max_val))

def calculate_distance(point1, point2):
    """
    Calculate the distance between two points in 3D space
    
    Args:
        point1 (Vec3): First point
        point2 (Vec3): Second point
        
    Returns:
        float: Distance between the points
    """
    return (point2 - point1).length()

def generate_random_color():
    """
    Generate a random color
    
    Returns:
        Color: Random color
    """
    return color.random_color()

def degrees_to_radians(degrees):
    """
    Convert degrees to radians
    
    Args:
        degrees (float): Angle in degrees
        
    Returns:
        float: Angle in radians
    """
    return degrees * (math.pi / 180)