"""
assets_loader.py - Threaded asset loading implementation

This module provides asynchronous loading of assets using threading to prevent
frame drops during texture loading operations.
"""

from threading import Lock
from queue import Queue, Empty
import time
from ursina import load_texture
from assets_manager import AssetsManager
from constants import *

class AssetLoader:
    def __init__(self, stop_event):
        """
        Initialize the asset loader.
        
        Args:
            stop_event (threading.Event): Event to signal thread termination
        """
        self.stop_event = stop_event
        self.assets_manager = AssetsManager()
        self.lock = Lock()
        self.load_queue = Queue()
        self.loaded_textures = {}
        
        # Define texture mapping
        self.texture_mapping = {
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

    def queue_texture_load(self, name, path):
        """
        Queue a texture for loading.
        
        Args:
            name (str): Name of the texture
            path (str): Path to the texture file
        """
        self.load_queue.put((name, path))

    def run(self):
        """Run the asset loading thread."""
        # First, queue all known textures
        for name, path in self.texture_mapping.items():
            self.queue_texture_load(name, path)
        
        # Process the queue until stopped
        while not self.stop_event.is_set():
            try:
                # Non-blocking queue check
                name, path = self.load_queue.get_nowait()
                
                try:
                    texture = load_texture(path)
                    with self.lock:
                        self.loaded_textures[name] = texture
                except Exception as e:
                    print(f"Error loading texture for {name}: {str(e)}")
                    # Don't set a fallback texture here - let the main thread handle that
                
                self.load_queue.task_done()
                
            except Empty:
                # No more textures to load, sleep briefly
                time.sleep(0.1)  # time is already imported at the top

    def update_assets_manager(self):
        """
        Update the AssetsManager with any newly loaded textures.
        This should be called from the main thread.
        """
        with self.lock:
            for name, texture in self.loaded_textures.items():
                self.assets_manager.textures[name] = texture
            self.loaded_textures.clear()

    def is_loading_complete(self):
        """
        Check if all textures have been loaded.
        
        Returns:
            bool: True if all textures are loaded, False otherwise
        """
        return self.load_queue.empty() and not self.loaded_textures

class ThreadedAssetsManager:
    """Thread-safe version of AssetsManager that works alongside the base singleton"""
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ThreadedAssetsManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the threaded assets manager"""
        if self._initialized:
            return
            
        self._initialized = True
        self.base_manager = AssetsManager()  # Get the singleton instance
        self.asset_loader = None  # Will be set up after thread manager is available
        self.lock = Lock()

    def setup_threading(self, thread_manager):
        """
        Set up threading components after initialization.
        
        Args:
            thread_manager (ThreadManager): The thread manager instance
        """
        if self.asset_loader is None:
            self.asset_loader = AssetLoader(thread_manager.stop_event)
            thread_manager.add_thread(target=self.asset_loader.run)

    def update(self):
        """Update with any newly loaded assets"""
        if self.asset_loader:
            self.asset_loader.update_assets_manager()

    def get_texture(self, name):
        """Thread-safe texture retrieval"""
        with self.lock:
            return self.base_manager.get_texture(name)