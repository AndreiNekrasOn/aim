from aim.core.simulator import Simulator
from aim.core.agent import BaseAgent
from aim.spaces.no_collision_space import NoCollisionSpace
from aim.blocks.source import SourceBlock
from aim.blocks.sink import SinkBlock
from aim.blocks.move import MoveBlock

def test_no_collision_space_basic():
    """
    Test agent moving from (0,0,0) to (10,10,0) in NoCollisionSpace.
    Speed = 2.0 units/tick → should take 7.07 ticks (distance=14.14).
    """
    space = NoCollisionSpace()
    sim = Simulator(max_ticks=20, spaces={"free_space": space})

    class MovingAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            self.start_position = (0.0, 0.0, 0.0)
            self.target_position = (10.0, 10.0, 0.0)
            self.speed = 2.0

    source = SourceBlock(sim, agent_class=MovingAgent, spawn_schedule=lambda tick: 1 if tick == 1 else 0)
    move_block = MoveBlock(sim, space_name="free_space", speed=1.0)
    sink = SinkBlock(sim)

    source.connect(move_block)
    move_block.connect(sink)

    sim.run()

    assert sink.count == 1, "Agent should reach sink"
    # Should take ceil(14.14 / 2.0) = 8 ticks to move + 1 for ejection = tick 9
    assert sim.current_tick >= 9, "Agent should take about 8-9 ticks to reach target"
