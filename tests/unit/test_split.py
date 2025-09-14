# test_split.py

from aim import BaseAgent, Simulator
from aim.blocks import SourceBlock, SinkBlock, SplitBlock

class Container(BaseAgent):
    def __init__(self):
        super().__init__()
        self.children_agents = []

class Pickup(BaseAgent):
    def __init__(self):
        super().__init__()
        self.parent_agents = []

def test_split_block_smoke():
    sim = Simulator(max_ticks=10)

    # Create container with one pickup
    def spawn_container_with_pickup():
        container = Container()
        pickup = Pickup()
        container.children_agents.append(pickup)
        pickup.parent_agents.append(container)
        return container

    source = SourceBlock(
        simulator=sim,
        agent_class=spawn_container_with_pickup,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )

    # SplitBlock
    split = SplitBlock(simulator=sim)

    # Sinks
    sink_container = SinkBlock(simulator=sim)
    sink_pickup = SinkBlock(simulator=sim)

    # Wiring
    source.connect(split)
    split.connect_first(sink_container)  # container goes here
    split.connect_second(sink_pickup)    # pickup goes here

    # Run
    sim.run()

    # Verify
    assert sink_container.count == 1, "SplitBlock should emit one container"
    assert sink_pickup.count == 1, "SplitBlock should emit one pickup"
    assert len(sink_container._agents[0].children_agents) == 0, "Container should have no children after split"
