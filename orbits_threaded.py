"""
orbits_threaded.py - Threaded implementation of orbital mechanics calculations

This module provides a threaded version of the orbital mechanics calculations,
offloading intensive computations to a separate thread.
"""

import time
import logging
from threading import Lock
from queue import Queue
from orbits import calculate_orbit_position, calculate_orbital_velocity
from ursina import lerp

# Configure logging
logger = logging.getLogger(__name__)

class OrbitalCalculator:
    def __init__(self, stop_event):
        """
        Initialize the orbital calculator with a stop event.
        
        Args:
            stop_event (threading.Event): Event to signal thread termination
        """
        self.stop_event = stop_event
        self.bodies = []
        self.lock = Lock()
        self.position_queue = Queue()

    def add_body(self, body):
        """
        Register a celestial body for orbit calculations.
        
        Args:
            body: The celestial body to add
        """
        with self.lock:
            self.bodies.append(body)

    def remove_body(self, body):
        """
        Remove a celestial body from orbit calculations.
        
        Args:
            body: The celestial body to remove
        """
        with self.lock:
            if body in self.bodies:
                self.bodies.remove(body)

    def run(self):
        """Run orbital calculations in a loop."""
        while not self.stop_event.is_set():
            with self.lock:
                current_bodies = self.bodies.copy()
            
            for body in current_bodies:
                if hasattr(body, 'orbit_angle') and hasattr(body, 'orbit_speed'):
                    # Get frame delta time in a thread-safe way
                    frame_dt = getattr(body, '_frame_dt', 0.0)
                    
                    # Calculate new angle with bounds checking
                    new_angle = (body.orbit_angle + body.orbit_speed * frame_dt) % 360
                    
                    # Calculate and validate new position
                    target_position = calculate_orbit_position(
                        body.orbit_radius,
                        new_angle
                    )
                    
                    # Ensure position is valid
                    if target_position.length() < 1:
                        logger.warning(f"Invalid position for {body.name}, resetting to orbit radius")
                        target_position = Vec3(body.orbit_radius, 0, 0)
                    
                    # Smooth transition to new position
                    if hasattr(body, 'position'):
                        current_position = body.get_position_threaded()
                        if current_position.length() > 0:  # Only smooth if current position is valid
                            smoothed_position = lerp(current_position, target_position, 0.1)
                        else:
                            smoothed_position = target_position
                    else:
                        smoothed_position = target_position
                    
                    # Update angle and queue position
                    body.orbit_angle = new_angle
                    self.position_queue.put((body, smoothed_position))
            
            # Maintain consistent update rate
            time.sleep(0.016)  # ~60 FPS

    def update_positions(self):
        """
        Update positions of celestial bodies from the queue.
        This should be called from the main thread.
        """
        while not self.position_queue.empty():
            body, new_position = self.position_queue.get()
            if hasattr(body, 'set_position_threaded'):
                body.set_position_threaded(new_position)
            else:
                print(f"Warning: {body.name} does not have thread-safe position setting")
                body.position = new_position
            self.position_queue.task_done()

class ThreadedOrbitController:
    """Manages threaded orbital mechanics for multiple bodies"""
    def __init__(self, thread_manager):
        """
        Initialize the threaded orbit controller.
        
        Args:
            thread_manager (ThreadManager): The thread manager instance
        """
        self.orbital_calculator = OrbitalCalculator(thread_manager.stop_event)
        thread_manager.add_thread(target=self.orbital_calculator.run)
        
    def add_body(self, body):
        """Add a celestial body to be managed"""
        self.orbital_calculator.add_body(body)
        print(f"Added {body.name} to orbital calculations with radius {body.orbit_radius}")
        
    def remove_body(self, body):
        """Remove a celestial body from management"""
        self.orbital_calculator.remove_body(body)
        
    def update(self):
        """Update orbital positions for all managed bodies"""
        self.orbital_calculator.update_positions()
