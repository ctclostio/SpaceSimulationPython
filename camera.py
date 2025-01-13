"""
camera.py - Modular camera system

This module contains:
- Base Camera class with core functionality
- Specialized camera feature classes
- CameraManager that composes features
"""

from ursina import *
from ursina.prefabs.editor_camera import EditorCamera
from math import atan2, degrees, radians, cos, sin, sqrt, tan, log10
import logging
import logging.handlers
import numpy as np

# Global camera reference for matrix access
from ursina import camera as main_camera

# Configure logging with structured format
class StructuredMessage:
    def __init__(self, category, message, **kwargs):
        self.category = category
        self.message = message
        self.kwargs = kwargs
        
    def __str__(self):
        # Optimized format: category|message|key=value pairs
        return f"{self.category}|{self.message}|" + \
            ",".join(f"{k}={v}" for k, v in self.kwargs.items())

class CameraLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # Default to INFO level
        
        # Create optimized formatter
        formatter = logging.Formatter(
            '%(levelname).1s|%(asctime)s|%(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Set up console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        # Create rotating file handler with size limit and error handling
        try:
            fh = logging.handlers.RotatingFileHandler(
                'camera.log',
                maxBytes=1024*1024,  # 1MB
                backupCount=3,
                delay=True  # Delay file creation until first write
            )
            fh.setLevel(logging.WARNING)  # Only log warnings and above to file
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        except PermissionError:
            # If file is locked, fall back to console-only logging
            pass
        
    def debug(self, category, message, **kwargs):
        self.logger.debug(StructuredMessage(category, message, **kwargs))
        
    def info(self, category, message, **kwargs):
        self.logger.info(StructuredMessage(category, message, **kwargs))
        
    def warning(self, category, message, **kwargs):
        self.logger.warning(StructuredMessage(category, message, **kwargs))
        
    def error(self, category, message, **kwargs):
        self.logger.error(StructuredMessage(category, message, **kwargs))
        
    def critical(self, category, message, **kwargs):
        self.logger.critical(StructuredMessage(category, message, **kwargs))

# Initialize structured logger
logger = CameraLogger()

# Create report generator
class CameraReport:
    def __init__(self):
        self.movements = []
        self.errors = []
        self.keypresses = []
        
    def log_movement(self, movement):
        self.movements.append(movement)
        
    def log_error(self, error):
        self.errors.append(error)
        
    def log_keypress(self, keypress):
        self.keypresses.append(keypress)
        
    def generate_report(self):
        report = [
            "Camera Movement Report",
            "=====================",
            f"Total movements: {len(self.movements)}",
            f"Total errors: {len(self.errors)}",
            f"Total keypresses: {len(self.keypresses)}",
            "",
            "Recent Movements:",
            *[str(m) for m in self.movements[-10:]],
            "",
            "Recent Errors:",
            *[str(e) for e in self.errors[-10:]],
            "",
            "Recent Keypresses:",
            *[str(k) for k in self.keypresses[-10:]]
        ]
        with open('camera_report.txt', 'w') as f:
            f.write('\n'.join(report))
        return '\n'.join(report)

# Initialize report
camera_report = CameraReport()

class Camera(EditorCamera):
    """Enhanced camera class extending EditorCamera for space simulation"""
    def __init__(self):
        # Initialize EditorCamera with custom settings for space scale
        super().__init__(
            rotation_speed = Vec2(40, 40),
            pan_speed = Vec2(10, 10),  # Increased for better space navigation
            zoom_speed = 2,  # Increased for better zoom control
            move_speed = 50  # Increased for space scale
        )
        
        # Override EditorCamera defaults with space simulation settings
        self.orthographic = False
        self.fov = 60  # Narrower FOV for better depth perception
        self.clip_plane_near = 1
        self.clip_plane_far = 100000000  # Increased for space scale
        self.min_zoom = 10  # Allow closer zoom
        self.max_zoom = 50000  # Allow much further zoom for space scale
        self.debug_overlay = None
        
        # Force initial position and rotation
        self.world_position = Vec3(0, 100, -500)  # Further back initial position
        self.rotation = Vec3(30, 0, 0)  # Initial look angle
        
        self.setup_debug_overlay()
        
        # Lock minimum height to prevent going below objects
        self.min_height = 10
        
    def update(self):
        """Override EditorCamera update to maintain space simulation requirements"""
        # Convert Vec2 components to floats before parent update
        if hasattr(self, 'smoothing_helper'):
            self.smoothing_helper.rotation_x = float(self.smoothing_helper.rotation_x)
            if hasattr(mouse, 'velocity'):
                mouse.velocity = Vec2(float(mouse.velocity[0]), float(mouse.velocity[1]))
                
        super().update()  # Let EditorCamera handle basic updates
        
        # Ensure camera stays within bounds
        if self.world_position.y < 10:  # Prevent camera from going too low
            self.world_position = Vec3(
                self.world_position.x,
                10,
                self.world_position.z
            )
            
        # Update debug overlay
        if hasattr(self, 'debug_overlay') and self.debug_overlay:
            self.update_debug_overlay()
            
    def input(self, key):
        """Handle camera input with EditorCamera integration"""
        if key == 'right mouse down':
            mouse.locked = True
        elif key == 'right mouse up':
            mouse.locked = False
            
        super().input(key)  # Let EditorCamera handle rotation after our modifications
        
    def setup_debug_overlay(self):
        """Setup debug overlay for camera state visualization"""
        self.debug_overlay = Text(
            text="",
            position=window.top_left + Vec2(0.02, -0.02),
            scale=0.8,
            visible=True
        )
        
    def update_debug_overlay(self):
        """Update debug overlay with current camera state"""
        if self.debug_overlay.visible:
            self.debug_overlay.text = (
                f"Position: {self.position}\n"
                f"Rotation: {self.rotation}\n"
                f"Zoom: {abs(self.position.z)}"
            )
            
    def reset_camera(self, duration=0.5):
        """Reset camera to default position and rotation"""
        default_position = Vec3(0, 50, -100)
        default_rotation = Vec3(30, 0, 0)
        
        # Use EditorCamera's built-in position setter
        self.world_position = default_position
        self.rotation = default_rotation
        
    def animate_position(self, target, duration):
        """Animate camera to target position"""
        if isinstance(target, (list, tuple)):
            # Handle path-based animation for celestial body transitions
            invoke(setattr, self, 'world_position', target[0], delay=0)
            for i, pos in enumerate(target[1:], 1):
                invoke(setattr, self, 'world_position', pos, delay=duration * (i/len(target)))
        else:
            # Simple position animation
            invoke(setattr, self, 'world_position', target, delay=duration)
        
    def animate_rotation(self, target, duration):
        """Animate camera to target rotation"""
        invoke(setattr, self, 'rotation', target, delay=duration)

class CameraZoom:
    """Handles camera zoom functionality for space simulation scale"""
    def __init__(self, camera):
        self.camera = camera
        self.base_zoom_speed = 200  # Increased for space scale
        self.zoom_smoothing = 5  # Smoothing factor for zoom interpolation
        
    def calculate_dynamic_zoom_speed(self):
        """Calculate zoom speed based on current zoom level and distance from origin"""
        current_distance = self.camera.world_position.length()
        zoom_factor = current_distance / self.camera.max_zoom
        
        # Logarithmic scaling for smoother transitions at different distances
        return self.base_zoom_speed * (1 + log10(max(1, zoom_factor)))
        
    def zoom(self):
        """Handle zoom functionality with space-scale considerations"""
        if not mouse.wheel:
            return
            
        # Calculate zoom speed based on current position
        zoom_speed = self.calculate_dynamic_zoom_speed()
        zoom_amount = mouse.wheel * zoom_speed * time.dt * 60  # Normalize for framerate
        
        # Get current forward direction for zoom
        forward = self.camera.forward
        
        # Calculate new position
        if mouse.wheel > 0:  # Zoom in
            target_pos = self.camera.world_position + forward * zoom_amount
            # Check minimum zoom
            if target_pos.length() < self.camera.min_zoom:
                target_pos = forward * self.camera.min_zoom
        else:  # Zoom out
            target_pos = self.camera.world_position - forward * zoom_amount
            # Check maximum zoom
            if target_pos.length() > self.camera.max_zoom:
                target_pos = forward * -self.camera.max_zoom
        
        # Ensure minimum height is maintained
        if target_pos.y < self.camera.min_height:
            target_pos.y = self.camera.min_height
            
        # Smoothly interpolate to new position
        self.camera.world_position = lerp(
            self.camera.world_position,
            target_pos,
            time.dt * self.zoom_smoothing
        )

class CameraRotation:
    """Handles camera rotation functionality"""
    def __init__(self, camera):
        self.camera = camera
        self.is_enabled = False
        
    def toggle(self):
        """Toggle rotation mode"""
        self.is_enabled = not self.is_enabled
        
    def rotate(self):
        """Handle camera rotation"""
        logger.debug("camera_rotation", "Rotate function called")
        if not self.is_enabled or not mouse.right:
            return
            
        logger.debug("camera_rotation", "Rotation enabled and right mouse button pressed")
        rotation_y = mouse.velocity[0] * self.camera.mouse_sensitivity[0]
        rotation_x = mouse.velocity[1] * self.camera.mouse_sensitivity[1]
        
        new_rotation_x = clamp(self.camera.rotation_x + rotation_x, -89, 89)
        new_rotation_y = (self.camera.rotation_y + rotation_y) % 360
        
        self.camera.rotation_x = new_rotation_x
        self.camera.rotation_y = new_rotation_y

class CelestialBodyTracker:
    """Handles tracking and transitioning between celestial bodies with space-scale considerations"""
    def __init__(self, camera):
        self.camera = camera
        self.tracking_offset = 2.5  # Multiplier for viewing distance based on body size
        self.min_tracking_distance = 50  # Minimum distance to maintain from any body
        
    def track_body(self, body, duration=1.0):
        """Track and focus on a celestial body with proper scaling"""
        if not body:
            logger.warning("No celestial body provided for tracking")
            return
            
        # Calculate optimal viewing distance based on body size
        body_radius = max(body.scale.x, body.scale.y, body.scale.z) / 2
        optimal_distance = max(
            body_radius * self.tracking_offset,
            self.min_tracking_distance
        )
        
        # Calculate position that gives good view of the body
        offset = Vec3(
            optimal_distance * 0.5,  # Slight offset for better perspective
            optimal_distance * 0.3,  # Height offset
            -optimal_distance        # Distance from body
        )
        
        target_position = body.position + offset
        
        # Ensure minimum height is maintained
        if target_position.y < self.camera.min_height:
            target_position.y = self.camera.min_height
            
        # Animate to new position and rotation
        self.camera.animate_position(target_position, duration)
        self.camera.animate_rotation(self.get_look_at_rotation(body.position), duration)
        
    def transition_between_bodies(self, from_body, to_body, duration=1.5):
        """Smoothly transition between celestial bodies with proper scaling"""
        if not from_body or not to_body:
            logger.warning("Missing celestial bodies for transition")
            return
            
        # Calculate transition path
        start_pos = self.camera.world_position
        end_pos = to_body.position
        
        # Calculate arc height based on distance
        distance = (end_pos - start_pos).length()
        arc_height = max(distance * 0.3, 1000)  # Ensure minimum arc height
        
        # Create Bezier curve control points
        midpoint = (start_pos + end_pos) * 0.5
        control_point = midpoint + Vec3(0, arc_height, 0)
        
        # Generate path points
        steps = 20  # Number of points in the path
        path = []
        for i in range(steps):
            t = i / (steps - 1)
            # Quadratic Bezier curve
            point = (1-t)**2 * start_pos + \
                   2*(1-t)*t * control_point + \
                   t**2 * end_pos
            # Ensure minimum height
            if point.y < self.camera.min_height:
                point.y = self.camera.min_height
            path.append(point)
        
        # Animate along path
        self.camera.animate_position(path, duration=duration)
        
        # Track target body at end of transition
        invoke(self.track_body, to_body, delay=duration)
        
    def calculate_zoom_constraints(self, body):
        """Calculate zoom constraints based on body size"""
        body_scale = max(body.scale.x, body.scale.y, body.scale.z)
        min_zoom = max(self.camera.min_zoom, body_scale * 0.5)
        max_zoom = min(self.camera.max_zoom, body_scale * 10)
        return min_zoom, max_zoom
        
    def get_look_at_rotation(self, target):
        """Calculate rotation needed to look at a target point"""
        direction = Vec3(target) - self.camera.position
        
        if direction.x == 0 and direction.z == 0:
            yaw = self.camera.rotation_y
        else:
            yaw = degrees(atan2(direction.x, direction.z))
            
        horizontal_distance = (direction.x**2 + direction.z**2)**0.5
        if horizontal_distance == 0:
            pitch = 90 if direction.y > 0 else -90
        else:
            pitch = degrees(atan2(direction.y, horizontal_distance))
            
        return Vec3(pitch, yaw, 0)

class CameraPivot:
    """Handles camera pivot functionality"""
    def __init__(self, camera):
        self.camera = camera
        self.is_pivoted = False
        
    def pivot(self, pivot_point=(0, 0, 0), angle=180, duration=0.5):
        """Pivot the camera around a point or return to original view"""
        if self.is_pivoted:
            self.camera.reset_camera(duration)
            self.is_pivoted = False
        else:
            direction = self.camera.position - Vec3(pivot_point)
            angle_radians = radians(angle)
            
            new_x = direction.x * cos(angle_radians) - direction.z * sin(angle_radians)
            new_z = direction.x * sin(angle_radians) + direction.z * cos(angle_radians)
            new_position = Vec3(new_x, direction.y, new_z) + Vec3(pivot_point)
            
            self.camera.animate_position(new_position, duration)
            target_rotation = self.get_look_at_rotation(pivot_point)
            self.camera.animate_rotation(target_rotation, duration)
            self.is_pivoted = True
            
    def get_look_at_rotation(self, target):
        """Calculate rotation needed to look at a target point"""
        direction = Vec3(target) - self.camera.position
        
        if direction.x == 0 and direction.z == 0:
            yaw = self.camera.rotation_y
        else:
            yaw = degrees(atan2(direction.x, direction.z))
            
        horizontal_distance = (direction.x**2 + direction.z**2)**0.5
        if horizontal_distance == 0:
            pitch = 90 if direction.y > 0 else -90
        else:
            pitch = degrees(atan2(direction.y, horizontal_distance))
            
        return Vec3(pitch, yaw, 0)

class FrustumCuller:
    """Handles frustum culling for camera visibility tests"""
    def __init__(self, camera):
        self.camera = camera
        self.planes = [np.zeros(4) for _ in range(6)]  # 6 frustum planes
        self._cached_vp_matrix = None
        self._last_camera_position = None
        self._last_camera_rotation = None
        self._matrix_dirty = True
        
    def _is_transform_changed(self):
        """Check if camera transform has changed since last update"""
        current_pos = self.camera.position
        
        if (self._last_camera_position is None or
            self._last_camera_rotation is None or
            not np.allclose([current_pos.x, current_pos.y, current_pos.z],
                          [self._last_camera_position.x, self._last_camera_position.y, self._last_camera_position.z]) or
            not np.allclose([self.camera.rotation_x, self.camera.rotation_y],
                           [self._last_camera_rotation[0], self._last_camera_rotation[1]])):
            
            self._last_camera_position = Vec3(current_pos.x, current_pos.y, current_pos.z)
            self._last_camera_rotation = [self.camera.rotation_x, self.camera.rotation_y]
            return True
        return False
        
    def extract_frustum_planes(self):
        """Extract frustum planes from view-projection matrix with caching"""
        if not self._is_transform_changed() and self._cached_vp_matrix is not None:
            return  # Use cached planes if transform hasn't changed
            
        # Calculate matrices only when needed
        aspect_ratio = window.aspect_ratio
        fov_rad = radians(self.camera.fov)
        near = self.camera.clip_plane_near
        far = self.camera.clip_plane_far
        
        # Calculate projection matrix
        f = 1.0 / tan(fov_rad / 2.0)
        projection_matrix = np.array([
            [f / aspect_ratio, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0]
        ])
        
        # Optimized view matrix calculation using cached directions
        position = self.camera.position
        forward = self.camera.forward.normalized()
        right = self.camera.right.normalized()
        up = self.camera.up.normalized()
        
        view_matrix = np.array([
            [right.x, right.y, right.z, -right.dot(position)],
            [up.x, up.y, up.z, -up.dot(position)],
            [-forward.x, -forward.y, -forward.z, forward.dot(position)],
            [0, 0, 0, 1]
        ])
        
        # Cache the view-projection matrix
        self._cached_vp_matrix = np.dot(projection_matrix, view_matrix)
        vp_matrix = self._cached_vp_matrix
        
        # Extract planes from combined matrix
        self.planes[0] = vp_matrix[3] + vp_matrix[0]  # Left
        self.planes[1] = vp_matrix[3] - vp_matrix[0]  # Right
        self.planes[2] = vp_matrix[3] + vp_matrix[1]  # Bottom
        self.planes[3] = vp_matrix[3] - vp_matrix[1]  # Top
        self.planes[4] = vp_matrix[3] + vp_matrix[2]  # Near
        self.planes[5] = vp_matrix[3] - vp_matrix[2]  # Far
        
        # Normalize planes
        for i in range(6):
            length = sqrt(self.planes[i][0]**2 + self.planes[i][1]**2 + self.planes[i][2]**2)
            self.planes[i] /= length
            
    def is_sphere_visible(self, center, radius):
        """Test if a sphere is visible within the frustum"""
        # Add 10% buffer to radius to prevent premature culling
        radius *= 1.1
        
        # Check each frustum plane
        for plane in self.planes:
            distance = (plane[0] * center.x +
                       plane[1] * center.y +
                       plane[2] * center.z +
                       plane[3])
            if distance < -radius:
                # Add debug logging for culled objects
                logger.debug("frustum", f"Object culled by plane: {plane}")
                return False
        return True

class CameraPerspective:
    """Handles different camera perspectives"""
    def __init__(self, camera):
        self.camera = camera
        self.perspectives = {
            '1': self.top_down_view,
            '2': self.side_view,
            '3': self.isometric_view
        }
        
    def top_down_view(self):
        """Set camera to top-down perspective"""
        self.camera.position = Vec3(0, 1000, 0)
        self.camera.rotation = Vec3(90, 0, 0)
        
    def side_view(self):
        """Set camera to side perspective"""
        self.camera.position = Vec3(1000, 0, 0)
        self.camera.rotation = Vec3(0, 90, 0)
        
    def isometric_view(self):
        """Set camera to isometric perspective"""
        self.camera.position = Vec3(1000, 1000, -1000)
        self.camera.rotation = Vec3(45, 45, 0)
        
    def switch_perspective(self, key):
        """Switch to selected perspective"""
        if key in self.perspectives:
            self.perspectives[key]()

# Movement is now handled by EditorCamera

class CameraManager:
    """Manages camera features through composition with EditorCamera integration"""
    def __init__(self):
        self.camera = Camera()  # Now using EditorCamera-based implementation
        self.zoom = CameraZoom(self.camera)
        self.rotation = CameraRotation(self.camera)
        self.tracker = CelestialBodyTracker(self.camera)
        self.pivot = CameraPivot(self.camera)
        self.culler = FrustumCuller(self)
        self.perspective = CameraPerspective(self.camera)
        
        # EditorCamera handles movement internally
        logger.info("camera_init", "Initialized with EditorCamera-based implementation")
        
    def update(self):
        """Update camera features, letting EditorCamera handle core functionality"""
        logger.debug("update", "Updating camera features")
        
        # Base camera updates (handled by EditorCamera)
        self.camera.update()
        
        # Additional feature updates
        self.zoom.zoom()
        
        # Update frustum planes for culling
        self.culler.extract_frustum_planes()
        logger.debug("update", "Finished camera update")
        
    # Maintain property access for compatibility
    @property
    def max_zoom(self): return self.camera.max_zoom
    @property
    def fov(self): return self.camera.fov
    @property
    def clip_plane_near(self): return self.camera.clip_plane_near
    @property
    def clip_plane_far(self): return self.camera.clip_plane_far
    @property
    def position(self): return self.camera.position
    @property
    def forward(self): return self.camera.forward
    @property
    def up(self): return self.camera.up
    @property
    def right(self): return self.camera.right
    @property
    def min_zoom(self): return self.camera.min_zoom
    @property
    def rotation_x(self): return self.camera.rotation.x
    @property
    def rotation_y(self): return self.camera.rotation.y
        
    def is_visible(self, entity):
        """Check if an entity is visible within the camera frustum"""
        if not hasattr(entity, 'scale'):
            return True
            
        # Calculate bounding sphere radius
        radius = max(entity.scale.x, entity.scale.y, entity.scale.z) / 2
        return self.culler.is_sphere_visible(entity.position, radius)
