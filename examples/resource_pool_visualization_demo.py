"""
Warehouse Fulfillment Center Visualization Example with Pygame 3D Viewer

This example demonstrates a warehouse fulfillment center where orders must acquire
workers, move to shelves to pick items, move to packing stations, and then release workers.
"""

import math
from aim import Simulator, BaseAgent, ResourcePool, ResourceAgent, SeizeBlock, ReleaseBlock, QueueBlock, SinkBlock
from aim.blocks.source import SourceBlock
from aim.blocks.delay import DelayBlock
from aim.blocks.move import MoveBlock
from aim.spaces.no_collision_space import NoCollisionSpace
from aim.visualization import Pygame3DViewer

class OrderAgent(BaseAgent):
    """Agent representing an order that needs to be fulfilled."""
    def __init__(self):
        super().__init__()
        self.order_id = id(self)
        # Define the path through the warehouse
        self.dispatch_location = (0, 0, 0)      # Start at dispatch area
        self.shelf_location = (8, 0, 5)         # Go to shelf to pick item
        self.packing_location = (-5, 0, -5)     # Go to packing station
        self.current_stage = "queue"            # Track current stage for visualization
        self.color = (0, 255, 0)

    def on_enter_block(self, block):
        # Set position based on current stage for visualization
        if "Queue" in str(type(block)):
            self.space_state["position"] = self.dispatch_location
            self.current_stage = "queue"
        elif "Seize" in str(type(block)):
            self.space_state["position"] = self.dispatch_location
            self.current_stage = "acquiring_worker"
        elif "MoveBlock" in str(type(block)):
            # Position will be handled by the MoveBlock based on movement
            # For fixed visualization during move actions, we can update positions
            if hasattr(self, 'current_stage') and self.current_stage == "going_to_shelf":
                # During move to shelf, update position as it moves
                pass  # MoveBlock will handle this
            elif hasattr(self, 'current_stage') and self.current_stage == "going_to_packing":
                # During move to packing station, update position as it moves
                pass  # MoveBlock will handle this
        elif "Delay" in str(type(block)):
            # Set position based on which delay (picking or packing)
            if hasattr(self, 'current_stage') and self.current_stage == "picking":
                self.space_state["position"] = self.shelf_location
            elif hasattr(self, 'current_stage') and self.current_stage == "packing":
                self.space_state["position"] = self.packing_location
        elif "Release" in str(type(block)):
            self.space_state["position"] = self.packing_location
            self.current_stage = "releasing_worker"
        elif "Sink" in str(type(block)):
            self.space_state["position"] = (0, -10, 0)  # Completed orders area
            self.current_stage = "completed"

def main():
    # Create simulator with 3D visualization
    sim = Simulator(max_ticks=100)

    # Create a NoCollisionSpace for spatial movement
    warehouse_space = NoCollisionSpace()

    # Create a Pygame 3D viewer
    viewer = Pygame3DViewer(sim, width=1000, height=700)
    sim.viewer = viewer

    # Create a ResourcePool with 3 worker resources
    worker_pool = ResourcePool(
        name="warehouse_workers",
        simulator=sim,
        resource_type="worker",
        initial_resources=[
            ResourceAgent(resource_id="worker_1", resource_type="worker"),
            ResourceAgent(resource_id="worker_2", resource_type="worker"),
            ResourceAgent(resource_id="worker_3", resource_type="worker")
        ]
    )

    # Set initial positions for worker resources (in a circle around dispatch area)
    for i, resource in enumerate(worker_pool.available_resources):
        angle = 2 * math.pi * i / 3
        x = 3 * math.cos(angle)
        z = 3 * math.sin(angle)
        resource.space_state["position"] = (x, 0.5, z)  # Y=0.5 to make them visible above floor

    # Register the space with the simulator
    sim.add_space("warehouse", warehouse_space)

    # Create blocks following warehouse fulfillment process:
    # 1. Source: Generate orders
    source = SourceBlock(
        simulator=sim,
        agent_class=OrderAgent,
        spawn_schedule=lambda tick: 1 if tick % 4 == 0 and tick <= 40 else 0  # Spawn orders every 4 ticks
    )

    # 2. Queue: Orders wait for workers
    queue = QueueBlock(simulator=sim)

    # 3. Seize: Acquire worker
    acquire_worker = SeizeBlock(simulator=sim, resource_pool=worker_pool, resource_count=1)

    # 4. Move: Go from dispatch to shelf
    go_to_shelf = MoveBlock(simulator=sim, space_name="warehouse", speed=1.0)

    # 5. Delay: Pick item
    picking_time = DelayBlock(simulator=sim, delay_ticks=5)

    # 6. Move: Go from shelf to packing station
    go_to_packing = MoveBlock(simulator=sim, space_name="warehouse", speed=1.0)

    # 7. Delay: Pack order
    packing_time = DelayBlock(simulator=sim, delay_ticks=3)

    # 8. Release: Release worker back to pool
    release_worker = ReleaseBlock(simulator=sim, resource_pool=worker_pool)

    # 9. Sink: Completed orders
    completed_orders = SinkBlock(simulator=sim)

    # Connect the blocks in the process flow
    source.connect(queue)
    queue.connect(acquire_worker)
    acquire_worker.connect(go_to_shelf)

    # We need to set the start and target positions for the move blocks
    # This requires setting these on the agents before they reach the move blocks
    # We'll use block callbacks to update agent positions
    def on_going_to_shelf(agent):
        if isinstance(agent, OrderAgent):
            agent.start_position = agent.dispatch_location
            agent.target_position = agent.shelf_location
            agent.current_stage = "going_to_shelf"

            # Update the agent's position as it moves
            if "position" not in agent.space_state:
                agent.space_state["position"] = agent.start_position

    def on_shelf_arrival(agent):
        if isinstance(agent, OrderAgent):
            agent.current_stage = "picking"
            # Agent should be at shelf location now
            agent.space_state["position"] = agent.shelf_location

    def on_going_to_packing(agent):
        if isinstance(agent, OrderAgent):
            agent.start_position = agent.shelf_location
            agent.target_position = agent.packing_location
            agent.current_stage = "going_to_packing"

    def on_packing_arrival(agent):
        if isinstance(agent, OrderAgent):
            agent.current_stage = "packing"
            # Agent should be at packing location now
            agent.space_state["position"] = agent.packing_location

    # Set up callbacks
    go_to_shelf.on_enter = on_going_to_shelf
    picking_time.on_enter = on_shelf_arrival
    go_to_packing.on_enter = on_going_to_packing
    packing_time.on_enter = on_packing_arrival

    # Connect the remaining blocks
    go_to_shelf.connect(picking_time)
    picking_time.connect(go_to_packing)
    go_to_packing.connect(packing_time)
    packing_time.connect(release_worker)
    release_worker.connect(completed_orders)

    # Run simulation
    print("Starting warehouse fulfillment simulation with 3D visualization...")
    print("Controls: Left-click + drag to rotate, mouse wheel to zoom, ESC to quit")
    print("Blue dots = orders, Green dots = workers, Red/Green/Blue lines = axes")
    sim.run()

    print(f"Simulation completed!")
    print(f"Orders completed: {completed_orders.count}")
    print(f"Workers available: {worker_pool.get_available_count()}")
    print(f"Workers occupied: {worker_pool.get_occupied_count()}")

    # Keep the window open for post-simulation navigation
    viewer.show_final()

if __name__ == "__main__":
    main()