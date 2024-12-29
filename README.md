# Solar System Simulation

A 3D simulation of the Solar System built using Python and the Ursina engine.

## Installation

1. Ensure you have Python 3.7 or higher installed
2. Install the required dependencies:

```bash
pip install ursina
```

## Running the Simulation

Navigate to the project directory and run:

```bash
python main.py
```

## Controls

- Right click + drag: Rotate camera
- Scroll wheel: Zoom in/out

## Project Structure

- `main.py`: Entry point for the simulation
- `game_manager.py`: Manages the overall game state
- `celestial_bodies.py`: Contains classes for celestial bodies
- `orbits.py`: Handles orbital mechanics
- `assets_manager.py`: Manages textures and other assets
- `constants.py`: Stores configuration parameters
- `ui_manager.py`: Handles user interface and controls
- `utilities.py`: Contains helper functions

## Future Improvements

- Add more planets and moons
- Implement realistic orbital mechanics
- Add informational HUD elements
- Include sound effects and background music
- Implement time controls (pause, speed up, slow down)