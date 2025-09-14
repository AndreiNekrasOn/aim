# core/space.py

from typing import Dict, Any, Protocol, Optional
from .agent import BaseAgent

class SpatialEntity(Protocol):
    """
    Protocol for any object that can exist in a SpaceManager.
    Not a base class — just a duck-typed interface.
    """
    pass

class SpaceManager:
    """
    Abstract base class for all spatial systems.
    Manages agent position, movement, and collision within a space.
    """

    def register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool:
        """
        Register an agent with this space.
        Returns False if agent cannot be placed (e.g., collision).
        """
        raise NotImplementedError

    def unregister(self, agent: BaseAgent) -> bool:
        """
        Unregister an agent from this space.
        Returns False if agent was not registered.
        """
        raise NotImplementedError

    def update(self, delta_time: float) -> None:
        """
        Advance all agents in this space by delta_time.
        Moves agents, checks collisions, updates state.
        """
        raise NotImplementedError

    def get_state(self, agent: BaseAgent) -> Dict[str, Any]:
        """
        Get current space-specific state of agent.
        Examples: {"progress": 0.5}, {"position": (x, y, z)}
        """
        raise NotImplementedError

    def is_movement_complete(self, agent: BaseAgent) -> bool:
        """
        Check if agent has completed its current movement (e.g., reached end of path).
        """
        raise NotImplementedError
