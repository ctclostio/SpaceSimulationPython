"""
constants.py - Contains all constants and configuration parameters

This module stores all the numerical values and configuration settings used
throughout the simulation. This includes:
- Celestial body sizes
- Orbital parameters
- Physical constants
- Configuration settings
"""

# Celestial body radii (relative to Earth's radius)
SUN_RADIUS = 20.0  # Increased size
MERCURY_RADIUS = 1.0  # Increased size
VENUS_RADIUS = 1.5  # Increased size
EARTH_RADIUS = 2.0  # Increased size
MARS_RADIUS = 1.2  # Increased size
JUPITER_RADIUS = 15.0  # Increased size
SATURN_RADIUS = 12.0  # Increased size
URANUS_RADIUS = 6.0  # Increased size
NEPTUNE_RADIUS = 5.5  # Increased size

# Orbital parameters
# Distances in AU (scaled), speeds calculated for periods
MERCURY_ORBIT_RADIUS = 11.7  # 0.39 AU * 30 (scale factor)
MERCURY_ORBIT_SPEED = 25.0   # 360° / 14.4s
VENUS_ORBIT_RADIUS = 21.6    # 0.72 AU * 30
VENUS_ORBIT_SPEED = 9.68     # 360° / 37.2s
EARTH_ORBIT_RADIUS = 30.0    # 1.00 AU * 30 (base scale)
EARTH_ORBIT_SPEED = 6.0      # 360° / 60s
MARS_ORBIT_RADIUS = 45.6     # 1.52 AU * 30
MARS_ORBIT_SPEED = 3.19      # 360° / 112.8s
JUPITER_ORBIT_RADIUS = 156.0  # 5.20 AU * 30
JUPITER_ORBIT_SPEED = 0.506   # 360° / 711.6s
SATURN_ORBIT_RADIUS = 287.4   # 9.58 AU * 30
SATURN_ORBIT_SPEED = 0.204    # 360° / 1767.6s
URANUS_ORBIT_RADIUS = 576.6   # 19.22 AU * 30
URANUS_ORBIT_SPEED = 0.071    # 360° / 5040.6s
NEPTUNE_ORBIT_RADIUS = 901.5  # 30.05 AU * 30
NEPTUNE_ORBIT_SPEED = 0.036   # 360° / 9887.4s

# Rotation speeds (degrees per second)
SUN_ROTATION_SPEED = 0.1
MERCURY_ROTATION_SPEED = 0.04
VENUS_ROTATION_SPEED = -0.02  # Venus rotates backwards
EARTH_ROTATION_SPEED = 1.0
MARS_ROTATION_SPEED = 0.97
JUPITER_ROTATION_SPEED = 2.4
SATURN_ROTATION_SPEED = 2.3
URANUS_ROTATION_SPEED = -1.4  # Uranus rotates on its side
NEPTUNE_ROTATION_SPEED = 1.5

# Texture paths
SUN_TEXTURE = "textures/2k_sun.jpg"
MERCURY_TEXTURE = "textures/2k_mercury.jpg"
VENUS_TEXTURE = "textures/2k_venus_surface.jpg"  # Using surface texture for Venus
EARTH_TEXTURE = "textures/2k_earth_daymap.jpg"
MARS_TEXTURE = "textures/2k_mars.jpg"
JUPITER_TEXTURE = "textures/2k_jupiter.jpg"
SATURN_TEXTURE = "textures/2k_saturn.jpg"
URANUS_TEXTURE = "textures/2k_uranus.jpg"
NEPTUNE_TEXTURE = "textures/2k_neptune.jpg"

# Camera settings
CAMERA_DISTANCE = 100
CAMERA_HEIGHT = 50

# Lighting settings
LIGHT_DIRECTION = (1, -1, -1)

# Simulation settings
TIME_SCALE = 1.0  # Set to 1.0 to maintain Earth's 60-second orbital period

# Orbital periods (in seconds) for reference:
# Mercury: 14.4
# Venus: 37.2
# Earth: 60.0
# Mars: 112.8
# Jupiter: 711.6
# Saturn: 1767.6
# Uranus: 5040.6
# Neptune: 9887.4