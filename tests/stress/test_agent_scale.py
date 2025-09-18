from aim.core import Simulator, BaseAgent
from aim.blocks import SourceBlock, SinkBlock

def test_agent_scale():
    sim = Simulator(max_ticks=100)
    source = SourceBlock(sim, agent_class=BaseAgent, spawn_schedule=lambda t: 10000 if t == 1 else 0)
    sink = SinkBlock(sim)
    source.connect(sink)
    sim.run()
    assert sink.count == 10000
