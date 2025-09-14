from aim import Simulator
from aim.blocks.source import SourceBlock
from aim.blocks.sink import SinkBlock

def test_source_block_smoke():
    sim = Simulator(max_ticks=10)

    source = SourceBlock(
        simulator=sim,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )

    sink = SinkBlock(simulator=sim)
    source.connect(sink)

    sim.run()

    assert sink.count == 1, "Source should spawn one agent"
