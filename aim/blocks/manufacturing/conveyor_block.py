# blocks/manufacturing/conveyor_block.py

from typing import Optional, Any
from aim.core import simulator
from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.core.space import SpaceManager
from aim.core.simulator import Simulator

class ConveyorBlock(BaseBlock):
    """
    Block that moves agents through a ConveyorSpace from start_entity to end_entity.
    Does NOT eject agents when movement is complete — must use ConveyorExit.

    Enforces one agent entry per tick — subsequent agents in same tick are rejected.
    This prevents within-tick collision races and matches discrete-event semantics.
    """

    def __init__(
        self,
        simulator: 'Simulator',
        space: SpaceManager,
        start_entity: Any,
        end_entity: Any
    ):
        super().__init__(simulator)
        self.space = space
        self.start_entity = start_entity
        self.end_entity = end_entity

        self._agent_entered_this_tick = False

        # Validate space supports entity registration
        if not hasattr(space, 'is_entity_registered'):
            raise TypeError(f"Space {type(space).__name__} does not support entity registration. "
                            f"Expected a ConveyorSpace or compatible SpaceManager.")

        # Validate entities are registered
        if not space.is_entity_registered(start_entity):
            raise ValueError(f"start_entity {start_entity} is not registered with the space. "
                             f"Did you forget to call space.register_entity(start_entity)?")

        if not space.is_entity_registered(end_entity):
            raise ValueError(f"end_entity {end_entity} is not registered with the space. "
                             f"Did you forget to call space.register_entity(end_entity)?")

    def take(self, agent: BaseAgent) -> None:
        """
        Place agent in space at start_entity.
        Rejects agent if cannot be placed (e.g., collision).
        """
        if self._agent_entered_this_tick:
            raise RuntimeError(f"ConveyorBlock: agent {id(agent)} rejected, only one per tick may enter")
        agent._enter_block(self)
        self._agent_entered_this_tick = True
        if self.on_enter is not None:
            self.on_enter(agent)

        initial_state = {
            "start_entity": self.start_entity,
            "end_entity": self.end_entity
        }
        if not self.space.register(agent, initial_state):
            raise RuntimeError(f"ConveyorBlock: agent {id(agent)} rejected by space")

        # Add to internal list — will be held until ConveyorExit
        self._agents.append(agent)

    def _tick(self) -> None:
        """
        Advance space — and eject agents that have completed movement.
        """
        # Movement is handled by space.update() — called by Simulator before block._tick()

        self._agent_entered_this_tick = False

        # Check each agent to see if movement is complete
        completed_agents = []
        for agent in self._agents:
            state = self.space._agent_movement[agent]
            if self.space.is_movement_complete(agent):
                completed_agents.append(agent)

        # Eject completed agents
        for agent in completed_agents:
            self._eject(agent)
            self._agents.remove(agent)
