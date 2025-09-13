# blocks/queue.py

from typing import List, TYPE_CHECKING
from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from ..core.simulator import Simulator


class QueueBlock(BaseBlock):
    """
    Holds agents until downstream block can accept them.
    Does NOT reject agents in .take() — always accepts.
    Every tick, tries to push waiting agents to next block.
    """

    def __init__(self, simulator: 'Simulator'):
        super().__init__(simulator)
        self._waiting_agents: List[BaseAgent] = []

    def take(self, agent: BaseAgent) -> None:
        """
        Always accepts agent. Never rejects.
        """
        agent._enter_block(self)
        self._waiting_agents.append(agent)

    def _tick(self) -> None:
        """
        Try to push all waiting agents to next block.
        If rejected, agent stays in queue.
        """
        if not self.output_connections or not self.output_connections[0]:
            return

        target_block = self.output_connections[0]
        # Try to push agents — preserve order (FIFO)
        remaining = []
        for agent in self._waiting_agents:
            # Try to push — if target block has .take() that might reject, handle it
            # But under new strategy, target blocks SHOULD NOT reject
            # If they do, we hold agent
            try:
                target_block.take(agent)
            except Exception:
                # If target block raises or rejects, hold agent
                remaining.append(agent)
        self._waiting_agents = remaining

    @property
    def size(self) -> int:
        """Current number of agents in queue."""
        return len(self._waiting_agents)
