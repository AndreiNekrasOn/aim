import pytest
from aim.core.simulator import Simulator
from aim.blocks import *
from aim.core.agent import BaseAgent
from aim.blocks.switch import SwitchBlock
from aim.blocks.sink import SinkBlock

def test_switch_block_smoke_str_keys():
    """
    Smoke test: route agents by string key.
    """
    sim = Simulator(max_ticks=10)

    class PriorityAgent(BaseAgent):
        def __init__(self, priority: str):
            super().__init__()
            self.priority = priority

    # Create blocks
    agent_A = PriorityAgent("high")
    agent_B = PriorityAgent("low")
    switch = SwitchBlock(sim, key_func=lambda agent: agent.priority)
    sink_high = SinkBlock(sim)
    sink_low = SinkBlock(sim)

    # Connect by key
    switch.connect("high", sink_high)
    switch.connect("low", sink_low)

    # Create and spawn agents
    switch.take(agent_A)
    switch.take(agent_B)

    assert sink_high.count == 1
    assert sink_low.count == 1
