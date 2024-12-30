from ursina import *
from camera import CameraManager
from celestial_bodies import CelestialBody

app = Ursina()

# Create test celestial bodies
bodies = [
    CelestialBody("Test1", 1, "textures/2k_earth_daymap.jpg", 1),
    CelestialBody("Test2", 1, "textures/2k_mars.jpg", 1),
    CelestialBody("Test3", 1, "textures/2k_jupiter.jpg", 1)
]

# Position bodies at different distances
bodies[0].position = (0, 0, -10)
bodies[1].position = (50, 0, -50)
bodies[2].position = (100, 0, -100)

# Create camera manager
camera_manager = CameraManager()

def update():
    # Check visibility of each body
    for body in bodies:
        if camera_manager.is_visible(body):
            print(f"{body.name} is visible")
        else:
            print(f"{body.name} is culled")

# Run the test
app.run()