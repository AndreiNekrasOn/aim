"""
Move Resource Block for resource Pool with visualization

This example demonstrates a simplified system where agents acquire resources,
and move them via MoveResource block with basic visualization.
"""

import math
from aim import Simulator, BaseAgent, ResourcePool, ResourceAgent, SeizeBlock, ReleaseBlock, QueueBlock, SinkBlock
from aim.blocks import move_resoure
from aim.blocks.source import SourceBlock
from aim.blocks.delay import DelayBlock
from aim.core import simulator
from aim.visualization import Pygame3DViewer
from aim.spaces.no_collision_space import NoCollisionSpace

class ProcessAgent(BaseAgent):
    """Agent that represents a process requiring resources."""
    def __init__(self):
        super().__init__()
        self.agent_id = id(self)

def main():
    # Create simulator with 3D visualization
    sim = Simulator(max_ticks=110)


    # Create a Pygame 3D viewer
    viewer = Pygame3DViewer(sim, width = 1000, height=500)
    sim.viewer = viewer

    space = NoCollisionSpace()
    sim.add_space("resources", space)

    # Create a ResourcePool with 2 worker resources
    worker_pool = ResourcePool(
        name="processing_workers",
        simulator=sim,
        resource_type="worker",
        initial_resources=[
            ResourceAgent(resource_id="worker_1", resource_type="worker", properties={"start_position": (0,0,0), "target_position": (100, 0, 0), "speed": 1}),
        ]
    )

    source = SourceBlock(
        simulator=sim,
        agent_class=ProcessAgent,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )
    queue = QueueBlock(simulator=sim)
    acquire_resource = SeizeBlock(simulator=sim, resource_pool=worker_pool, resource_count=1)
    queue2 = QueueBlock(simulator=sim)
    send_resource = move_resoure.MoveResourcelock(simulator=sim, space_name="resources", speed=1)
    release_resource = ReleaseBlock(simulator=sim, resource_pool=worker_pool)
    completed = SinkBlock(simulator=sim)

    # Connect the blocks
    source.connect(queue)
    queue.connect(acquire_resource)
    acquire_resource.connect(queue2)
    queue2.connect(send_resource)
    send_resource.connect(release_resource)
    release_resource.connect(completed)


    def acquire_resource_on_enter(agent: BaseAgent):
        agent.resource_agent = agent._acquired_resources[0]
        print(agent.resource_agent)

    # setup hooks
    acquire_resource.on_enter = acquire_resource_on_enter
    queue2.on_enter = lambda _: print("entered quee")
    send_resource.on_enter = lambda _: print("entered send_resource")
    send_resource.on_exit = lambda _: print("exited send_resource")

    sim.run()

    viewer.show_final()

if __name__ == "__main__":
    main()

