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
                    print("Update loop running")  # Debug print
                    game_manager.update()
                    ui_manager.update()  # Update UI elements including FPS counter
                    if game_manager.selector.selected_entity:
                        ui_manager.update_selected_info(game_manager.selector.selected_entity)
                except Exception as e:
                    print(f"Error in update loop: {str(e)}")
                    traceback.print_exc()
        
        # Create game loop entity
        game_loop = GameLoop()
                
        def on_shutdown():
            """Cleanup handler for application shutdown"""
            print("Shutting down simulation...")
            if game_manager:
                try:
                    game_manager.cleanup()
                except Exception as e:
                    print(f"Error during cleanup: {str(e)}")
                    traceback.print_exc()
            print("Cleanup complete")
            
        # Create game loop entity
        print("Creating game loop entity")
        game_loop = GameLoop()
        print("Game loop entity created")
        
        # Register cleanup handler
        application.on_shutdown = on_shutdown
        
        # Enable update loop and manually step the application
        application.do_update = True
        print("Manually stepping application")
        application.step()
        print("Application stepped")
        
        # Run the application
        print("Starting application")
        application.run()
        print("Application started")
        
        # Manually call update in a loop
        while True:
            update()
            application.step()
            time.sleep(1/60)  # Target 60 FPS
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
        
    finally:
        # Ensure cleanup runs even if an error occurred during setup
        if game_manager:
            try:
                game_manager.cleanup()
            except Exception as e:
                print(f"Error during emergency cleanup: {str(e)}")
                traceback.print_exc()
        
        # Exit with error code if we caught an exception
        if sys.exc_info()[0] is not None:
            sys.exit(1)

if __name__ == "__main__":
    main()