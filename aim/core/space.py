# core/space.py

from abc import ABC, abstractmethod
from typing import Any, Protocol, Optional, List

# --- PROTOCOL: What it means to be a "spatial entity" ---
# (Not a base class — just for type checking)

class SpatialEntity(Protocol):
    """
    Protocol for any object that can exist in a Space.
    Does NOT require inheritance — just duck-typed attributes.
    """
    # Optional: current space the entity is registered with
    space: Optional['Space']
    # Optional: position — interpretation depends on Space subclass
    position: Any
    # Optional: velocity — interpretation depends on Space subclass
    velocity: Any


# --- ABSTRACT BASE CLASS: Space ---
# All concrete spaces (ConveyorNetwork, Physical3DSpace, etc.) must inherit from this.

class Space(ABC):
    """
    Abstract base class for all spatial or logical containers.
    Defines the minimal interface that all spaces must implement.
    Not a singleton. Not global. Instantiable.
    """

    def __init__(self):
        pass

    @abstractmethod
    def register(self, entity: SpatialEntity) -> bool:
        """
        Register an entity with this space.
        Returns True if successful, False if rejected (e.g., collision, capacity).
        """
        pass

    @abstractmethod
    def unregister(self, entity: SpatialEntity) -> bool:
        """
        Unregister an entity from this space.
        Returns True if removed, False if not found.
        """
        pass

    @abstractmethod
    def update(self, delta_time: float = 1.0) -> None:
        """
        Advance the state of this space by delta_time (in ticks or seconds).
        Moves agents, checks collisions, ejects entities, etc.
        Called once per simulation tick.
        """
        pass

    @abstractmethod
    def find_entities(self, query: Any) -> List[SpatialEntity]:
        """
        Return entities matching a query (e.g., near a point, in a zone).
        Query type and semantics are space-specific.
        For MVP, may return all entities or empty list.
        """
        pass
