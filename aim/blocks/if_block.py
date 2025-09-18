# blocks/if_block.py

from ..core.simulator import Simulator
from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from typing import Callable


class IfBlock(BaseBlock):
    def __init__(self, simulator: Simulator, condition: Callable[[BaseAgent], bool]):
        super().__init__(simulator)
        self.condition = condition
        self.output_connections = [None, None]

    def take(self, agent: BaseAgent) -> bool:
        agent._enter_block(self)
        self._agents.append(agent)
        return True

    def _tick(self) -> None:
        # Process all agents waiting in this block
        while self._agents:
            agent = self._agents.pop(0)
            if self.condition(agent):
                if len(self.output_connections) > 0 and self.output_connections[0]:
                    self.output_connections[0].take(agent)
            else:
                if len(self.output_connections) > 1 and self.output_connections[1]:
                    self.output_connections[1].take(agent)

    def connect_first(self, block: BaseBlock):
        """Connect the 'True' branch."""
        self.output_connections[0] = block

    def connect_second(self, block: BaseBlock):
        """Connect the 'False' branch."""
        self.output_connections[1] = block
