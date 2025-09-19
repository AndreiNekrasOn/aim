# entities/manufacturing/conveyor.py

from typing import List, Tuple, Any
from aim.core.space import SpatialEntity

Point3D = Tuple[float, float, float]

class Conveyor(SpatialEntity):
    """
    A linear path in 3D space defined by waypoints.
    Agents move along it at a fixed speed.
    """

    def __init__(self, points: List[Point3D], speed: float = 1.0, name: str = ""):
        if len(points) < 2:
            raise ValueError("Conveyor must have at least 2 points.")
        self.points = points
        self.speed = speed
        self.name = name
        self.connections: List['SpatialEntity'] = []  # Connected entities (conveyors, turntables, etc.)
        self._total_length = None

    def get_total_length(self) -> float:
        """Calculate total length of the conveyor path."""
        if self._total_length is None:
            total = 0.0
            for i in range(len(self.points) - 1):
                p1 = self.points[i]
                p2 = self.points[i + 1]
                seg_len = (
                    (p2[0] - p1[0])**2 +
                    (p2[1] - p1[1])**2 +
                    (p2[2] - p1[2])**2
                ) ** 0.5
                total += seg_len
                self._total_length = total
        return self._total_length

    def get_position_at_progress(self, progress: float) -> Point3D:
        """Get 3D position at normalized progress (0.0 to 1.0)."""
        if progress <= 0.0:
            return self.points[0]
        if progress >= 1.0:
            return self.points[-1]

        total_length = self.get_total_length()
        if total_length == 0:
            return self.points[0]

        target_distance = progress * total_length
        accumulated = 0.0

        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            seg_len = (
                (p2[0] - p1[0])**2 +
                (p2[1] - p1[1])**2 +
                (p2[2] - p1[2])**2
            ) ** 0.5

            if accumulated + seg_len >= target_distance:
                local_progress = (target_distance - accumulated) / seg_len
                return (
                    p1[0] + local_progress * (p2[0] - p1[0]),
                    p1[1] + local_progress * (p2[1] - p1[1]),
                    p1[2] + local_progress * (p2[2] - p1[2]),
                )
            accumulated += seg_len

        return self.points[-1]

    def __lt__(self, other: Any) -> bool:
        """
        For heapq — break ties by name or id.
        """
        if not isinstance(other, Conveyor):
            return NotImplemented
        # Compare by name first, then id for stability
        if self.name != other.name:
            return self.name < other.name
        return id(self) < id(other)
