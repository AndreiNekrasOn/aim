import pytest
from typing import Optional

from aim.core.simulator import Simulator
from aim.core.agent import BaseAgent
from aim.blocks import *
from aim.blocks.sink import SinkBlock
from aim.spaces.manufacturing.conveyor_space import ConveyorSpace
from aim.entities.manufacturing.conveyor import Conveyor
from aim.blocks.manufacturing.conveyor_block import ConveyorBlock

def test_switch_block_integration_conveyor_keys():
    """
    Integration test: route agents by Conveyor key.
    """
    space = ConveyorSpace()
    sim = Simulator(max_ticks=20, spaces={"main": space})

    # Create conveyors
    conv_A = Conveyor([(0, 0, 0), (10, 0, 0)], speed=1.0)
    conv_B = Conveyor([(0, 0, 0), (0, 10, 0)], speed=1.0)
    conv_A.name = "conv_A"
    conv_B.name = "conv_B"
    space.register_entity(conv_A)
    space.register_entity(conv_B)

    class DestinationAgent(BaseAgent):
        def __init__(self, dest_conveyor: Optional[Conveyor] = None):
            super().__init__()
            self.destination = dest_conveyor

    # Create blocks
    queue = QueueBlock(sim)  # ← Use QueueBlock to feed pre-configured agents
    switch = SwitchBlock(sim, key_func=lambda agent: agent.destination)
    block_A = ConveyorBlock(sim, space_name="main", start_entity=conv_A, end_entity=conv_A)
    block_B = ConveyorBlock(sim, space_name="main", start_entity=conv_B, end_entity=conv_B)
    sink_A = SinkBlock(sim)
    sink_B = SinkBlock(sim)

    # Connect switch by key (Conveyor objects)
    switch.connect(conv_A, block_A)
    switch.connect(conv_B, block_B)

    # Wire the system
    queue.connect(switch)
    block_A.connect(sink_A)
    block_B.connect(sink_B)

    # Create and configure agents
    agent_A = DestinationAgent()
    agent_A.destination = conv_A

    agent_B = DestinationAgent()
    agent_B.destination = conv_B

    # Feed agents into queue
    queue.take(agent_A)
    queue.take(agent_B)

    # Run simulation
    sim.run()

    # Verify routing
    assert sink_A.count == 1, "Agent A should reach sink_A"
    assert sink_B.count == 1, "Agent B should reach sink_B"
