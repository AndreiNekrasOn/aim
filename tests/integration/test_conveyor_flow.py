# tests/integration/test_conveyor_flow.py

import pytest
from aim import Simulator, BaseAgent
from aim.blocks.source import SourceBlock
from aim.blocks.queue import QueueBlock
from aim.blocks.delay import DelayBlock
from aim.blocks.sink import SinkBlock
from aim.blocks.manufacturing.conveyor_block import ConveyorBlock
from aim.blocks.manufacturing.conveyor_exit import ConveyorExit
from aim.blocks.gate import GateBlock
from aim.spaces.manufacturing.conveyor_space import ConveyorSpace
from aim.entities.manufacturing.conveyor import Conveyor


def conveyor_setup():
    """Setup a 10m conveyor with speed 1.0 m/tick."""
    conveyor = Conveyor(points=[(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)], speed=1.0)
    space = ConveyorSpace()
    space.register_entity(conveyor)
    return conveyor, space

def test_conveyor_multiple_agents():
    """Test multiple agents can enter conveyor without collision."""
    conveyor, space = conveyor_setup()
    sim = Simulator(max_ticks=35, space=space) # PASS SPACE TO SIMULATOR

    NAME = 1
    class Box(BaseAgent):
        def __init__(self):
            nonlocal NAME
            super().__init__()
            self.length = 1.0  # 2m long
            self.name = NAME
            NAME += 1

    source = SourceBlock(
        simulator=sim,
        agent_class=Box,
        spawn_schedule=lambda tick: 2 if tick == 1 else 0  # Spawn 2 agents at tick 1
    )
    queue = QueueBlock(simulator=sim)
    queue.on_exit = lambda agent: print(f"Queue. Tick[{sim.current_tick}] Agent[{agent.name}]")
    conveyor_block = ConveyorBlock(
        simulator=sim,
        space=space,
        start_entity=conveyor,
        end_entity=conveyor  # Same for simplicity
    )
    delay = DelayBlock(simulator=sim, delay_ticks=1)
    conveyor_exit = ConveyorExit(simulator=sim, space=space)
    sink = SinkBlock(simulator=sim)

    # Wire
    source.connect(queue)
    queue.connect(conveyor_block)
    conveyor_block.connect(delay)
    delay.connect(conveyor_exit)
    conveyor_exit.connect(sink)

    sim.run()

    assert sink.count == 2, "Both agents should reach sink"
    # No crashes = no collisions

def test_conveyor_blocked_by_gate():
    """Test conveyor blocks when downstream is blocked."""
    conveyor, space = conveyor_setup()
    sim = Simulator(max_ticks=20, space=space)

    NAME = 1
    class Box(BaseAgent):
        def __init__(self):
            nonlocal NAME
            super().__init__()
            self.length = 1.0
            self.name = NAME
            NAME += 1

    source = SourceBlock(
        simulator=sim,
        agent_class=Box,
        spawn_schedule=lambda tick: 1
        )
    queue1 = QueueBlock(simulator=sim)
    conveyor_block = ConveyorBlock(
        simulator=sim,
        space=space,
        start_entity=conveyor,
        end_entity=conveyor
    )
    queue2 = QueueBlock(simulator=sim)
    gate = GateBlock(simulator=sim, initial_state="closed")  # BLOCKED
    sink = SinkBlock(simulator=sim)

    # Wire
    source.connect(queue1)
    queue1.connect(conveyor_block)
    conveyor_block.connect(queue2)
    queue2.connect(gate)
    gate.connect(sink)

    sim.run()

    # First agent enters conveyor - reaches end - stuck in queue2 (gate closed)
    # Second agent tries to enter conveyor - should be blocked (overlap) → stuck in queue1
    agents_on_conveyor = len(space._entity_agents[conveyor]) if conveyor in space._entity_agents else 0
    assert agents_on_conveyor == 10, "Only ten agents fit"
    assert sink.count == 0, "No agents should pass closed gate"

if __name__ == '__main__':
    test_conveyor_multiple_agents()

