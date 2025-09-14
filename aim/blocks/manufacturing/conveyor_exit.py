# blocks/manufacturing/conveyor_exit.py

from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.core.space import SpaceManager
from aim.core.simulator import Simulator

class ConveyorExit(BaseBlock):
    """
    Block that removes agents from space.
    Must be used after ConveyorBlock to free space.
    """

    def __init__(self, simulator: 'Simulator', space: SpaceManager):
        super().__init__(simulator)
        self.space = space

    def take(self, agent: BaseAgent) -> None:
        """
        Remove agent from space.
        Rejects if agent is not registered in space.
        """
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)

        if not self.space.unregister(agent):
            raise RuntimeError(f"ConveyorExit: agent {id(agent)} not in space")

        self._eject(agent)
