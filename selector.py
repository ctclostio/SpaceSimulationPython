from ursina import *

class Selector:
    def __init__(self):
        """Initialize the selector."""
        self.selected_entity = None

    def register_clickable(self, entity):
        """Mark an entity as clickable."""
        entity.is_clickable = True

    def update(self):
        """Check for mouse clicks and select entities."""
        if mouse.left and mouse.hovered_entity and getattr(mouse.hovered_entity, 'is_clickable', False):
            self.select_entity(mouse.hovered_entity)

    def select_entity(self, entity):
        """Handle selection logic."""
        if self.selected_entity:
            self.deselect_entity(self.selected_entity)
        self.selected_entity = entity
        print(f"Selected: {entity.name}")
        # Highlight the entity visually
        entity.color = color.red

    def deselect_entity(self, entity):
        """Handle deselection logic."""
        print(f"Deselected: {entity.name}")
        # Reset the entity's color or other properties
        entity.color = color.white