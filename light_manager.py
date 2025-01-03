"""
light_manager.py - Centralized lighting management system

This module contains the LightManager class which handles:
- Light creation and configuration
- Light attachment to entities
- Performance optimization through light limiting
- Dynamic light effects
"""

from ursina import *
from typing import List, Dict, Optional, Union
import noise
import math

class SunLight(DirectionalLight):
    """Specialized directional light for realistic sunlight simulation"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shadow_map_resolution = Vec2(2048, 2048)  # Higher resolution shadows
        self.shadows = True
        self._time_of_day = 0.0  # 0-1 representing day cycle
        self._base_color = color.rgb(255, 253, 208)  # Warm sunlight color
        self._intensity = 1.0
        
    @property
    def time_of_day(self):
        return self._time_of_day
        
    @time_of_day.setter
    def time_of_day(self, value):
        """Update light properties based on time of day (0-1)"""
        self._time_of_day = value % 1.0
        self.update_light_properties()
        
    def update_light_properties(self):
        """Update color and intensity based on time of day"""
        # Calculate color temperature
        if self._time_of_day < 0.25:  # Morning
            t = self._time_of_day * 4
            self.color = lerp(color.rgb(255, 200, 150), self._base_color, t)
            self._intensity = lerp(0.5, 1.0, t)
        elif self._time_of_day < 0.75:  # Day
            self.color = self._base_color
            self._intensity = 1.0
        else:  # Evening
            t = (self._time_of_day - 0.75) * 4
            self.color = lerp(self._base_color, color.rgb(255, 150, 100), t)
            self._intensity = lerp(1.0, 0.5, t)
            
        # Update shadow intensity
        self.shadow_intensity = self._intensity * 0.8
        
class LightManager:
    def __init__(self, max_lights: int = 8):
        """Initialize the light manager with a maximum number of active lights"""
        self.max_lights = max_lights
        self.lights: List[Entity] = []
        self.light_configs: Dict[Entity, Dict] = {}
        self.enabled = True
        
    def add_sun_light(self,
                    direction: Vec3 = Vec3(1, -1, -1),
                    shadows: bool = True) -> Optional[SunLight]:
        """Add a sunlight to the scene"""
        if len(self.lights) >= self.max_lights:
            print("Warning: Maximum number of lights reached")
            return None
            
        light = SunLight()
        light.look_at(direction)
        light.shadows = shadows
        
        # Store configuration for later adjustment
        self.light_configs[light] = {
            'type': 'sun',
            'direction': direction,
            'shadows': shadows
        }
        
        self.lights.append(light)
        return light
        
    def add_directional_light(self, 
                            direction: Vec3 = Vec3(1, -1, -1),
                            color: Color = color.white,
                            shadows: bool = True,
                            intensity: float = 1.0) -> Optional[DirectionalLight]:
        """Add a directional light to the scene"""
        if len(self.lights) >= self.max_lights:
            print("Warning: Maximum number of lights reached")
            return None
            
        light = DirectionalLight()
        light.look_at(direction)
        light.color = color
        light.shadows = shadows
        
        # Store configuration for later adjustment
        self.light_configs[light] = {
            'type': 'directional',
            'direction': direction,
            'color': color,
            'shadows': shadows,
            'intensity': intensity
        }
        
        self.lights.append(light)
        return light
        
    def add_point_light(self,
                       position: Vec3,
                       color: Color = color.white,
                       shadows: bool = False,
                       intensity: float = 1.0,
                       range: float = 100) -> Optional[PointLight]:
        """Add a point light to the scene"""
        if len(self.lights) >= self.max_lights:
            print("Warning: Maximum number of lights reached")
            return None
            
        light = PointLight()
        light.position = position
        light.color = color
        light.shadows = shadows
        
        # Store configuration
        self.light_configs[light] = {
            'type': 'point',
            'position': position,
            'color': color,
            'shadows': shadows,
            'intensity': intensity,
            'range': range
        }
        
        self.lights.append(light)
        return light
        
    def add_ambient_light(self,
                         color: Color = color.rgba(0.1, 0.1, 0.1, 1.0),
                         intensity: float = 0.1) -> Optional[AmbientLight]:
        """Add ambient light to the scene"""
        if len(self.lights) >= self.max_lights:
            print("Warning: Maximum number of lights reached")
            return None
            
        light = AmbientLight()
        light.color = color
        
        # Store configuration
        self.light_configs[light] = {
            'type': 'ambient',
            'color': color,
            'intensity': intensity
        }
        
        self.lights.append(light)
        return light
        
    def remove_light(self, light: Entity) -> bool:
        """Remove a light from the scene"""
        if light in self.lights:
            self.lights.remove(light)
            self.light_configs.pop(light)
            destroy(light)
            return True
        return False
        
    def attach_to_entity(self, light: Entity, entity: Entity) -> bool:
        """Parent a light to an entity for dynamic movement"""
        if light in self.lights:
            light.parent = entity
            return True
        return False
        
    def set_intensity(self, light: Entity, intensity: float) -> bool:
        """Adjust the intensity of a light"""
        if light in self.light_configs:
            config = self.light_configs[light]
            config['intensity'] = intensity
            # Apply intensity through color modification
            original_color = config['color']
            light.color = Color(
                original_color.r * intensity,
                original_color.g * intensity,
                original_color.b * intensity,
                original_color.a
            )
            return True
        return False
        
    def toggle_shadows(self, light: Entity, enabled: bool) -> bool:
        """Toggle shadows for a specific light"""
        if light in self.light_configs:
            light.shadows = enabled
            self.light_configs[light]['shadows'] = enabled
            return True
        return False
        
    def toggle_all_lights(self, enabled: bool = True):
        """Enable or disable all lights"""
        self.enabled = enabled
        for light in self.lights:
            light.enabled = enabled
            
    def create_light_effect(self, light: Entity, effect_type: str, **params):
        """Create special light effects (flickering, pulsing, etc.)"""
        if light not in self.light_configs:
            return
            
        if effect_type == 'flicker':
            min_intensity = params.get('min_intensity', 0.5)
            max_intensity = params.get('max_intensity', 1.0)
            speed = params.get('speed', 1.0)
            
            def update_flicker():
                t = time.time() * speed
                intensity = lerp(min_intensity, max_intensity, 
                               (noise.pnoise1(t) + 1) / 2)
                self.set_intensity(light, intensity)
                
            light.update = update_flicker
            
        elif effect_type == 'pulse':
            min_intensity = params.get('min_intensity', 0.2)
            max_intensity = params.get('max_intensity', 1.0)
            speed = params.get('speed', 1.0)
            
            def update_pulse():
                t = time.time() * speed
                intensity = lerp(min_intensity, max_intensity, 
                               (math.sin(t) + 1) / 2)
                self.set_intensity(light, intensity)
                
            light.update = update_pulse
            
    def update(self):
        """Update method called every frame"""
        if not self.enabled:
            return
            
        # Update any dynamic light effects
        for light in self.lights:
            if hasattr(light, 'update'):
                light.update()