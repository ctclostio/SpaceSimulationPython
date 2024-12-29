"""
camera.py - Manages camera controls and functionality

This module contains the CameraManager class which handles:
- Camera initialization and configuration
- Zoom/scroll functionality with dynamic sensitivity
- Camera movement controls with explicit mode switching
- Camera rotation with improved control
- Debug logging and state visualization
"""

from ursina import *
from math import atan2, degrees, radians, cos, sin
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CameraManager:
    def __init__(self):
        """Initialize camera with default settings"""
        self.camera = camera
        self.base_zoom_speed = 50
        self.min_zoom = 30
        self.max_zoom = 2000
        self.is_pivoted = False
        self.is_rotation_enabled = False  # Explicit rotation mode
        self.debug_overlay = None
        
        # Initialize debug overlay
        self.setup_debug_overlay()
        
        # Set initial camera position and rotation
        self.reset_camera()
        
        # Enable mouse controls
        self.enable_mouse_controls()
        
        logger.info("Camera manager initialized with position: %s, rotation: %s",
                   self.camera.position, self.camera.rotation)
        
    def setup_debug_overlay(self):
        """Setup debug overlay for camera state visualization"""
        self.debug_overlay = Text(
            text="",
            position=window.top_left + Vec2(0.02, -0.02),
            scale=0.8,
            visible=False
        )
    
    def toggle_debug_overlay(self):
        """Toggle the debug overlay visibility"""
        self.debug_overlay.visible = not self.debug_overlay.visible
        logger.info("Debug overlay toggled: %s", self.debug_overlay.visible)
    
    def update_debug_overlay(self):
        """Update debug overlay with current camera state"""
        if self.debug_overlay.visible:
            self.debug_overlay.text = (
                f"Camera Position: {self.camera.position}\n"
                f"Camera Rotation: {self.camera.rotation}\n"
                f"Zoom Level: {abs(self.camera.position.z)}\n"
                f"Rotation Mode: {'Enabled' if self.is_rotation_enabled else 'Disabled'}\n"
                f"Pivoted: {'Yes' if self.is_pivoted else 'No'}"
            )
    
    def enable_mouse_controls(self):
        """Enable mouse controls for camera movement and zoom"""
        try:
            self.camera.mouse_sensitivity = Vec2(40, 40)
            logger.info("Mouse controls enabled")
        except Exception as e:
            logger.error("Failed to enable mouse controls: %s", e)
    
    def disable_mouse_controls(self):
        """Disable mouse controls for the camera"""
        try:
            self.camera.mouse_sensitivity = Vec2(0, 0)
            self.camera.zoom = None
            logger.info("Mouse controls disabled")
        except Exception as e:
            logger.error("Failed to disable mouse controls: %s", e)
    
    def calculate_dynamic_zoom_speed(self):
        """Calculate zoom speed based on current zoom level"""
        current_zoom = abs(self.camera.position.z)
        # Adjust sensitivity based on zoom level
        return self.base_zoom_speed * (current_zoom / self.max_zoom + 0.1)
    
    def zoom(self):
        """Smooth zoom functionality with dynamic sensitivity."""
        try:
            # Only zoom when control is held (explicit mode)
            if not held_keys['control']:
                return
            
            zoom_speed = self.calculate_dynamic_zoom_speed()
            zoom_amount = -mouse.wheel * zoom_speed
            
            if zoom_amount == 0:
                return
                
            target_distance = clamp(
                self.camera.position.z + zoom_amount,
                -self.max_zoom,
                -self.min_zoom
            )
            
            # Interpolate position while maintaining x and y
            new_position = Vec3(
                0,
                self.camera.position.y,
                lerp(self.camera.position.z, target_distance, time.dt * 10)
            )
            
            self.camera.position = new_position
            logger.debug("Camera zoomed to z=%f", new_position.z)
            
        except Exception as e:
            logger.error("Error during zoom operation: %s", e)
    
    def toggle_rotation_mode(self):
        """Toggle camera rotation mode"""
        self.is_rotation_enabled = not self.is_rotation_enabled
        logger.info("Camera rotation mode: %s",
                   "enabled" if self.is_rotation_enabled else "disabled")
    
    def rotate_camera(self):
        """Allow camera rotation with right mouse button in rotation mode"""
        try:
            # Only rotate when in rotation mode and right mouse button is held
            if not self.is_rotation_enabled or not mouse.right:
                return
                
            # Calculate rotation with improved precision
            rotation_y = mouse.velocity[0] * self.camera.mouse_sensitivity[0]
            rotation_x = mouse.velocity[1] * self.camera.mouse_sensitivity[1]
            
            # Apply rotation with bounds checking
            new_rotation_x = clamp(self.camera.rotation_x + rotation_x, -89, 89)
            new_rotation_y = (self.camera.rotation_y + rotation_y) % 360
            
            self.camera.rotation_x = new_rotation_x
            self.camera.rotation_y = new_rotation_y
            
            logger.debug("Camera rotated to x=%f, y=%f", new_rotation_x, new_rotation_y)
            
        except Exception as e:
            logger.error("Error during camera rotation: %s", e)
    
    def get_look_at_rotation(self, target):
        """Calculate the rotation needed to look at a target point with error handling"""
        try:
            direction = Vec3(target) - self.camera.position
            
            # Avoid division by zero
            if direction.x == 0 and direction.z == 0:
                yaw = self.camera.rotation_y
            else:
                yaw = degrees(atan2(direction.x, direction.z))
            
            # Calculate pitch with safety checks
            horizontal_distance = (direction.x**2 + direction.z**2)**0.5
            if horizontal_distance == 0:
                pitch = 90 if direction.y > 0 else -90
            else:
                pitch = degrees(atan2(direction.y, horizontal_distance))
            
            logger.debug("Calculated look-at rotation: pitch=%f, yaw=%f", pitch, yaw)
            return Vec3(pitch, yaw, 0)
            
        except Exception as e:
            logger.error("Error calculating look-at rotation: %s", e)
            return self.camera.rotation
    
    def calculate_optimal_view(self):
        """Calculate optimal camera position based on the farthest planet's orbit"""
        try:
            from constants import NEPTUNE_ORBIT_RADIUS, CAMERA_DISTANCE, CAMERA_HEIGHT
            
            # Use configured camera distance and height from constants
            distance = NEPTUNE_ORBIT_RADIUS * (CAMERA_DISTANCE / 100)
            height = CAMERA_HEIGHT
            optimal_position = Vec3(0, height, -distance)
            
            logger.debug("Calculated optimal view position: %s", optimal_position)
            return optimal_position
            
        except Exception as e:
            logger.error("Error calculating optimal view: %s", e)
            return Vec3(0, 100, -500)  # Fallback position
    
    def reset_camera(self, duration=0.5):
        """Reset camera to the optimal position and smoothly look at the target"""
        try:
            target_position = self.calculate_optimal_view()
            self.camera.animate_position(target_position, duration=duration)
            
            # Animate rotation by calculating look_at rotation
            target_rotation = self.get_look_at_rotation((0, 0, 0))
            self.camera.animate_rotation(target_rotation, duration=duration)
            
            logger.info("Camera reset to position: %s, rotation: %s",
                       target_position, target_rotation)
            
        except Exception as e:
            logger.error("Error resetting camera: %s", e)
    
    def pivot_camera(self, pivot_point=(0, 0, 0), angle=180, duration=0.5):
        """Pivot the camera around a pivot point or return to the original view"""
        try:
            if self.is_pivoted:
                # Return to the original view
                self.reset_camera(duration)
                self.is_pivoted = False
                logger.info("Camera returned to original view")
            else:
                # Calculate the direction vector from the pivot point to the camera
                direction = self.camera.position - Vec3(pivot_point)
                
                try:
                    # Calculate the rotation angle in radians
                    angle_radians = radians(angle)
                    
                    # Calculate the new camera position using rotation
                    new_x = direction.x * cos(angle_radians) - direction.z * sin(angle_radians)
                    new_z = direction.x * sin(angle_radians) + direction.z * cos(angle_radians)
                    new_position = Vec3(new_x, direction.y, new_z) + Vec3(pivot_point)
                    
                    # Smoothly interpolate the camera position and rotation
                    self.camera.animate_position(new_position, duration=duration)
                    target_rotation = self.get_look_at_rotation(pivot_point)
                    self.camera.animate_rotation(target_rotation, duration=duration)
                    self.is_pivoted = True
                    
                    logger.info("Camera pivoted to position: %s, rotation: %s",
                               new_position, target_rotation)
                    
                except Exception as e:
                    logger.error("Error calculating pivot position: %s", e)
                    self.reset_camera(duration)  # Fallback to reset
                    
        except Exception as e:
            logger.error("Error during camera pivot: %s", e)
    
    def update(self):
        """Update camera controls and debug overlay"""
        try:
            self.zoom()
            self.rotate_camera()
            self.update_debug_overlay()
        except Exception as e:
            logger.error("Error in camera update: %s", e)