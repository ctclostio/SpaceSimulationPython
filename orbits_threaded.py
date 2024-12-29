"""
orbits_threaded.py - Threaded implementation of orbital mechanics calculations

This module provides a threaded version of the orbital mechanics calculations,
offloading intensive computations to a separate thread.
"""

import time
from threading import Lock
from queue import Queue
from orbits import calculate_orbit_position, calculate_orbital_velocity

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
                    # Calculate new position using frame delta time
                    if not hasattr(body, '_frame_dt'):
                        body._frame_dt = 0.0
                    
                    body.orbit_angle += body.orbit_speed * body._frame_dt
                    new_position = calculate_orbit_position(
                        body.orbit_radius,
                        body.orbit_angle
                    )
                    
                    # Queue the position update
                    self.position_queue.put((body, new_position))
            
            # Dynamic sleep to maintain reasonable update rate without excessive CPU usage
            time.sleep(0.001)  # 1ms sleep to prevent thread from consuming too much CPU

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