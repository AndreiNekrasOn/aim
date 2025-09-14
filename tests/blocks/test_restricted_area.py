from aim import Simulator
from aim.blocks import SourceBlock, SinkBlock, QueueBlock, RestrictedAreaStart, RestrictedAreaEnd


def test_restricted_area_smoke():
    sim = Simulator(max_ticks=10)

    source = SourceBlock(
        simulator=sim,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )
    queue = QueueBlock(sim)
    ras = RestrictedAreaStart(sim, 1)
    rae = RestrictedAreaEnd(sim, ras)
    ras.set_end(rae)
    sink = SinkBlock(simulator=sim)

    source.connect(queue)
    queue.connect(ras)
    ras.connect(rae)
    rae.connect(sink)

    sim.run()

    assert sink.count == 1, "RestrictedAreaStart/End should release agents"

