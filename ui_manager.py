"""
ui_manager.py - Manages user interface and camera controls

This module handles:
- Camera movement and controls
- On-screen displays (e.g., planet labels, FPS counter)
- User input handling
"""

from ursina import *
from constants import *

# Debug flag for FPS logging
DEBUG = False  # Set to True to enable dt/fps debug prints

class UIManager:
    def __init__(self):
        """Initialize UI elements and camera controls"""
        self.setup_camera_controls()
        self.setup_ui_elements()
        
        # Initialize timing system
        self.last_time = time.perf_counter()
        self.smoothed_fps = 60.0  # Initial FPS estimate
        
    def setup_camera_controls(self):
        """Configure camera movement and controls"""
        # Camera initialization is handled by CameraManager
        self.camera_update = lambda: None  # No-op update
        
    def setup_ui_elements(self):
        """Create basic UI elements"""
        # Add performance stats
        self.stats_text = Text(
            text='FPS: 0\nFrame: 0ms',
            position=(-0.9, 0.45),  # Move left for better visibility
            scale=1.2,
            color=color.white,
            origin=(0, 0)  # Left align
        )
        
        # Add enhanced camera controls display
        self.camera_text = Text(
            text="Camera Controls:\nRight click: Toggle rotation\nScroll: Zoom\nWASD: Move\nQ/E: Up/Down",
            position=(-0.9, 0.35),
            scale=1,
            color=color.gray,
            origin=(0, 0)  # Left align
        )
        
        # Add camera position display
        self.camera_pos_text = Text(
            text="Camera: (0, 0, 0)",
            position=(-0.9, 0.25),
            scale=1,
            color=color.light_gray,
            origin=(0, 0)  # Left align
        )
        
        # Add planet info display
        self.info_text = Text(
            text="",
            position=(-0.7, 0.3),
            scale=1.2,
            color=color.white
        )
        
    def update(self):
        """Update UI elements each frame"""
        # Get current time using high-precision monotonic clock
        current_time = time.perf_counter()
        dt = current_time - self.last_time
        self.last_time = current_time

        # Handle pause detection (e.g., when window is minimized)
        if dt > 1.0:  # If more than 1 second has passed
            return  # Skip update to avoid anomalies
            
        # Cap extreme frame times to avoid skewing FPS calculations
        dt = min(dt, 0.25)  # Cap at 250ms per frame (~4 FPS minimum)
        dt = max(dt, 1e-6)  # Minimum of 1 microsecond
        
        # Calculate FPS using exponential moving average
        instant_fps = 1.0 / dt
        alpha = 0.1  # Smoothing factor (0.1 = 10% weight to new samples)
        self.smoothed_fps = (alpha * instant_fps) + ((1 - alpha) * self.smoothed_fps)
        
        # Update stats display with FPS and frame time
        self.stats_text.text = f'FPS: {int(self.smoothed_fps)}\nFrame: {dt*1000:.1f}ms'
        
        # Update camera position display if camera is available
        if hasattr(self, 'camera') and self.camera:
            pos = self.camera.position
            self.camera_pos_text.text = f'Camera: ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})'
            
        self.camera_update()

    def update_selected_info(self, entity):
        """Update the on-screen display with entity info"""
        self.info_text.text = f"Selected: {entity.name}\nRadius: {entity.scale}\nOrbit: {entity.orbit_radius}"