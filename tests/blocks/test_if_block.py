from aim import Simulator
from aim.blocks import SourceBlock, SinkBlock, IfBlock

def _check_branch(branch: bool) -> int:
    sim = Simulator(max_ticks=10)

    source = SourceBlock(
        simulator=sim,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )

    ifblock = IfBlock(sim, condition=lambda _ : branch)

    sink_first = SinkBlock(simulator=sim)
    sink_second = SinkBlock(simulator=sim)

    source.connect(ifblock)
    ifblock.connect_first(sink_first)
    ifblock.connect_second(sink_second)

    sim.run()

    if branch:
        return sink_first.count
    else:
        return sink_second.count


def test_if_block_smoke():
    true_branch = _check_branch(True)
    false_branch = _check_branch(False)

    assert true_branch == 1 and false_branch == 1, "Both If branches should release an agent"

