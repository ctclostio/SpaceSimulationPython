"""
game_manager.py - Manages the overall game state and simulation

This module contains the GameManager class which handles:
- Scene setup and initialization
- Celestial body creation
- Camera and lighting configuration
- Main game loop updates
- Thread management for async operations
"""

from ursina import *
from celestial_bodies import Star, Planet
from constants import *
from camera import CameraManager
from selector import Selector
from light_manager import LightManager
from thread_manager import ThreadManager
from orbits_threaded import ThreadedOrbitController
from assets_loader import ThreadedAssetsManager
from orbits import calculate_orbit_position

class GameManager:
    def __init__(self):
        """Initialize the game environment and setup the scene"""
        # Initialize thread manager first
        self.thread_manager = ThreadManager()
        
        # Initialize threaded components
        self.assets_manager = ThreadedAssetsManager()
        self.assets_manager.setup_threading(self.thread_manager)
        self.orbit_controller = ThreadedOrbitController(self.thread_manager)
        
        # Setup scene and create bodies
        self.setup_scene()
        self.create_celestial_bodies()
        self.selector = Selector()

        # Register planets as clickable and for orbital calculations
        for planet in self.planets:
            self.selector.register_clickable(planet)
            self.orbit_controller.add_body(planet)
        
        # Start all threads
        self.thread_manager.start_threads()
        
        # Track the sun with the camera
        self.camera_manager.tracker.track_body(self.sun)
        
    def setup_scene(self):
        """Configure the scene with lighting and camera settings"""
        # Initialize light manager
        self.light_manager = LightManager(max_lights=8)
        
        # Add ambient light for better scene visibility
        self.ambient_light = self.light_manager.add_ambient_light(
            color=color.rgba(0.1, 0.1, 0.2, 1.0),
            intensity=0.3  # Slightly increased for better visibility
        )
        
        # Initialize camera manager
        self.camera_manager = CameraManager()
        
    def create_celestial_bodies(self):
        """Create and position all celestial bodies in the scene"""
        # Create the Sun with its own light source
        self.sun = Star(
            name="Sun",
            radius=SUN_RADIUS,
            color=color.rgb(255, 253, 208),  # Yellowish-white color for the Sun
            rotation_speed=SUN_ROTATION_SPEED,
            light_manager=self.light_manager,
            texture="sun"
        )
        
        print("\nInitializing planets...")
        # Create all planets using modular data structure
        planet_data = [
            {
                'name': 'Mercury',
                'radius': MERCURY_RADIUS,
                'texture': 'mercury',
                'orbit_radius': MERCURY_ORBIT_RADIUS,
                'orbit_speed': MERCURY_ORBIT_SPEED,
                'rotation_speed': MERCURY_ROTATION_SPEED,
                'start_angle': 0,
                'color': color.gray
            },
            {
                'name': 'Venus',
                'radius': VENUS_RADIUS,
                'texture': 'venus',
                'orbit_radius': VENUS_ORBIT_RADIUS,
                'orbit_speed': VENUS_ORBIT_SPEED,
                'rotation_speed': VENUS_ROTATION_SPEED,
                'start_angle': 45,
                'color': color.orange
            },
            {
                'name': 'Earth',
                'radius': EARTH_RADIUS,
                'texture': 'earth',
                'orbit_radius': EARTH_ORBIT_RADIUS,
                'orbit_speed': EARTH_ORBIT_SPEED,
                'rotation_speed': EARTH_ROTATION_SPEED,
                'start_angle': 90,
                'color': color.blue
            },
            {
                'name': 'Mars',
                'radius': MARS_RADIUS,
                'texture': 'mars',
                'orbit_radius': MARS_ORBIT_RADIUS,
                'orbit_speed': MARS_ORBIT_SPEED,
                'rotation_speed': MARS_ROTATION_SPEED,
                'start_angle': 135,
                'color': color.red
            },
            {
                'name': 'Jupiter',
                'radius': JUPITER_RADIUS,
                'texture': 'jupiter',
                'orbit_radius': JUPITER_ORBIT_RADIUS,
                'orbit_speed': JUPITER_ORBIT_SPEED,
                'rotation_speed': JUPITER_ROTATION_SPEED,
                'start_angle': 180,
                'color': color.orange
            },
            {
                'name': 'Saturn',
                'radius': SATURN_RADIUS,
                'texture': 'saturn',
                'orbit_radius': SATURN_ORBIT_RADIUS,
                'orbit_speed': SATURN_ORBIT_SPEED,
                'rotation_speed': SATURN_ROTATION_SPEED,
                'start_angle': 225,
                'color': color.yellow
            },
            {
                'name': 'Uranus',
                'radius': URANUS_RADIUS,
                'texture': 'uranus',
                'orbit_radius': URANUS_ORBIT_RADIUS,
                'orbit_speed': URANUS_ORBIT_SPEED,
                'rotation_speed': URANUS_ROTATION_SPEED,
                'start_angle': 270,
                'color': color.cyan
            },
            {
                'name': 'Neptune',
                'radius': NEPTUNE_RADIUS,
                'texture': 'neptune',
                'orbit_radius': NEPTUNE_ORBIT_RADIUS,
                'orbit_speed': NEPTUNE_ORBIT_SPEED,
                'rotation_speed': NEPTUNE_ROTATION_SPEED,
                'start_angle': 315,
                'color': color.blue
            }
        ]
        
        self.planets = []
        for data in planet_data:
            planet = Planet(
                name=data['name'],
                radius=data['radius'],
                color=data['color'],
                orbit_radius=data['orbit_radius'],
                orbit_speed=data['orbit_speed'],
                rotation_speed=data['rotation_speed'],
                texture=data['texture']
            )
            planet.position = calculate_orbit_position(data['orbit_radius'], data['start_angle'])
            self.planets.append(planet)
        
        # Print debug info for created planets
        for planet in self.planets:
            print(f"Created planet: {planet.name}, Orbit radius: {planet.orbit_radius}")
        
    def update(self):
        """Update method called every frame"""
        # Calculate frame delta time
        current_time = time.time()
        if not hasattr(self, '_last_frame_time'):
            self._last_frame_time = current_time
        frame_dt = current_time - self._last_frame_time
        self._last_frame_time = current_time
        
        # Pass frame delta time to celestial bodies
        for planet in self.planets:
            planet._frame_dt = frame_dt
            
        # Update threaded components
        self.assets_manager.update()  # Update with any newly loaded textures
        self.orbit_controller.update()  # Update orbital positions
        
        # Update sun rotation
        self.sun.update()
        
        # Update celestial body rotations (positions are handled by orbit_controller)
        for planet in self.planets:
            planet.update_rotation()
            
        # Update camera controls
        self.camera_manager.update()
        
        # Update selection logic
        self.selector.update()
        
        # Update lighting effects
        self.light_manager.update()
        
        # Track planet positions and ensure they're within viewable range
        for planet in self.planets:
            distance = planet.position.length()
            if distance > self.camera_manager.max_zoom:
                print(f"Warning: {planet.name} is outside camera view at {distance:.1f} units")
            elif distance < 0.1:  # Check if planet is too close to origin (0,0,0)
                print(f"Warning: {planet.name} position near origin: {planet.position}")
    
    def cleanup(self):
        """Clean up resources when closing the application"""
        # Stop all threads first
        self.thread_manager.stop_threads()
        
        # Disable all lights
        self.light_manager.toggle_all_lights(False)
        
        # Remove all lights
        for light in self.light_manager.lights[:]:  # Create a copy of the list to iterate
            self.light_manager.remove_light(light)

if __name__ == "__main__":
    GameManager()