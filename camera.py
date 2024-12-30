"""
camera.py - Modular camera system

This module contains:
- Base Camera class with core functionality
- Specialized camera feature classes
- CameraManager that composes features
"""

from ursina import *
from math import atan2, degrees, radians, cos, sin, sqrt, tan
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

class Camera(Entity):
    """Base camera class with core functionality"""
    def __init__(self):
        super().__init__()
        self.position = Vec3(0, 500, -1000)  # Better initial distance for space view
        self.orthographic = False
        self.fov = 60  # Wider FOV for better space visualization
        self.clip_plane_near = 1
        self.clip_plane_far = 10000000  # Extended far plane for distant objects
        self.rotation = Vec3(30, 0, 0)  # Angled down slightly for better perspective
        self.min_zoom = 50
        self.max_zoom = 5000  # Increased for better distant viewing
        self.debug_overlay = None
        self.mouse_sensitivity = Vec2(40, 40)  # Standardized mouse sensitivity
        
        self.setup_debug_overlay()
        self.reset_camera()
        
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
        self.animate_position(self.position, duration)
        self.animate_rotation(self.rotation, duration)
        
    def animate_position(self, target, duration):
        """Animate camera to target position"""
        super().animate_position(target, duration=duration)
        
    def animate_rotation(self, target, duration):
        """Animate camera to target rotation"""
        super().animate_rotation(target, duration=duration)
        
    def update(self):
        """Update camera state"""
        self.update_debug_overlay()
        self.update_view_matrix()
        
    def update_view_matrix(self):
        """Calculate and update the camera's view matrix"""
        position = self.position
        target = position + self.forward
        up = self.up
        
        z = (position - target).normalized()
        x = up.cross(z).normalized()
        y = z.cross(x)
        
        self.view_matrix = np.array([
            [x.x, x.y, x.z, -x.dot(position)],
            [y.x, y.y, y.z, -y.dot(position)],
            [z.x, z.y, z.z, -z.dot(position)],
            [0, 0, 0, 1]
        ])

class CameraZoom:
    """Handles camera zoom functionality"""
    def __init__(self, camera):
        self.camera = camera
        self.base_zoom_speed = 50
        
    def calculate_dynamic_zoom_speed(self):
        """Calculate zoom speed based on current zoom level"""
        current_zoom = abs(self.camera.position.z)
        return self.base_zoom_speed * (current_zoom / self.camera.max_zoom + 0.1)
        
    def zoom(self):
        """Handle zoom functionality in both directions"""
        if not held_keys['control']:
            return
            
        zoom_speed = self.calculate_dynamic_zoom_speed()
        
        # Safely handle mouse wheel input
        try:
            zoom_amount = getattr(mouse, 'wheel', 0) * zoom_speed
        except Exception as e:
            logger.warning(f"Error getting mouse wheel: {e}")
            return
            
        if zoom_amount == 0:
            return
            
        # Calculate target distance based on scroll direction
        current_distance = abs(self.camera.position.z)
        if mouse.wheel > 0:
            # Zoom in (scroll forward)
            target_distance = max(current_distance - zoom_amount, self.camera.min_zoom)
        else:
            # Zoom out (scroll back)
            target_distance = min(current_distance + zoom_amount, self.camera.max_zoom)
            
        # Maintain negative z-axis for proper perspective
        target_distance = -target_distance
        
        # Smoothly interpolate to new position
        new_position = Vec3(
            self.camera.position.x,
            self.camera.position.y,
            lerp(self.camera.position.z, target_distance, time.dt * 10)
        )
        
        self.camera.position = new_position

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
        if not self.is_enabled or not mouse.right:
            return
            
        rotation_y = mouse.velocity[0] * self.camera.mouse_sensitivity[0]
        rotation_x = mouse.velocity[1] * self.camera.mouse_sensitivity[1]
        
        new_rotation_x = clamp(self.camera.rotation_x + rotation_x, -89, 89)
        new_rotation_y = (self.camera.rotation_y + rotation_y) % 360
        
        self.camera.rotation_x = new_rotation_x
        self.camera.rotation_y = new_rotation_y

class CelestialBodyTracker:
    """Handles tracking and transitioning between celestial bodies"""
    def __init__(self, camera):
        self.camera = camera
        
    def track_body(self, body, duration=1.0):
        """Track and focus on a celestial body"""
        if not body:
            logger.warning("No celestial body provided for tracking")
            return
            
        min_zoom, max_zoom = self.calculate_zoom_constraints(body)
        optimal_distance = max(body.scale.x * 3, min_zoom)
        optimal_distance = min(optimal_distance, max_zoom)
        
        target_position = body.position + Vec3(0, optimal_distance/2, -optimal_distance)
        
        self.camera.animate_position(target_position, duration)
        self.camera.animate_rotation(self.get_look_at_rotation(body.position), duration)
        
    def transition_between_bodies(self, from_body, to_body, duration=1.5):
        """Smoothly transition between two celestial bodies"""
        if not from_body or not to_body:
            logger.warning("Missing celestial bodies for transition")
            return
            
        midpoint = (from_body.position + to_body.position) * 0.5
        distance = (to_body.position - from_body.position).length()
        arc_height = distance * 0.5
        
        control_point1 = from_body.position + Vec3(0, arc_height, 0)
        control_point2 = to_body.position + Vec3(0, arc_height, 0)
        
        path = [
            from_body.position,
            control_point1,
            control_point2,
            to_body.position
        ]
        
        self.camera.animate_position(path, duration=duration, curve='smooth')
        self.track_body(to_body, duration)
        
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
        current_rot = self.camera.rotation
        
        if (self._last_camera_position is None or
            self._last_camera_rotation is None or
            not np.allclose([current_pos.x, current_pos.y, current_pos.z],
                          [self._last_camera_position.x, self._last_camera_position.y, self._last_camera_position.z]) or
            not np.allclose([current_rot.x, current_rot.y, current_rot.z],
                          [self._last_camera_rotation.x, self._last_camera_rotation.y, self._last_camera_rotation.z])):
            
            self._last_camera_position = Vec3(current_pos.x, current_pos.y, current_pos.z)
            self._last_camera_rotation = Vec3(current_rot.x, current_rot.y, current_rot.z)
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
        for plane in self.planes:
            distance = (plane[0] * center.x +
                       plane[1] * center.y +
                       plane[2] * center.z +
                       plane[3])
            if distance < -radius:
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

class CameraMovement:
    """Handles camera movement with WASD/QE controls"""
    def __init__(self, camera):
        self.camera = camera
        self.move_speed = 500
        self.vertical_speed = 500
        
    def __init__(self, camera):
        self.camera = camera
        self.base_move_speed = 500
        self.base_vertical_speed = 500
        self._cached_forward = None
        self._cached_right = None
        self._cached_up = None
        self._last_update_time = 0
        self._cache_lifetime = 0.1  # Cache vectors for 100ms
        
    def _update_cached_directions(self):
        """Cache normalized direction vectors"""
        self._cached_forward = self.camera.forward.normalized()
        self._cached_right = self.camera.right.normalized()
        self._cached_up = self.camera.up.normalized()
        
    def _get_dynamic_speed(self):
        """Calculate movement speed based on camera distance from origin"""
        distance = self.camera.position.length()
        return self.base_move_speed * (1 + distance / 1000)

    def move(self):
        """Handle camera movement based on key inputs with dynamic speed"""
        # Update cached directions if cache expired
        current_time = time.time()
        if (self._cached_forward is None or
            current_time - self._last_update_time > self._cache_lifetime):
            self._update_cached_directions()
            self._last_update_time = current_time
            
        move_direction = Vec3(0, 0, 0)
        current_speed = self._get_dynamic_speed()
        
        # Debug input system state
        try:
            if held_keys:
                active_keys = [k for k, v in held_keys.items() if v]
                logger.debug("input", "Active keys detected", keys=active_keys)
                camera_report.log_keypress(active_keys)
                
                if held_keys['w']:
                    move_direction += self._cached_forward
                if held_keys['s']:
                    move_direction -= self._cached_forward
                if held_keys['a']:
                    move_direction -= self._cached_right
                if held_keys['d']:
                    move_direction += self._cached_right
                if held_keys['q']:
                    move_direction -= self._cached_up
                if held_keys['e']:
                    move_direction += self._cached_up
                    
                if move_direction.length() > 0:
                    # Normalize and scale movement
                    move_direction = move_direction.normalized()
                    current_speed = self._get_dynamic_speed()
                    
                    # Apply smooth acceleration
                    smooth_factor = min(time.dt * 5, 1.0)  # Smooth acceleration over 0.2 seconds
                    
                    # Calculate target position using Panda3D vectors
                    movement = move_direction * current_speed * time.dt
                    target_position = self.camera.position + movement
                    
                    logger.debug("movement", "Camera movement calculated",
                                movement=movement, speed=current_speed)
                    camera_report.log_movement(movement)
                    
                    # Update position using Panda3D's native lerp
                    self.camera.position = self.camera.position.lerp(target_position, smooth_factor)
                    self.camera._world_transform_needs_update = True
                    
                    # Update view matrix
                    if hasattr(self.camera, 'update_view_matrix'):
                        self.camera.update_view_matrix()
                        
            else:
                logger.debug("input", "No active movement keys detected")
        except Exception as e:
            logger.error("movement", "Error updating camera movement", error=str(e))
            camera_report.log_error(e)

class CameraManager:
    """Manages camera features through composition"""
    def __init__(self):
        self.camera = Camera()
        self.zoom = CameraZoom(self.camera)
        self.rotation = CameraRotation(self.camera)
        self.tracker = CelestialBodyTracker(self.camera)
        self.pivot = CameraPivot(self.camera)
        self.culler = FrustumCuller(self)
        self.perspective = CameraPerspective(self.camera)
        self.movement = CameraMovement(self.camera)
        
    @property
    def max_zoom(self):
        """Get max zoom value from base camera"""
        return self.camera.max_zoom
        
    @property
    def fov(self):
        """Get field of view from base camera"""
        return self.camera.fov
        
    @property
    def clip_plane_near(self):
        """Get near clipping plane from base camera"""
        return self.camera.clip_plane_near
        
    @property
    def clip_plane_far(self):
        """Get far clipping plane from base camera"""
        return self.camera.clip_plane_far
        
    @property
    def position(self):
        """Get camera position from base camera"""
        return self.camera.position
        
    @property
    def forward(self):
        """Get forward vector from base camera"""
        return self.camera.forward
        
    @property
    def up(self):
        """Get up vector from base camera"""
        return self.camera.up
        
    @property
    def min_zoom(self):
        """Get min zoom value from base camera"""
        return self.camera.min_zoom
        
    def update(self):
        """Update all camera features"""
        logger.debug("update", "Updating camera features")
        self.camera.update()
        self.zoom.zoom()
        self.rotation.rotate()
        logger.debug("update", "Calling movement.update()")
        self.movement.move()
        logger.debug("update", "Finished movement.update()")
        
        # Update frustum planes for culling
        self.culler.extract_frustum_planes()
        logger.debug("update", "Finished camera update")
        
    def is_visible(self, entity):
        """Check if an entity is visible within the camera frustum"""
        if not hasattr(entity, 'scale'):
            return True
            
        # Calculate bounding sphere radius
        radius = max(entity.scale.x, entity.scale.y, entity.scale.z) / 2
        return self.culler.is_sphere_visible(entity.position, radius)