# blocks/if_block.py

from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from typing import Callable


class IfBlock(BaseBlock):
    def __init__(self, condition: Callable[[BaseAgent], bool]):
        super().__init__()
        self.condition = condition

    def take(self, agent: BaseAgent) -> None:
        agent._enter_block(self)
        self._agents.append(agent)

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
        if len(self.output_connections) < 1:
            self.output_connections.append(None)
        self.output_connections[0] = block

    def connect_second(self, block: BaseBlock):
        """Connect the 'False' branch."""
        if len(self.output_connections) < 2:
            self.output_connections.append(None)
        self.output_connections[1] = block
