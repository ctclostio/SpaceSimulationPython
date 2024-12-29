"""
assets_manager.py - Manages loading and storage of assets

This module handles the loading and management of all assets used in the simulation,
including textures, models, and sounds. It provides a centralized way to access
and manage these resources.

The AssetsManager class implements the Singleton pattern to ensure only one
instance exists throughout the application.
"""

from ursina import load_texture
from constants import *

class AssetsManager:
    _instance = None

    def __new__(cls):
        """Implement Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(AssetsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the assets manager"""
        if self._initialized:
            return
        self._initialized = True
        self.textures = {}
        self.load_assets()

    def load_assets(self):
        """Load all required assets"""
        print("\nLoading celestial body textures...")
        # Load textures for all celestial bodies
        texture_mapping = {
            'sun': SUN_TEXTURE,
            'mercury': MERCURY_TEXTURE,
            'venus': VENUS_TEXTURE,
            'earth': EARTH_TEXTURE,
            'mars': MARS_TEXTURE,
            'jupiter': JUPITER_TEXTURE,
            'saturn': SATURN_TEXTURE,
            'uranus': URANUS_TEXTURE,
            'neptune': NEPTUNE_TEXTURE
        }
        
        for name, texture_path in texture_mapping.items():
            try:
                self.textures[name] = load_texture(texture_path)
                print(f"Successfully loaded texture for {name}: {texture_path}")
            except Exception as e:
                print(f"Error loading texture for {name}: {str(e)}")
                # Create a colored entity instead of loading a non-existent default texture
                from ursina import Texture
                self.textures[name] = Texture(name)
                print(f"Using fallback color for {name}")

    def get_texture(self, name):
        """
        Get a loaded texture by name
        
        Args:
            name (str): Name of the texture to retrieve
            
        Returns:
            Texture: The requested texture
        """
        return self.textures.get(name)

    def reload_assets(self):
        """Reload all assets (useful for development)"""
        self.textures.clear()
        self.load_assets()