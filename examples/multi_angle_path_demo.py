"""
Example demonstrating an agent following a multi-angle path with obstacle avoidance
"""

from aim import Simulator, BaseAgent
from aim.blocks.source import SourceBlock
from aim.blocks.sink import SinkBlock
from aim.blocks.move import MoveBlock
from aim.spaces.collision_space import CollisionSpace, Prism
from aim.visualization import Pygame3DViewer

def main():
    # Create simulator with 3D visualization
    sim = Simulator(max_ticks=200)

    # Create a CollisionSpace with multiple obstacles
    obstacles = []

    # Add multiple obstacles to create a more complex path
    # Obstacle 1: A vertical barrier
    obstacle1_base = [
        (0, -3, 0),
        (1, -3, 0),
        (1, 1, 0),
        (0, 1, 0)
    ]
    obstacle1: Prism = (obstacle1_base, 2.0)
    obstacles.append(obstacle1)

    # Obstacle 2: A horizontal barrier
    obstacle2_base = [
        (2, 2, 0),
        (5, 2, 0),
        (5, 3, 0),
        (2, 3, 0)
    ]
    obstacle2: Prism = (obstacle2_base, 2.0)
    obstacles.append(obstacle2)

    space = CollisionSpace(obstacles=obstacles)

    # Create a Pygame 3D viewer
    viewer = Pygame3DViewer(sim, width=1800, height=1200)
    sim.viewer = viewer

    # Register the space with the simulator
    sim.add_space("collision_space", space)

    class TraceAgent(BaseAgent):
        def __init__(self, position):
            super().__init__()
            self.color = (0, 200, 0)
            self.start_position = position
            self.target_position = position
            self.speed = 0.1

    # Create an agent that follows a multi-angle path with specified waypoints
    class MultiAngleAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            self.color = (255, 100, 100)  # Reddish
            # Define start, target and a path with multiple angles
            self.start_position = (-4, -4, 1)
            self.target_position = (6, 4, 1)
            self.speed = 0.7

        def on_enter_block(self, block: BaseBlock) -> None:
            tracked_agents.append(self)


        def spawn_track(self, space):
            trace: TraceAgent = TraceAgent(self.space_state['position'])
            space.register(trace, { 'start_position': trace.start_position, 'target_position': trace.target_position, 'speed': trace.speed })
            sim.add_agent(trace)




    tracked_agents = []

    # Create blocks
    source = SourceBlock(
        simulator=sim,
        agent_class=MultiAngleAgent,
        spawn_schedule=lambda tick: 1 if tick == 0 else 0  # One agent at tick 0
    )

    def callback_event():
        for agent in tracked_agents:
            if not space.is_movement_complete(agent):
                agent.spawn_track(space)

    sim.schedule_event(callback=lambda _: callback_event(),
            delay_ticks=0,
            recurring=True
    )


    move_block = MoveBlock(simulator=sim, space_name="collision_space", speed=0.7)

    sink = SinkBlock(simulator=sim)

    # Connect blocks
    source.connect(move_block)
    # move_block.connect(sink)

    # Run simulation
    print("Starting multi-angle path following with pre-defined path...")
    print("Controls: Left-click + drag to rotate, mouse wheel to zoom, ESC to quit")
    print("Red dots = agents, Gray shapes = obstacles, Red/Green/Blue lines = axes")
    sim.run()

    print(f"Simulation completed!")
    print(f"Agents completed: {sink.count}")

    # Keep the window open for post-simulation navigation
    viewer.show_final()

if __name__ == "__main__":
    main()