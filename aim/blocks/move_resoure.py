from typing import Any, Optional
from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.core.simulator import Simulator
from aim.entities.resource import ResourceAgent

class MoveResourcelock(BaseBlock):
    """
    Moves resource_agent belonging to the agents from start_position to target_position in the space.
    Enforces one agent per tick.
    """

    def __init__(
        self,
        simulator: Simulator,
        space_name: str,
        speed: float = 1.0
    ):
        """
        Initialize MoveBlock.
        :param simulator: Simulator instance.
        :param space_name: Name of space to use.
        :param speed: Default speed for agents (can be overridden per agent).
        """
        super().__init__(simulator)
        self.space_name = space_name
        self.space = simulator.get_space(space_name)
        self.default_speed = speed
        self._agent_entered_this_tick = False

    def take(self, agent: BaseAgent) -> None:
        """
        Place agent in space at start_position.
        Expects agent to have .start_position and .target_position attributes.
        """
        if self._agent_entered_this_tick:
            raise RuntimeError(f"MoveBlock: only one agent per tick allowed.")

        if not hasattr(agent, "resource_agent"):
            raise RuntimeError("Agent must have attached resource_agent as an attribute.")

        start_position = agent.resource_agent.properties['start_position']
        target_position = agent.resource_agent.properties['target_position']
        speed = agent.resource_agent.properties['speed']
        if start_position == None or target_position == None:
            raise RuntimeError("Agent's resource_agent must have start_position and target_position attributes.")

        self._agent_entered_this_tick = True

        initial_state = {
            "start_position": start_position,
            "target_position": target_position,
            "speed": speed or default_speed
        }

        if not self.space.register(agent.resource_agent, initial_state):
            raise RuntimeError(f"MoveResourceBlock: agent {id(agent.resource_agent)} rejected by space")

        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)

        self._agents.append(agent)

    def _tick(self) -> None:
        """
        Advance space -- and eject agents that have completed movement.
        """
        self._agent_entered_this_tick = False

        completed_agents = []
        for agent in self._agents:
            if self.space.is_movement_complete(agent.resource_agent):
                completed_agents.append(agent)

        for agent in completed_agents:
            self._eject(agent)
            self._agents.remove(agent)

