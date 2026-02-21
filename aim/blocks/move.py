from typing import Any, Optional
from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.core.simulator import Simulator

class MoveBlock(BaseBlock):
    """
    Moves agents from start_position to target_position in a space.
    Agents are registered with the space and move toward their target.
    When movement is complete, agents are ejected to the next block.
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

    def take(self, agent: BaseAgent) -> None:
        """
        Place agent in space at start_position.
        Expects agent to have .start_position and .target_position attributes,
        or on_enter callback to set them.
        """
        # Call on_enter callback first to allow it to set start_position and target_position
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)

        if not hasattr(agent, 'start_position') or not hasattr(agent, 'target_position'):
            raise RuntimeError("Agent must have start_position and target_position attributes.")

        initial_state = {
            "start_position": agent.start_position,
            "target_position": agent.target_position,
            "speed": getattr(agent, 'speed', self.default_speed)
        }

        if not self.space.register(agent, initial_state):
            raise RuntimeError(f"MoveBlock: agent {id(agent)} rejected by space")

        self._agents.append(agent)

    def _tick(self) -> None:
        """
        Advance space -- and eject agents that have completed movement.
        """
        completed_agents = []
        for agent in self._agents:
            if self.space.is_movement_complete(agent):
                completed_agents.append(agent)

        for agent in completed_agents:
            self._eject(agent)
            self._agents.remove(agent)
