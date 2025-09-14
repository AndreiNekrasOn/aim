from aim import Simulator
from aim.blocks import SourceBlock, SinkBlock, GateBlock, QueueBlock, queue

def test_delay_block_smoke():
    sim = Simulator(max_ticks=10)

    source = SourceBlock(
        simulator=sim,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )

    queue = QueueBlock(sim)

    gate = GateBlock(sim)
    gate.open()

    sink = SinkBlock(simulator=sim)

    source.connect(queue)
    queue.connect(gate)
    gate.connect(sink)

    sim.run()

    assert sink.count == 1, "Gate should release agents when open"

