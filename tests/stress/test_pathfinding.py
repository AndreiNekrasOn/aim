from aim.core import Simulator
from aim.blocks import SourceBlock, SinkBlock, QueueBlock
from aim.blocks.manufacturing.conveyor_block import ConveyorBlock
from aim.spaces.manufacturing.conveyor_space import ConveyorSpace
from aim.entities.manufacturing.conveyor import Conveyor

def test_pathfinding_stress():
    space = ConveyorSpace()
    sim = Simulator(max_ticks=10_000, spaces={"main": space})

    # Create 500 conveyors in a grid
    conveyors = []
    for i in range(50):
        for j in range(10):
            c = Conveyor(points=[(i*10, j*10, 0), (i*10+5, j*10, 0)], speed=1.0)
            conveyors.append(c)
            space.register_entity(c)

    # Connect each to next
    for i in range(len(conveyors)-1):
        conveyors[i].connections.append(conveyors[i+1])

    source = SourceBlock(sim, spawn_schedule=lambda t: 100 if t == 1 else 0)
    queue = QueueBlock(sim)
    conv_block = ConveyorBlock(sim, space_name="main", start_entity=conveyors[0], end_entity=conveyors[-1])
    sink = SinkBlock(sim)

    source.connect(queue)
    queue.connect(conv_block)
    conv_block.connect(sink)

    sim.run()
    assert sink.count == 100
