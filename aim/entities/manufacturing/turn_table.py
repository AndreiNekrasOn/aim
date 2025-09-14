# entities/manufacturing/turn_table.py

from typing import List
from aim.core.space import SpatialEntity
import math

class TurnTable(SpatialEntity):
    """
    A rotating platform that turns agents by a target angle.
    Movement is angular — speed in radians per tick.
    """

    def __init__(self, radius: float, angular_speed: float, name: str = ""):
        self.radius = radius
        self.angular_speed = angular_speed
        self.name = name
        self.connections: List['SpatialEntity'] = []  # Connected entities

    def get_position_at_angle(self, angle: float) -> tuple:
        """Get 2D position at angle (radians) — assume center at (0,0)."""
        x = self.radius * math.cos(angle)
        y = self.radius * math.sin(angle)
        return (x, y, 0.0)  # Assume z=0 for simplicity

