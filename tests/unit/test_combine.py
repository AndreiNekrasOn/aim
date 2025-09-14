# test_combine.py

from aim import BaseAgent, Simulator
from aim.blocks import SourceBlock, QueueBlock, SinkBlock, CombineBlock

class Container(BaseAgent):
    def __init__(self):
        super().__init__()
        self.children_agents = []

class Pickup(BaseAgent):
    def __init__(self):
        super().__init__()
        self.parent_agents = []

def test_combine_block_smoke():
    sim = Simulator(max_ticks=10)

    # Sources
    source_container = SourceBlock(
        simulator=sim,
        agent_class=Container,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )
    source_pickup = SourceBlock(
        simulator=sim,
        agent_class=Pickup,
        spawn_schedule=lambda tick: 1 if tick == 2 else 0
    )

    # Queues
    queue_container = QueueBlock(simulator=sim)
    queue_pickup = QueueBlock(simulator=sim)

    # CombineBlock (1 container + 1 pickup)
    combine = CombineBlock(simulator=sim, max_pickups=1)

    # Sink
    sink = SinkBlock(simulator=sim)

    # Wiring
    source_container.connect(queue_container)
    source_pickup.connect(queue_pickup)
    queue_container.connect(combine.container)
    queue_pickup.connect(combine.pickup)
    combine.connect(sink)

    # Run
    sim.run()

    # Verify
    assert sink.count == 1, "CombineBlock should emit one combined agent"

