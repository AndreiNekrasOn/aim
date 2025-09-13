# examples/conveyor_demo.py

from aim import BaseAgent, Simulator
from aim.blocks.queue import QueueBlock
from aim.blocks.source import SourceBlock
from aim.blocks.sink import SinkBlock
from aim.blocks.manufacturing.conveyor_block import ConveyorBlock
from aim.entities.manufacturing.conveyor import Conveyor
from aim.spaces.manufacturing.conveyor_network import ConveyorNetwork

class DemoAgent(BaseAgent):
    """Simple agent for demo — logs entry/exit."""
    def __init__(self):
        super().__init__()
        self.agent_id = id(self)  # simple unique ID

    def on_enter_block(self, block):
        # print(f"Agent {self.agent_id} entered {block.__class__.__name__}")
        pass

    def on_event(self, event):
        pass  # not used


def main():
    # --- SETUP ---
    sim = Simulator(max_ticks=100)

    # Create conveyor network
    cn = ConveyorNetwork()

    # Define 3D conveyor path: straight line in X, rising in Z
    points = [
        (0.0, 0.0, 0.0),
        (5.0, 0.0, 1.0),
        (10.0, 0.0, 2.0),
    ]

    # Create conveyor (speed = 0.2 → 20% of path per tick → 5 ticks to traverse)
    conveyor = Conveyor(points=points, speed=0.2, name="MainLine")

    # Add conveyor to network
    cn.add_conveyor(conveyor)

    # Create blocks
    source = SourceBlock(sim, agent_class=DemoAgent)
    queue = QueueBlock(sim)
    conveyor_block = ConveyorBlock(sim, conveyor=conveyor)
    sink = SinkBlock(sim)

    # Wire pipeline
    source.connect(queue)
    queue.connect(conveyor_block)
    conveyor_block.connect(sink)  # eject to sink

    # --- RUN ---
    print("Starting simulation...\n")
    sim.run()

    # --- RESULTS ---
    print(f"\nSimulation finished after {sim.current_tick} ticks.")
    print(f"Agents in sink: {sink.count}")

    # Optional: show final positions of any agents still on conveyor (should be 0)
    agents_on_conveyor = cn.find_entities(None)
    if agents_on_conveyor:
        print(f"WARNING: {len(agents_on_conveyor)} agents still on conveyor:")
        for agent in agents_on_conveyor:
            progress = cn.get_progress(agent)
            pos = conveyor.get_position_at_progress(progress or 0.0)
            print(f"  Agent {agent.agent_id} at progress {progress:.2f}, position {pos}")
    else:
        print("All agents successfully exited conveyor.")


if __name__ == "__main__":
    main()
