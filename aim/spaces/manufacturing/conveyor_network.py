# spaces/manufacturing/conveyor_network.py

from __future__ import annotations

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from aim.core.space import Space, SpatialEntity

if TYPE_CHECKING:
    from aim.entities.manufacturing.conveyor import Conveyor

class ConveyorNetwork(Space):
    """
    A specialized Space that manages one or more Conveyors.
    Agents move along conveyors; their 'position' is interpreted as progress (0.0 to 1.0).
    Supports registration, movement, and ejection of agents.
    Multiple ConveyorNetworks can coexist in one simulation.
    """

    def __init__(self):
        super().__init__()
        self.conveyors: List[Conveyor] = []
        # Track which agent is on which conveyor
        self._agent_conveyor_map: Dict[SpatialEntity, Conveyor] = {}
        # Track progress of each agent (0.0 = start, 1.0 = end)
        self._agent_progress: Dict[SpatialEntity, float] = {}

    def add_conveyor(self, conveyor: Conveyor) -> None:
        """
        Add a conveyor to this network.
        Called by user during setup — not during simulation tick.
        """
        if conveyor not in self.conveyors:
            self.conveyors.append(conveyor)
            conveyor.network = self  # back-reference

    def register(self, entity: SpatialEntity) -> bool:
        """
        Register an agent with this space — only if placed on a conveyor.
        Entity must be assigned to a specific conveyor externally (e.g., by ConveyorBlock).
        Returns False if entity is already registered or no conveyor assigned.
        """
        # For now, assume entity is assigned to a conveyor via external logic
        # (e.g., Conveyor.try_place_agent sets entity._assigned_conveyor)
        assigned_conveyor = getattr(entity, '_assigned_conveyor', None)

        if not assigned_conveyor:
            return False  # no conveyor assigned — cannot register

        if assigned_conveyor not in self.conveyors:
            return False  # conveyor not part of this network

        if entity in self._agent_conveyor_map:
            return False  # already registered

        # Register agent
        self._agent_conveyor_map[entity] = assigned_conveyor
        self._agent_progress[entity] = 0.0
        entity.space = self
        entity.position = 0.0  # start of conveyor

        return True

    def unregister(self, entity: SpatialEntity) -> bool:
        """
        Unregister an agent from this space.
        Cleans up progress and mapping.
        """
        if entity not in self._agent_conveyor_map:
            return False

        del self._agent_conveyor_map[entity]
        del self._agent_progress[entity]
        entity.space = None
        entity.position = None
        return True

    def update(self, delta_time: float = 1.0) -> None:
        """
        Advance all agents in this network by delta_time ticks.
        Moves agents along their conveyor.
        Ejects agents that reach progress >= 1.0.
        """
        # First, advance all agents and collect ejected ones per conveyor
        ejected_by_conveyor: Dict[Conveyor, List[SpatialEntity]] = {conv: [] for conv in self.conveyors}

        for agent in list(self._agent_conveyor_map.keys()):
            conveyor = self._agent_conveyor_map[agent]
            progress = self._agent_progress[agent]

            new_progress = progress + (conveyor.speed * delta_time)

            if new_progress >= 1.0:
                # Mark for ejection
                ejected_by_conveyor[conveyor].append(agent)
                # Do NOT unregister yet — let conveyor handle it after callback
            else:
                self._agent_progress[agent] = new_progress
                agent.position = new_progress

        # Now, unregister ejected agents and notify conveyors
        for conveyor, agents in ejected_by_conveyor.items():
            if agents:
                # Notify conveyor first (while agents are still registered)
                conveyor._on_agents_ejected(agents)
                # Then unregister them
                for agent in agents:
                    self.unregister(agent)

    def find_entities(self, query: Any) -> List[SpatialEntity]:
        """
        For MVP: return all agents in this network.
        Later: support spatial queries (e.g., agents near point, on specific conveyor).
        """
        return list(self._agent_conveyor_map.keys())

    def get_progress(self, agent: SpatialEntity) -> Optional[float]:
        """Get current progress of agent (0.0 to 1.0), or None if not registered."""
        return self._agent_progress.get(agent)

    def get_conveyor_for_agent(self, agent: SpatialEntity) -> Optional[Conveyor]:
        """Get the conveyor an agent is currently on, or None."""
        return self._agent_conveyor_map.get(agent)
