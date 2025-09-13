# blocks/manufacturing/conveyor_block.py (FINAL)

from typing import Optional, List
from aim.core.block import BaseBlock
from aim.core.simulator import Simulator
from aim.core.agent import BaseAgent
from aim.entities.manufacturing.conveyor import Conveyor

class ConveyorBlock(BaseBlock):
    """
    A block that interfaces with a Conveyor (spatial entity).
    Agents are placed on the conveyor; movement is managed by ConveyorNetwork.
    Implements backpressure: .take(agent) returns False if conveyor cannot accept.
    Ejects agents to next block when they reach end of conveyor.
    """

    def __init__(self,
             simulator: Simulator,
             conveyor: Conveyor):
        super().__init__(simulator)
        self.conveyor = conveyor
        self.conveyor.block = self  # ← bind for ejection callback
        self._rejected_agents: List[BaseAgent] = []

    def take(self, agent: BaseAgent) -> None:
        """
        Try to place agent on conveyor. If rejected, RAISE or let system handle via QueueBlock.
        Under new strategy: this should not happen — user must place QueueBlock upstream.
        """
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)
        if not self.conveyor.try_place_agent(agent):
            raise RuntimeError(f"ConveyorBlock {self} rejected agent {agent} — use QueueBlock upstream.")

    def _tick(self) -> None:
        if self.conveyor.network is None:
            return
        self.conveyor.network.update(delta_time=1.0)
        # Ejection handled via Conveyor._on_agents_ejected → _eject_agent

    def _eject_agent(self, agent: BaseAgent) -> None:
        self._eject(agent)
