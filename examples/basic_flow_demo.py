# examples/basic_flow.py

from aim import BaseAgent, SourceBlock, SinkBlock, Simulator
from aim.blocks.manufacturing import ConveyorBlock
from aim.blocks.queue import QueueBlock
from aim.spaces.manufacturing import ConveyorNetwork
from aim.entities.manufacturing import Conveyor

class TestAgent(BaseAgent):
    def on_enter_block(self, block):
        print(f"Agent entered {block.__class__.__name__}")

def init_conveyor(sim: Simulator, cn: ConveyorNetwork, points, speed, name):
    conv = Conveyor(points, speed, name)
    cn.add_conveyor(conv)
    convey = ConveyorBlock(sim, conv)
    conv.block = convey
    return convey

sim = Simulator(max_ticks=20)

# Setup
source = SourceBlock(
    sim,
    agent_class=TestAgent,
    spawn_schedule=lambda tick: 1 if tick % 20 == 0 else 0
)

cn = ConveyorNetwork()

queue_main = QueueBlock(sim)
conveyor_main = init_conveyor(sim, cn, [(0,0,0),(1,0,0)], 0.1, "main_line")
queue_pivot  = QueueBlock(sim)
conveyor_pivot = init_conveyor(sim, cn, [(1,0,0),(1,0,0)], 0.2, "pivot")

sink = SinkBlock(sim)

source.connect(queue_main)
queue_main.connect(conveyor_main)
conveyor_main.connect(queue_pivot)
queue_pivot.connect(conveyor_pivot)
conveyor_pivot.connect(sink)

sim.run()

print(f"Total agents in sink: {sink.count}")
