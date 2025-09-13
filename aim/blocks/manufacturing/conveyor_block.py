# blocks/manufacturing/conveyor_block.py (FINAL)

from typing import Optional, List
from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.entities.manufacturing.conveyor import Conveyor

class ConveyorBlock(BaseBlock):
    """
    A block that interfaces with a Conveyor (spatial entity).
    Agents are placed on the conveyor; movement is managed by ConveyorNetwork.
    Implements backpressure: .take(agent) returns False if conveyor cannot accept.
    Ejects agents to next block when they reach end of conveyor.
    """

    def __init__(self, conveyor: Conveyor):
        super().__init__()
        self.conveyor = conveyor
        self.conveyor.block = self  # ← bind for ejection callback
        self._rejected_agents: List[BaseAgent] = []

    def take(self, agent: BaseAgent) -> bool:
        if self.conveyor.try_place_agent(agent):
            agent._enter_block(self)
            return True
        else:
            self._rejected_agents.append(agent)
            return False

    def _tick(self) -> None:
        if self.conveyor.network is None:
            return

        # Advance network
        self.conveyor.network.update(delta_time=1.0)

        # Retry rejected agents
        still_rejected = []
        for agent in self._rejected_agents:
            if not self.take(agent):
                still_rejected.append(agent)
        self._rejected_agents = still_rejected

        # Ejection is handled via Conveyor._on_agents_ejected → calls self._eject_agent

    def _eject_agent(self, agent: BaseAgent) -> None:
        """Push agent to next block."""
        if self.output_connections and self.output_connections[0]:
            self.output_connections[0].take(agent)
