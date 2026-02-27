"""
Resource Pool with Movement Visualization Example

This example demonstrates a simplified system where agents acquire resources,
wait for a period of time, and then release resources, with basic visualization.
"""

import math
from aim import Simulator, BaseAgent, ResourcePool, ResourceAgent, SeizeBlock, ReleaseBlock, QueueBlock, SinkBlock
from aim.blocks.source import SourceBlock
from aim.blocks.delay import DelayBlock
from aim.visualization import Pygame3DViewer

class ProcessAgent(BaseAgent):
    """Agent that represents a process requiring resources."""
    def __init__(self):
        super().__init__()
        self.agent_id = id(self)

    def on_enter_block(self, block):
        # Set position based on which block the agent is in
        print('on_enter_block executed')
        block_name = block.__class__.__name__

        if "Source" in block_name:
            self.space_state["position"] = (-8, 0, 0)  # Source area (left)
        elif "Queue" in block_name:
            self.space_state["position"] = (-4, 0, 0)  # Queue area
        elif "Seize" in block_name:
            self.space_state["position"] = (0, 0, 0)   # Resource acquisition area (center)
        elif "Delay" in block_name:
            # During processing time, move to processing area
            self.space_state["position"] = (4, 0, 0)   # Processing area
        elif "Release" in block_name:
            self.space_state["position"] = (8, 0, 0)   # Release area (right)
        elif "Sink" in block_name:
            self.space_state["position"] = (0, -8, 0)  # Completed area (bottom)

def main():
    # Create simulator with 3D visualization
    sim = Simulator(max_ticks=80)

    # Create a Pygame 3D viewer
    viewer = Pygame3DViewer(sim)
    sim.viewer = viewer

    # Create a ResourcePool with 2 worker resources
    worker_pool = ResourcePool(
        name="processing_workers",
        simulator=sim,
        resource_type="worker",
        initial_resources=[
            ResourceAgent(resource_id="worker_1", resource_type="worker"),
            ResourceAgent(resource_id="worker_2", resource_type="worker")
        ]
    )

    # Set initial positions for worker resources
    for i, resource in enumerate(worker_pool.available_resources):
        angle = 2 * math.pi * i / len(worker_pool.available_resources)
        x = 2 * math.cos(angle)
        z = 2 * math.sin(angle)
        # Place workers slightly above the process line for visibility
        resource.space_state["position"] = (x, 2, z)

    # Create blocks following the process flow:
    # Source -> Queue -> Seize -> Delay -> Release -> Sink

    source = SourceBlock(
        simulator=sim,
        agent_class=ProcessAgent,
        spawn_schedule=lambda tick: 1 if tick % 2 == 0 and tick <= 20 else 0  # 11 agents total
    )

    queue = QueueBlock(simulator=sim)
    acquire_resource = SeizeBlock(simulator=sim, resource_pool=worker_pool, resource_count=1)
    processing_delay = DelayBlock(simulator=sim, delay_ticks=5)
    release_resource = ReleaseBlock(simulator=sim, resource_pool=worker_pool)
    completed = SinkBlock(simulator=sim)

    # Connect the blocks
    source.connect(queue)
    queue.connect(acquire_resource)
    acquire_resource.connect(processing_delay)
    processing_delay.connect(release_resource)
    release_resource.connect(completed)

    sim.run()

    viewer.show_final()

if __name__ == "__main__":
    main()