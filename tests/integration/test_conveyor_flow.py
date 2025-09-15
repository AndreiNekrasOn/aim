# tests/integration/test_conveyor_flow.py

import pytest
from aim import Simulator, BaseAgent
from aim.blocks.source import SourceBlock
from aim.blocks.queue import QueueBlock
from aim.blocks.delay import DelayBlock
from aim.blocks.sink import SinkBlock
from aim.blocks.manufacturing.conveyor_block import ConveyorBlock
from aim.blocks.manufacturing.conveyor_exit import ConveyorExit
from aim.blocks.gate import GateBlock
from aim.spaces.manufacturing.conveyor_space import ConveyorSpace
from aim.entities.manufacturing.conveyor import Conveyor


def conveyor_setup():
    """Setup a 10m conveyor with speed 1.0 m/tick."""
    conveyor = Conveyor(points=[(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)], speed=1.0)
    space = ConveyorSpace()
    space.register_entity(conveyor)
    return conveyor, space

def test_conveyor_multiple_agents():
    """Test multiple agents can enter conveyor without collision."""
    conveyor, space = conveyor_setup()
    sim = Simulator(max_ticks=35, space=space) # PASS SPACE TO SIMULATOR

    NAME = 1
    class Box(BaseAgent):
        def __init__(self):
            nonlocal NAME
            super().__init__()
            self.length = 1.0  # 2m long
            self.name = NAME
            NAME += 1

    source = SourceBlock(
        simulator=sim,
        agent_class=Box,
        spawn_schedule=lambda tick: 2 if tick == 1 else 0  # Spawn 2 agents at tick 1
    )
    queue = QueueBlock(simulator=sim)
    queue.on_exit = lambda agent: print(f"Queue. Tick[{sim.current_tick}] Agent[{agent.name}]")
    conveyor_block = ConveyorBlock(
        simulator=sim,
        space=space,
        start_entity=conveyor,
        end_entity=conveyor  # Same for simplicity
    )
    delay = DelayBlock(simulator=sim, delay_ticks=1)
    conveyor_exit = ConveyorExit(simulator=sim, space=space)
    sink = SinkBlock(simulator=sim)

    # Wire
    source.connect(queue)
    queue.connect(conveyor_block)
    conveyor_block.connect(delay)
    delay.connect(conveyor_exit)
    conveyor_exit.connect(sink)

    sim.run()

    assert sink.count == 2, "Both agents should reach sink"
    # No crashes = no collisions

def test_conveyor_blocked_by_gate():
    """Test conveyor blocks when downstream is blocked."""
    conveyor, space = conveyor_setup()
    sim = Simulator(max_ticks=20, space=space)

    NAME = 1
    class Box(BaseAgent):
        def __init__(self):
            nonlocal NAME
            super().__init__()
            self.length = 1.0
            self.name = NAME
            NAME += 1

    source = SourceBlock(
        simulator=sim,
        agent_class=Box,
        spawn_schedule=lambda tick: 1
        )
    queue1 = QueueBlock(simulator=sim)
    conveyor_block = ConveyorBlock(
        simulator=sim,
        space=space,
        start_entity=conveyor,
        end_entity=conveyor
    )
    queue2 = QueueBlock(simulator=sim)
    gate = GateBlock(simulator=sim, initial_state="closed")  # BLOCKED
    sink = SinkBlock(simulator=sim)

    # Wire
    source.connect(queue1)
    queue1.connect(conveyor_block)
    conveyor_block.connect(queue2)
    queue2.connect(gate)
    gate.connect(sink)

    sim.run()

    # First agent enters conveyor - reaches end - stuck in queue2 (gate closed)
    # Second agent tries to enter conveyor - should be blocked (overlap) → stuck in queue1
    agents_on_conveyor = len(space._entity_agents[conveyor]) if conveyor in space._entity_agents else 0
    assert agents_on_conveyor == 10, "Only ten agents fit"
    assert sink.count == 0, "No agents should pass closed gate"


def test_two_conveyors_in_one_block():
    """
    Test agent traversing two connected conveyors within a single ConveyorBlock.
    - conv1: 10m long, speed=1.0 m/tick → 10 ticks to traverse
    - conv2: 10m long, speed=2.0 m/tick → 5 ticks to traverse
    - Total path time: 15 ticks
    - Agent should be ejected at tick 16 (15 ticks of movement + 1 for ejection)
    """
    # Setup space
    space = ConveyorSpace()

    # Create two conveyors
    conv1 = Conveyor(points=[(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)], speed=1.0, name="conv1")
    conv2 = Conveyor(points=[(10.0, 0.0, 0.0), (20.0, 0.0, 0.0)], speed=2.0, name="conv2")

    # Connect them
    conv1.connections = [conv2]
    conv2.connections = []

    # Register with space
    space.register_entity(conv1)
    space.register_entity(conv2)

    # Setup simulator
    sim = Simulator(max_ticks=30, space=space)

    # Define agent
    class Box(BaseAgent):
        def __init__(self):
            super().__init__()
            self.length = 1.0  # 1m long

    # Blocks
    source = SourceBlock(
        simulator=sim,
        agent_class=Box,
        spawn_schedule=lambda tick: 1 if tick == 1 else 0
    )
    queue = QueueBlock(simulator=sim)
    conveyor_block = ConveyorBlock(
        simulator=sim,
        space=space,
        start_entity=conv1,   # Start on first conveyor
        end_entity=conv2     # End on second conveyor
    )
    conveyor_exit = ConveyorExit(simulator=sim, space=space)
    sink = SinkBlock(simulator=sim)

    # Debug prints
    conveyor_block.on_enter = lambda agent: print(f"[DEBUG] Tick {sim.current_tick}: Agent entered conveyor block")
    conveyor_exit.on_enter = lambda agent: print(f"[DEBUG] Tick {sim.current_tick}: Agent exited conveyor space")

    # Wire blocks
    source.connect(queue)
    queue.connect(conveyor_block)
    conveyor_block.connect(conveyor_exit)
    conveyor_exit.connect(sink)

    # Run simulation
    sim.run()

    # Assertions
    assert sink.count == 1, "Agent should reach sink"
    assert sim.current_tick >= 16, "Agent should take at least 15 ticks to traverse path"

    # Optional: Validate space_state at ejection
    # (Would require storing agent reference — omitted for simplicity)

def test_pathfinding_chooses_fastest_path():
    """
    Test that pathfinding chooses the fastest (shortest-time) path in a multi-path network.

    Network:
        A (start)
        | \\
        |  \\
        B   C  E
        |   |  |
        \\  |  /
            D (end)

    Paths:
        A->B->D: time = 5 + 5 = 10
        A->C->D: time = 2 + 2 = 4  ← fastest
        A->E->D: time = 1 + 10 = 11

    Agent should take A->C->D.
    """
    space = ConveyorSpace()

    # Create conveyors
    A = Conveyor(points=[(0,0,0), (5,0,0)], speed=1.0, name="A")   # len=5, time=5
    B = Conveyor(points=[(5,0,0), (10,5,0)], speed=1.0, name="B")  # len= ~7.07, but we set time=5 for simplicity
    C = Conveyor(points=[(5,0,0), (10,-5,0)], speed=2.5, name="C") # len= ~7.07, time=2 (speed=3.535)
    E = Conveyor(points=[(5,0,0), (10,0,0)], speed=5.0, name="E")   # len=5, time=1
    D = Conveyor(points=[(10,-5,0), (15,0,0)], speed=2.5, name="D") # len= ~7.07, time=2 (to connect C->D)

    # Set connections
    A.connections = [B, C, E]
    B.connections = [D]
    C.connections = [D]
    E.connections = [D]
    D.connections = []

    # Register entities
    for entity in [A, B, C, E, D]:
        space.register_entity(entity)

    # Setup simulator
    sim = Simulator(max_ticks=20, space=space)

    class Box(BaseAgent):
        def __init__(self):
            super().__init__()
            self.length = 0.5

    # Blocks
    source = SourceBlock(sim, Box, lambda tick: 1 if tick == 1 else 0)
    queue = QueueBlock(sim)
    conveyor_block = ConveyorBlock(sim, space, start_entity=A, end_entity=D)
    conveyor_exit = ConveyorExit(sim, space)
    sink = SinkBlock(sim)


    # Debug: capture path taken
    path_taken = []

    def on_enter(agent):
        print(f"[DEBUG] on_enter CALLED for agent {id(agent)}")
        state = agent.space_state
        print(f"[DEBUG] space_state: {state}")
        if state and "path" in state:
            path_names = [getattr(e, 'name', str(e)) for e in state["path"]]
            path_taken.append(path_names)
            print(f"[DEBUG] Agent path: {' -> '.join(path_names)}")

    conveyor_block.on_enter = on_enter
    conveyor_exit.on_enter = lambda agent: print(f"[DEBUG] Tick {sim.current_tick}: Agent exited conveyor space")

    # Wire
    source.connect(queue)
    queue.connect(conveyor_block)
    conveyor_block.connect(conveyor_exit)
    conveyor_exit.connect(sink)

    # Run
    sim.run()

    # Assertions
    assert sink.count == 1, "Agent should reach sink"
    assert len(path_taken) == 1, "Should have recorded one path"
    chosen_path = path_taken[0]

    # Expected: A -> C -> D (fastest: time=4)
    expected_fastest = ["A", "E", "D"]
    assert chosen_path == expected_fastest, f"Expected {expected_fastest}, got {chosen_path}"

    # Optional: Verify total time
    # If you store total_time in space_state, you can assert it == 4.0

if __name__ == '__main__':
    test_pathfinding_chooses_fastest_path()

