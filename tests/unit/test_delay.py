from aim import Simulator
from aim.blocks import SourceBlock, SinkBlock, DelayBlock

def test_delay_block_smoke():
    sim = Simulator(max_ticks=10)

    source = SourceBlock(
        simulator=sim,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )

    delay = DelayBlock(sim, 1)

    sink = SinkBlock(simulator=sim)

    source.connect(delay)
    delay.connect(sink)

    sim.run()

    assert sink.count == 1, "Delay should release agents after timeout"

