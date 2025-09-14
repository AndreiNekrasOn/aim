from aim import Simulator
from aim.blocks import SourceBlock, SinkBlock, QueueBlock

def test_queue_block_smoke():
    sim = Simulator(max_ticks=10)

    source = SourceBlock(
        simulator=sim,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )

    queue = QueueBlock(sim)

    sink = SinkBlock(simulator=sim)

    source.connect(queue)
    queue.connect(sink)

    sim.run()

    assert sink.count == 1, "Queue should release agents"


