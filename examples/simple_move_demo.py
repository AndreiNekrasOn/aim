"""
Simple Move Visualization Example with Pygame 3D Viewer

This example demonstrates multiple sequential Move blocks to show agents moving
between different locations in 3D space.
"""

import math
from aim import Simulator, BaseAgent
from aim.blocks.source import SourceBlock
from aim.blocks.sink import SinkBlock
from aim.blocks.move import MoveBlock
from aim.spaces.no_collision_space import NoCollisionSpace
from aim.visualization import Pygame3DViewer

class MovingAgent(BaseAgent):
    """Agent that moves through different locations."""
    def __init__(self):
        super().__init__()
        self.agent_id = id(self)
        self.color = (0, 255, 0)

    def on_enter_block(self, block):
        # This will be called when the agent enters a block
        pass

def main():
    # Create simulator with 3D visualization
    sim = Simulator(max_ticks=100)

    # Create a NoCollisionSpace for spatial movement
    space = NoCollisionSpace()

    # Create a Pygame 3D viewer
    viewer = Pygame3DViewer(sim, width=1000, height=700)
    sim.viewer = viewer

    # Register the space with the simulator
    sim.add_space("main_space", space)

    # Define locations for the agent to move through
    start_location = (0, 0, 0)        # Origin
    mid_location = (5, 3, 4)          # Mid point
    end_location = (-3, 1, -6)        # End point

    # Create agents that move through these locations
    class WaypointAgent(BaseAgent):
        def __init__(self):
            super().__init__()
            self.waypoints = [start_location, mid_location, end_location]
            self.current_waypoint_idx = 0
            self.start_position = self.waypoints[0]  # Need this for first move
            self.target_position = self.waypoints[1]  # First destination
            self.space_state["position"] = self.waypoints[0]  # Start at first location
            self.color = (255, 0, 0)

    # Create blocks
    source = SourceBlock(
        simulator=sim,
        agent_class=WaypointAgent,
        spawn_schedule=lambda tick: 1 if tick % 10 == 0 and tick <= 30 else 0  # 4 agents total
    )

    # First move: Origin to mid point
    move1 = MoveBlock(simulator=sim, space_name="main_space", speed=1.0)

    # Second move: Mid point to end point
    move2 = MoveBlock(simulator=sim, space_name="main_space", speed=1.0)

    # Sink for completed agents
    sink = SinkBlock(simulator=sim)

    # Connect blocks
    source.connect(move1)
    move1.connect(move2)
    move2.connect(sink)

    # Set up agent positions when entering move blocks
    def setup_first_move(agent):
        if isinstance(agent, WaypointAgent):
            if agent.current_waypoint_idx < len(agent.waypoints) - 1:
                agent.start_position = agent.waypoints[agent.current_waypoint_idx]
                agent.target_position = agent.waypoints[agent.current_waypoint_idx + 1]

    def setup_second_move(agent):
        if isinstance(agent, WaypointAgent):
            # Update the waypoint index as the agent moves to next segment
            agent.current_waypoint_idx += 1
            if agent.current_waypoint_idx < len(agent.waypoints) - 1:
                agent.start_position = agent.waypoints[agent.current_waypoint_idx]
                agent.target_position = agent.waypoints[agent.current_waypoint_idx + 1]

    move1.on_enter = setup_first_move
    move2.on_enter = setup_second_move

    sim.run()
    viewer.show_final()

if __name__ == "__main__":
    main()