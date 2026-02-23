"""
Integration tests for CollisionSpace functionality
"""

from aim import Simulator, BaseAgent
from aim.blocks.source import SourceBlock
from aim.blocks.sink import SinkBlock
from aim.blocks.move import MoveBlock
from aim.spaces.collision_space import CollisionSpace, Prism
import pytest

def test_collision_space_agent_avoids_obstacle_by_default():
    """
    Test that agents automatically avoid obstacles when using CollisionSpace.
    The agent should find a path around the obstacle instead of going through it.
    """
    sim = Simulator(max_ticks=100)
    
    # Create an obstacle right in the middle of the path
    obstacle_base = [
        (-1, -1, 0), 
        (1, -1, 0),
        (1, 1, 0),
        (-1, 1, 0)
    ]
    obstacle_height = 2.0
    obstacle: Prism = (obstacle_base, obstacle_height)
    
    space = CollisionSpace(obstacles=[obstacle])
    sim.add_space("collision_space", space)
    
    class TestAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            self.start_position = (-3, 0, 1)  # Start on left side
            self.target_position = (3, 0, 1)   # Target on right side
            self.speed = 0.2
    
    source = SourceBlock(sim, agent_class=TestAgent, spawn_schedule=lambda tick: 1 if tick == 0 else 0)
    move_block = MoveBlock(sim, space_name="collision_space", speed=0.2)
    sink = SinkBlock(sim)
    
    source.connect(move_block)
    move_block.connect(sink)
    
    # Run simulation
    sim.run()
    
    # The agent should reach the sink
    assert sink.count == 1, f"Expected 1 agent to reach sink, got {sink.count}"
    
    # Check that agent completed successfully
    for agent in sim.agents:
        if hasattr(agent, 'space_state'):
            assert agent.space_state.get("progress", 0) >= 1.0


def test_collision_space_agent_follows_predefined_path():
    """
    Test that agents follow a predefined path when one is specified.
    """
    sim = Simulator(max_ticks=100)
    
    # Create an obstacle
    obstacle_base = [
        (0, -1, 0), 
        (2, -1, 0),
        (2, 1, 0),
        (0, 1, 0)
    ]
    obstacle_height = 2.0
    obstacle: Prism = (obstacle_base, obstacle_height)
    
    space = CollisionSpace(obstacles=[obstacle])
    sim.add_space("collision_space", space)
    
    class PathAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            # Define start, target, and a specific path that goes around the obstacle
            self.start_position = (-2, 0, 1)  # Start position
            self.target_position = (4, 0, 1)   # Target position 
            # Predefined path that goes around the obstacle
            self.path = [
                (-2, 0, 1),  # Start
                (-1, 2, 1),  # Go above obstacle
                (3, 2, 1),   # Move right above obstacle
                (4, 0, 1)    # Go down to target
            ]
            self.speed = 0.2
    
    source = SourceBlock(sim, agent_class=PathAgent, spawn_schedule=lambda tick: 1 if tick == 0 else 0)
    move_block = MoveBlock(sim, space_name="collision_space", speed=0.2)
    sink = SinkBlock(sim)
    
    source.connect(move_block)
    move_block.connect(sink)
    
    # Run simulation
    sim.run()
    
    # The agent should reach the sink using the predefined path
    assert sink.count == 1, f"Expected 1 agent to reach sink, got {sink.count}"


def test_collision_space_agent_collision_with_invalid_path():
    """
    Test that CollisionSpace throws an error when strict collision checking is enabled
    and an agent tries to follow a path through an obstacle.
    """
    # Create an obstacle
    obstacle_base = [
        (-0.5, -1, 0), 
        (0.5, -1, 0),
        (0.5, 1, 0),
        (-0.5, 1, 0)
    ]
    obstacle_height = 2.0
    obstacle: Prism = (obstacle_base, obstacle_height)
    
    # Use strict collision checking mode
    space = CollisionSpace(obstacles=[obstacle], strict_collision_checking=True)
    
    # Create an agent and register it directly with a path through the obstacle
    agent = BaseAgent()
    
    # Initial state with a path that goes through the obstacle
    # Note: the first item in path is the next waypoint, not the starting position
    initial_state = {
        "start_position": (-2, 0, 1),  # Start on left
        "target_position": (2, 0, 1),  # Target on right
        "speed": 0.2,
        "path": [              # Path that goes through the obstacle (starting from next position)
            (0, 0, 1),        # Go through the obstacle (should trigger error with strict checking)
            (2, 0, 1)         # End
        ]
    }
    
    # Register the agent - this should work fine
    assert space.register(agent, initial_state) == True
    
    # Now try to update the space - this should trigger the collision error when moving from (-2,0,1) to (0,0,1)
    with pytest.raises(RuntimeError, match="intersects obstacle"):
        space.update(1.0)  # Update with 1.0 time delta


if __name__ == "__main__":
    test_collision_space_agent_avoids_obstacle_by_default()
    test_collision_space_agent_follows_predefined_path()
    test_collision_space_agent_collision_with_invalid_path()
    print("All collision space tests passed!")