# examples/split_combine_demo.py

from aim import BaseAgent, Simulator
from aim.blocks.source import SourceBlock
from aim.blocks.queue import QueueBlock
from aim.blocks.combine import CombineBlock
from aim.blocks.split import SplitBlock
from aim.blocks.if_block import IfBlock
from aim.blocks.sink import SinkBlock
import random

class Container(BaseAgent):
    def __init__(self):
        super().__init__()
        self.children_agents = []

class Pickup(BaseAgent):
    def __init__(self):
        super().__init__()
        self.parent_agents = []

def main():
    sim = Simulator(max_ticks=200)
    # Source1: Container every 5 ticks
    source1 = SourceBlock( simulator=sim, agent_class=Container, spawn_schedule=lambda tick: 1 if tick % 5 == 0 else 0)
    queue1 = QueueBlock(simulator=sim)
    source1.connect(queue1)
    # Source2: Pickup every 1 tick
    source2 = SourceBlock( simulator=sim, agent_class=Pickup, spawn_schedule=lambda tick: 1)
    queue2 = QueueBlock(simulator=sim)
    source2.connect(queue2)
    # CombineBlock: 1 container + 20 pickups
    combine = CombineBlock(simulator=sim, max_pickups=20)
    queue1.connect(combine.container)
    queue2.connect(combine.pickup)
    # IfBlock: 50% chance to split or go direct to sink
    if_block = IfBlock( simulator=sim, condition=lambda agent: random.random() < 0.5)
    combine.connect(if_block)
    # Sink for direct path
    direct_sink = SinkBlock(simulator=sim)
    if_block.connect_first(direct_sink)
    # SplitBlock + Sink for split path
    split_block = SplitBlock(simulator=sim)
    container_sink = SinkBlock(simulator=sim)
    products_sink = SinkBlock(simulator=sim)
    if_block.connect_second(split_block)
    split_block.connect_first(container_sink)
    split_block.connect_second(products_sink)
    # Run simulation
    sim.run()

    # Print results
    print(f"Direct sink count: {direct_sink.count}")
    print(f"Split sink count: {container_sink.count}")

if __name__ == "__main__":
    main()
