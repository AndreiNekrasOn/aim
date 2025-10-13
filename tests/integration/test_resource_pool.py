"""
Integration test for Resource Pool functionality
"""

from aim import Simulator, BaseAgent, ResourcePool, ResourceAgent, SeizeBlock, ReleaseBlock, QueueBlock, SinkBlock
from aim.blocks.source import SourceBlock
from aim.blocks.delay import DelayBlock

# Define custom agent types
class TaskAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.work_location = (5, 5, 0)  # Example location

def test_resource_pool():
    # Create a simulator
    sim = Simulator(max_ticks=20)
    
    # Create a ResourcePool with 2 resources
    resource_pool = ResourcePool(
        name="workers",
        simulator=sim,
        resource_type="worker",
        initial_resources=[
            ResourceAgent(resource_id="worker_1", resource_type="worker"),
            ResourceAgent(resource_id="worker_2", resource_type="worker")
        ]
    )
    
    # Create blocks
    source = SourceBlock(simulator=sim, agent_class=TaskAgent, spawn_schedule=lambda tick: 1 if tick < 3 else 0)
    queue = QueueBlock(simulator=sim)
    seize = SeizeBlock(simulator=sim, resource_pool=resource_pool, resource_count=1)
    # Add delay to simulate movement/processing time with resources
    work_delay = DelayBlock(simulator=sim, delay_ticks=3)
    release = ReleaseBlock(simulator=sim, resource_pool=resource_pool)
    sink = SinkBlock(simulator=sim)
    
    # Connect blocks
    source.connect(queue)
    queue.connect(seize)
    seize.connect(work_delay)  # Simulate resource movement/delay
    work_delay.connect(release)
    release.connect(sink)
    
    # Run simulation
    sim.run()
    
    print(f"Resources available after simulation: {resource_pool.get_available_count()}")
    print(f"Resources occupied after simulation: {resource_pool.get_occupied_count()}")
    print(f"Tasks completed: {sink.count}")
    
    # Verify that all tasks were completed
    assert sink.count == 3, f"Expected 3 completed tasks, got {sink.count}"
    # Verify all resources are available after completion
    assert resource_pool.get_available_count() == 2, f"Expected 2 available resources, got {resource_pool.get_available_count()}"

def test_resource_pool_contention():
    """
    Test that resources are properly queued when not available.
    """
    sim = Simulator(max_ticks=20)
    
    # Create a ResourcePool with only 1 resource
    resource_pool = ResourcePool(
        name="single_worker",
        simulator=sim,
        resource_type="worker",
        initial_resources=[
            ResourceAgent(resource_id="worker_1", resource_type="worker")
        ]
    )
    
    # Create blocks
    source = SourceBlock(simulator=sim, agent_class=TaskAgent, spawn_schedule=lambda tick: 1 if tick <= 2 else 0)
    queue = QueueBlock(simulator=sim)
    seize = SeizeBlock(simulator=sim, resource_pool=resource_pool, resource_count=1)
    # Add delay to simulate movement/processing time with resources
    work_delay = DelayBlock(simulator=sim, delay_ticks=5)
    release = ReleaseBlock(simulator=sim, resource_pool=resource_pool)
    sink = SinkBlock(simulator=sim)
    
    # Connect blocks
    source.connect(queue)
    queue.connect(seize)
    seize.connect(work_delay)  # Simulate resource movement/delay
    work_delay.connect(release)
    release.connect(sink)
    
    # Run simulation
    sim.run()
    
    print(f"Second test - Resources available after simulation: {resource_pool.get_available_count()}")
    print(f"Second test - Resources occupied after simulation: {resource_pool.get_occupied_count()}")
    print(f"Second test - Tasks completed: {sink.count}")
    
    # With 1 resource and 5 tick delay, should process 1 task per 5 ticks
    # In 20 ticks, should complete at least 2 tasks (first starts at tick 0, second at tick 5, third would start at tick 10)
    assert sink.count >= 2, f"Expected at least 2 completed tasks with 1 resource, got {sink.count}"
    assert resource_pool.get_available_count() == 1, f"Expected 1 available resource, got {resource_pool.get_available_count()}"

if __name__ == "__main__":
    test_resource_pool()
    test_resource_pool_contention()
    print("All tests passed!")