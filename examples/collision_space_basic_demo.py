"""
Example demonstrating CollisionSpace with obstacles and agent movement using boundary following
"""

from aim import Simulator, BaseAgent
from aim.blocks.source import SourceBlock
from aim.blocks.sink import SinkBlock
from aim.blocks.move import MoveBlock
from aim.spaces.collision_space import CollisionSpace, Prism
from aim.visualization import Pygame3DViewer

class ObstacleAgent(BaseAgent):
    """Agent that moves through space with obstacles."""
    def __init__(self):
        super().__init__()
        self.color = (0, 200, 255)  # Light blue

def main():
    # Create simulator with 3D visualization
    sim = Simulator(max_ticks=100)
    
    # Create a CollisionSpace with obstacles
    # Prism: list of base points and height
    # Simple rectangular obstacle right in the middle of the direct path
    obstacle_base = [
        (-1, -2, 0),  # Bottom rectangle
        (1, -2, 0),
        (1, 2, 0),
        (-1, 2, 0)
    ]
    obstacle_height = 3.0
    obstacle: Prism = (obstacle_base, obstacle_height)
    
    space = CollisionSpace(obstacles=[obstacle])
    
    # Create a Pygame 3D viewer
    viewer = Pygame3DViewer(sim, width=1000, height=700)
    sim.viewer = viewer
    
    # Register the space with the simulator
    sim.add_space("collision_space", space)
    
    # Create an agent that moves from one side of the obstacle to the other
    class PathfindingAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            self.color = (0, 200, 255)  # Light blue
            # Set start and target positions that require pathfinding around the obstacle
            self.start_position = (-5, 0, 1)
            self.target_position = (5, 0, 1)
            self.speed = 0.5
    
    # Create blocks
    source = SourceBlock(
        simulator=sim, 
        agent_class=PathfindingAgent, 
        spawn_schedule=lambda tick: 1 if tick == 0 else 0  # One agent at tick 0
    )
    
    move_block = MoveBlock(simulator=sim, space_name="collision_space", speed=0.5)
    
    sink = SinkBlock(simulator=sim)
    
    # Connect blocks
    source.connect(move_block)
    move_block.connect(sink)
    
    # Run simulation
    print("Starting obstacle navigation simulation with boundary following...")
    print("Controls: Left-click + drag to rotate, mouse wheel to zoom, ESC to quit")
    print("Blue dots = agents, Gray shapes = obstacles, Red/Green/Blue lines = axes")
    sim.run()
    
    print(f"Simulation completed!")
    print(f"Agents completed: {sink.count}")
    
    # Keep the window open for post-simulation navigation
    viewer.show_final()

if __name__ == "__main__":
    main()