# entities/manufacturing/conveyor.py

from __future__ import annotations

from typing import List, Tuple, Optional, Any
from aim.core.space import SpatialEntity
from aim.spaces.manufacturing.conveyor_network import ConveyorNetwork  # type: ignore

from typing import List, Tuple, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aim.spaces.manufacturing.conveyor_network import ConveyorNetwork

Point3D = Tuple[float, float, float]

class Conveyor:
    """
    A spatial entity representing a conveyor with a 3D polyline path.
    Agents move along it from start (progress 0.0) to end (progress 1.0).
    Belongs to exactly one ConveyorNetwork.
    Does not manage agent state directly — delegates to ConveyorNetwork.
    """

    def __init__(
        self,
        points: List[Point3D],
        speed: float = 0.1,
        name: str = "",
        block: Optional['ConveyorBlock'] = None  # ← ADD THIS
    ):
        """
        :param points: List of 3D waypoints defining the conveyor path.
        :param speed: Progress increment per tick (e.g., 0.1 = 10% per tick).
        :param name: Optional identifier.
        """
        if len(points) < 2:
            raise ValueError("Conveyor must have at least 2 points.")

        self.block = block  # ← store reference        """
        self.points = points
        self.speed = speed
        self.name = name
        self.network: Optional[ConveyorNetwork] = None  # assigned when added to network

        # For internal use: agents waiting to be placed (if network is full or busy)
        self._waiting_agents: List[Any] = []

    def try_place_agent(self, agent: SpatialEntity) -> bool:
        """
        Attempt to place an agent at the start of this conveyor.
        Delegates to ConveyorNetwork.register().
        If network rejects, agent is queued internally for retry next tick.
        Returns True if placed immediately, False if queued or rejected permanently.
        """
        if self.network is None:
            return False  # not attached to any network

        # Mark agent as assigned to this conveyor
        agent._assigned_conveyor = self  # type: ignore

        if self.network.register(agent):
            return True
        else:
            # Queue for retry next tick (optional — or let upstream block handle)
            self._waiting_agents.append(agent)
            return False

    def _on_agents_ejected(self, agents: List[SpatialEntity]) -> None:
        """
        Called by ConveyorNetwork when agents reach end of conveyor.
        Override to trigger events, logging, or custom logic.
        """
        if self.block:
            for agent in agents:
                self.block._eject_agent(agent)  # type: ignore

    def get_position_at_progress(self, progress: float) -> Point3D:
        """
        Map normalized progress (0.0 to 1.0) to a 3D point along the polyline.
        Uses linear interpolation between waypoints.
        """
        if progress <= 0.0:
            return self.points[0]
        if progress >= 1.0:
            return self.points[-1]

        total_length = 0.0
        segment_lengths = []

        # Precompute segment lengths
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            seg_len = (
                (p2[0] - p1[0])**2 +
                (p2[1] - p1[1])**2 +
                (p2[2] - p1[2])**2
            ) ** 0.5
            segment_lengths.append(seg_len)
            total_length += seg_len

        if total_length == 0:
            return self.points[0]

        target_distance = progress * total_length
        accumulated = 0.0

        for i in range(len(segment_lengths)):
            seg_len = segment_lengths[i]
            if accumulated + seg_len >= target_distance:
                # Interpolate within this segment
                p1 = self.points[i]
                p2 = self.points[i + 1]
                local_progress = (target_distance - accumulated) / seg_len
                return (
                    p1[0] + local_progress * (p2[0] - p1[0]),
                    p1[1] + local_progress * (p2[1] - p1[1]),
                    p1[2] + local_progress * (p2[2] - p1[2]),
                )
            accumulated += seg_len

        return self.points[-1]

    def tick(self) -> None:
        """
        Called by ConveyorBlock or externally — retries placing waiting agents.
        Optional: can be auto-triggered via network or simulator later.
        """
        if self.network is None:
            return

        # Retry placing waiting agents
        still_waiting = []
        for agent in self._waiting_agents:
            if not self.try_place_agent(agent):
                still_waiting.append(agent)
        self._waiting_agents = still_waiting
