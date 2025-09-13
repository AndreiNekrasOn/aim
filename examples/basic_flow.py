# examples/basic_flow.py

from aim import BaseAgent, SourceBlock, SinkBlock, Simulator

class TestAgent(BaseAgent):
    def on_enter_block(self, block):
        print(f"Agent entered {block.__class__.__name__}")

# Setup
source = SourceBlock(agent_class=TestAgent, spawn_rate=2)
sink = SinkBlock()
source.connect(sink)

sim = Simulator(max_ticks=3)
sim.add_block(source)
sim.add_block(sink)

sim.run()

print(f"Total agents in sink: {sink.count}")
