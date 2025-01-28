"""
main.py - Entry point for the Solar System simulation

This module initializes the Ursina application and sets up the game environment.
It imports and utilizes the GameManager class to handle the main simulation logic.

Usage:
    python main.py
"""

from ursina import *
from game_manager import GameManager
from ui_manager import UIManager
import sys
import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('camera.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    # Initialize game manager and UI manager outside try block for proper cleanup
    game_manager = None
    ui_manager = None
    
    try:
        # Initialize Ursina application with fixed window size
        application = Ursina(
            fullscreen=False,
            borderless=False,
            window_width=1152,  # Integer instead of float
            window_height=648   # 16:9 aspect ratio
        )
        
        # Set up game manager and UI manager
        game_manager = GameManager()
        ui_manager = UIManager()
        
        class GameLoop(Entity):
            def update(self):
                """Main game loop update function"""
                try:
                    logger.debug("Update loop running")
                    game_manager.update()
                    ui_manager.update()  # Update UI elements including FPS counter
                    if game_manager.selector.selected_entity:
                        ui_manager.update_selected_info(game_manager.selector.selected_entity)
                    
                    # Handle perspective switching
                    if held_keys['1']:
                        game_manager.camera_manager.perspective.switch_perspective('1')
                    if held_keys['2']:
                        game_manager.camera_manager.perspective.switch_perspective('2')
                    if held_keys['3']:
                        game_manager.camera_manager.perspective.switch_perspective('3')
                except Exception as e:
                    logger.error(f"Error in update loop: {str(e)}")
                    logger.error(traceback.format_exc())
        
        # Create game loop entity
        game_loop = GameLoop()
                
        def on_shutdown():
            """Cleanup handler for application shutdown"""
            logger.info("Shutting down simulation...")
            if game_manager:
                try:
                    game_manager.cleanup()
                except Exception as e:
                    logger.error(f"Error during cleanup: {str(e)}")
                    logger.error(traceback.format_exc())
            logger.info("Cleanup complete")
            
        # Register cleanup handler
        application.on_shutdown = on_shutdown
        
        # Run the application
        logger.info("Starting application")
        application.run()
        logger.info("Application started")
        
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        logger.critical(traceback.format_exc())
        
    finally:
        # Ensure cleanup runs even if an error occurred during setup
        if game_manager:
            try:
                game_manager.cleanup()
            except Exception as e:
                logger.error(f"Error during emergency cleanup: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Exit with error code if we caught an exception
        if sys.exc_info()[0] is not None:
            sys.exit(1)

if __name__ == "__main__":

    main()