# blocks/combine.py

from typing import List, Optional, Callable
from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from ..core.simulator import Simulator

class _CombineInputPort:
    """Internal port that forwards agents to CombineBlock."""
    def __init__(self, parent: 'CombineBlock', port_name: str):
        self.parent = parent
        self.port_name = port_name

    def take(self, agent: BaseAgent) -> None:
        if self.port_name == "container":
            self.parent._handle_container(agent)
        elif self.port_name == "pickup":
            self.parent._handle_pickup(agent)

class CombineBlock(BaseBlock):
    """
    Combines one container with N pickups.
    - Accepts one container at a time.
    - Collects up to N pickups (queued internally).
    - Ejects container when N pickups are collected.
    - Rejects excess containers/pickups (upstream QueueBlock must handle).
    """

    def __init__(self, simulator: 'Simulator', max_pickups: int = 1):
        super().__init__(simulator)
        self.max_pickups = max_pickups
        self.container = _CombineInputPort(self, "container")
        self.pickup = _CombineInputPort(self, "pickup")
        self._held_container: Optional[BaseAgent] = None
        self._pickup_queue: List[BaseAgent] = []


    def take(self, agent: BaseAgent) -> None:
        raise RuntimeError("Can't take for CombineBlock")


    def _handle_container(self, agent: BaseAgent) -> None:
        """Handle incoming container."""
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)

        if self._held_container is not None:
            # Reject — container already held
            raise RuntimeError(f"CombineBlock {id(self)} already holds a container. Use QueueBlock upstream.")
        self._held_container = agent

    def _handle_pickup(self, agent: BaseAgent) -> None:
        """Handle incoming pickup."""
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)

        if self._held_container is None:
            # No container — queue pickup if under limit
            if len(self._pickup_queue) < self.max_pickups:
                self._pickup_queue.append(agent)
            else:
                # Reject — queue full
                raise RuntimeError(f"CombineBlock {id(self)} pickup queue full. Use QueueBlock upstream.")
        else:
            # Container held — add pickup
            self._add_pickup_to_container(agent)

    def _add_pickup_to_container(self, pickup: BaseAgent) -> None:
        """Add pickup to container. Eject if full."""
        # Ensure container has children_agents list
        if not hasattr(self._held_container, 'children_agents'):
            self._held_container.children_agents = []
        if not hasattr(pickup, 'parent_agents'):
            pickup.parent_agents = []

        # Link parent/children
        self._held_container.children_agents.append(pickup)
        pickup.parent_agents.append(self._held_container)

        # Check if container is full
        if len(self._held_container.children_agents) >= self.max_pickups:
            self._eject(self._held_container)
            self._held_container = None
            # Process queued pickups if new container arrives later — not now

    def _tick(self) -> None:
        """Try to assign queued pickups to held container."""
        if self._held_container is None:
            return

        while self._pickup_queue and len(self._held_container.children_agents) < self.max_pickups:
            pickup = self._pickup_queue.pop(0)
            self._add_pickup_to_container(pickup)

    @property
    def container_held(self) -> bool:
        return self._held_container is not None

    @property
    def pickup_queue_size(self) -> int:
        return len(self._pickup_queue)
