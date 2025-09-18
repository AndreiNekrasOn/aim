from aim.core import Simulator
from aim.blocks import SourceBlock, SinkBlock, QueueBlock

def test_block_complexity():
    sim = Simulator(max_ticks=1000)
    prev = SourceBlock(sim, spawn_schedule=lambda t: 1 if t == 1 else 0)
    for _ in range(1000):
        block = QueueBlock(sim)
        prev.connect(block)
        prev = block
    sink = SinkBlock(sim)
    prev.connect(sink)
    sim.run()
    assert sink.count == 1
