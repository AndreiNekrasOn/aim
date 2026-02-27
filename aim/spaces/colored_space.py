"""
Visual space for colored rectangles rendered as flat prisms.
Purely for visualization — no movement, no collision detection.

Rectangles stored as _obstacles (same pattern as CollisionSpace) for viewer compatibility.
"""

from typing import Dict, Any, List, Optional, Tuple
from aim.core.space import SpaceManager
from aim.core.agent import BaseAgent

Point3D = Tuple[float, float, float]
ColoredPrism = Tuple[List[Point3D], float, Tuple[int, int, int], int]  # (base_points, height, color, alpha)


class ColoredRectangle:
    """
    Visual rectangle represented as a flat prism (height=0).
    Position (x, y) is the center, z is the bottom level.
    """

    def __init__(
        self,
        rect_id: str,
        x: float,
        y: float,
        z: float,
        width: float,
        depth: float,
        color: Tuple[int, int, int],
        alpha: int = 255,
        label: Optional[str] = None,
        visible: bool = True
    ):
        self.id = rect_id
        self.x = x  # Center X
        self.y = y  # Center Y
        self.z = z  # Bottom Z
        self.width = width
        self.depth = depth
        self.color = color  # RGB
        self.alpha = alpha  # 0-255, 255 = opaque
        self.label = label
        self.visible = visible

    def to_prism(self) -> Tuple[List[Point3D], float]:
        """
        Convert to prism format for Pygame3DViewer.
        Returns base polygon points and height (0 for flat rectangle).
        """
        half_w = self.width / 2
        half_d = self.depth / 2

        # Base polygon (counter-clockwise from bottom-left)
        base_points = [
            (self.x - half_w, self.y - half_d, self.z),  # Bottom-left
            (self.x + half_w, self.y - half_d, self.z),  # Bottom-right
            (self.x + half_w, self.y + half_d, self.z),  # Top-right
            (self.x - half_w, self.y + half_d, self.z),  # Top-left
        ]

        return (base_points, 0.0)  # Height = 0 for flat rectangle


class ColoredSpace(SpaceManager):
    """
    Visual space for colored rectangles.
    Rectangles stored as _obstacles list (same pattern as CollisionSpace).

    No movement logic — purely for visualization.
    """

    def __init__(self, obstacles: Optional[List[ColoredRectangle]] = None):
        """
        Initialize ColoredSpace with optional static obstacles.

        :param obstacles: List of ColoredRectangle to add at initialization
                          (e.g., storage units, avenues, parts)
        """
        # List of (base_points, height, color, alpha) tuples
        self._obstacles: List[ColoredPrism] = []
        self._agent_visuals: Dict[BaseAgent, str] = {}
        self._rect_ids: Dict[str, int] = {}  # rect_id -> index in _obstacles

        # Add static obstacles from constructor
        if obstacles:
            for rect in obstacles:
                self._add_rectangle(rect)

    # === SpaceManager Contract ===

    def register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool:
        """
        Register agent with a colored rectangle.

        initial_state expected keys:
        - "rectangle": ColoredRectangle

        Returns True if successful.
        """
        rect = initial_state.get("rectangle")
        if not rect or not isinstance(rect, ColoredRectangle):
            return False

        if rect.id in self._rect_ids:
            return False  # ID already exists

        # Convert to prism format with color/alpha
        base_points, height = rect.to_prism()
        prism: ColoredPrism = (base_points, height, rect.color, rect.alpha)

        self._obstacles.append(prism)
        self._rect_ids[rect.id] = len(self._obstacles) - 1
        self._agent_visuals[agent] = rect.id
        return True

    def unregister(self, agent: BaseAgent) -> bool:
        """
        Unregister agent and remove its rectangle.
        Returns True if agent was registered.
        """
        if agent not in self._agent_visuals:
            return False

        rect_id = self._agent_visuals[agent]
        if rect_id in self._rect_ids:
            idx = self._rect_ids[rect_id]
            self._obstacles[idx] = None  # Mark for removal
            del self._rect_ids[rect_id]

        del self._agent_visuals[agent]
        return True

    def update(self, delta_time: float) -> None:
        """No-op — static visualization."""
        pass

    def get_state(self, agent: BaseAgent) -> Dict[str, Any]:
        """
        Get agent's visual state.
        Returns dict with rectangle info, or {} if not registered.
        """
        if agent not in self._agent_visuals:
            return {}

        rect_id = self._agent_visuals[agent]
        if rect_id not in self._rect_ids:
            return {}

        idx = self._rect_ids[rect_id]
        if idx >= len(self._obstacles) or self._obstacles[idx] is None:
            return {}

        base_points, height, color, alpha = self._obstacles[idx]
        # Calculate center from base_points
        center_x = sum(p[0] for p in base_points) / 4
        center_y = sum(p[1] for p in base_points) / 4
        center_z = base_points[0][2]

        return {
            "rectangle_id": rect_id,
            "position": (center_x, center_y, center_z),
            "color": color,
            "alpha": alpha,
            "visible": True
        }

    def is_movement_complete(self, agent: BaseAgent) -> bool:
        """Always True — no movement."""
        return True

    # === Internal Methods ===

    def _add_rectangle(self, rect: ColoredRectangle) -> None:
        """Add rectangle directly (used for static obstacles)."""
        base_points, height = rect.to_prism()
        prism: ColoredPrism = (base_points, height, rect.color, rect.alpha)

        self._obstacles.append(prism)
        self._rect_ids[rect.id] = len(self._obstacles) - 1
