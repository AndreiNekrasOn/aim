# examples/basic_flow.py

from aim import BaseAgent, SourceBlock, SinkBlock, Simulator
from aim.blocks.manufacturing import ConveyorBlock
from aim.spaces.manufacturing import ConveyorNetwork
from aim.entities.manufacturing import Conveyor

class TestAgent(BaseAgent):
    def on_enter_block(self, block):
        print(f"Agent entered {block.__class__.__name__}")

def init_conveyor(cn: ConveyorNetwork, points, speed, name):
    conv = Conveyor(points, speed, name)
    cn.add_conveyor(conv)
    convey = ConveyorBlock(conv)
    conv.block = convey
    return convey


# Setup
source = SourceBlock(
    agent_class=TestAgent,
    spawn_schedule=lambda tick: 1 if tick % 20 == 0 else 0
)
sink = SinkBlock()
# source.connect(sink)

cn = ConveyorNetwork()

conveyor_main = init_conveyor(cn, [(0,0,0),(1,0,0)], 0.1, "main_line")
conveyor_pivot = init_conveyor(cn, [(1,0,0),(1,0,0)], 0.2, "pivot")

source.connect(conveyor_main)
conveyor_main.connect(conveyor_pivot)
conveyor_pivot.connect(sink)

sim = Simulator(max_ticks=20)
sim.add_block(source)
sim.add_block(conveyor_main)
sim.add_block(conveyor_pivot)
sim.add_block(sink)
sim.run()

print(f"Total agents in sink: {sink.count}")
