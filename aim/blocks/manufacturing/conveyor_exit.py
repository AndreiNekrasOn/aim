# blocks/manufacturing/conveyor_exit.py

from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.core.space import SpaceManager
from aim.core.simulator import Simulator

class ConveyorExit(BaseBlock):
    """
    Removes agents from space (frees occupancy).
    Does not unregister agents -- unregistration is handled by ConveyorBlock.
    """

    def __init__(self, simulator: Simulator, space_name: str):
        """
        Initialize ConveyorExit.
        :param simulator: Simulator instance.
        :param space_name: Name of space to use.
        """
        super().__init__(simulator)
        self.space = simulator.get_space(space_name)
        self.space_name = space_name

    def take(self, agent: BaseAgent) -> None:
        """
        Pass agent to next block. Does not interact with space.
        """
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)
        self._eject(agent)
