from typing import Optional, List, Dict
from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.core.simulator import Simulator
from aim.entities.resource.resource_pool import ResourcePool
from aim.entities.resource.resource_agent import ResourceAgent


class SeizeBlock(BaseBlock):
    """
    Block that attempts to acquire resources from a ResourcePool.
    If resources are not available, throws an exception to be handled by upstream Queue.
    Holds agent until acquired resources finish movement to task location.
    """
    
    def __init__(
        self,
        simulator: Simulator,
        resource_pool: ResourcePool,
        resource_count: int = 1
    ):
        """
        Initialize a Seize block.
        
        :param simulator: The simulator instance
        :param resource_pool: The ResourcePool to acquire resources from
        :param resource_count: Number of resources to acquire
        """
        super().__init__(simulator)
        self.resource_pool = resource_pool
        self.resource_count = resource_count
        # Track agents waiting for resources to finish movement
        self._agents_waiting_for_movement: List[BaseAgent] = []
        # Track which resources are moving for each agent
        self._movement_trackers: Dict[BaseAgent, List[ResourceAgent]] = {}
    
    def take(self, agent: BaseAgent) -> None:
        """
        Attempt to acquire resources for the agent.
        If successful, check if resources need to finish movement before proceeding.
        If unsuccessful, throw an exception to be handled by upstream QueueBlock.
        """
        # Try to acquire resources
        acquired_resources = self.resource_pool.seize_resources(self.resource_count)
        
        # If we couldn't acquire enough resources, raise an exception
        if len(acquired_resources) < self.resource_count:
            # Execute on_exit for the agent before raising exception
            if self.on_exit:
                self.on_exit(agent)
            
            # Raise exception to signal rejection
            raise RuntimeError(f"SeizeBlock: Not enough resources available. Needed: {self.resource_count}, Available: {len(acquired_resources)}")
        
        # Mark that agent has acquired resources (for later release)
        agent._acquired_resources = acquired_resources
        agent._resource_pool = self.resource_pool
        
        # Set occupied_by on each resource
        for resource in acquired_resources:
            resource.occupied_by = agent
            resource.is_available = False
            resource.occupied_since_tick = self._simulator.current_tick
            
            # Execute on_occupy callback if resource pool has one
            if self.resource_pool.on_occupy:
                self.resource_pool.on_occupy(resource, agent)
        
        # Process agent entry into this block
        agent._enter_block(self)
        if self.on_enter:
            self.on_enter(agent)
        
        # Check if resources need to move to task location
        # For now, we'll assume they do and hold the agent until movement completes
        # In a real spatial implementation, we'd check movement status
        if hasattr(agent, 'work_location'):
            # Add agent to waiting list for movement completion
            self._agents_waiting_for_movement.append(agent)
            self._movement_trackers[agent] = acquired_resources
            
            # Don't eject the agent yet - it will be handled in _tick()
            return  # Agent remains in this block until resources complete movement
        else:
            # No movement required, eject immediately
            self._eject(agent)
    
    def _tick(self) -> None:
        """
        Check if agents can proceed (resources have finished movement).
        """
        # For now, simulate movement completion immediately
        # In a real spatial implementation, check if resources have reached their destination
        agents_to_process = self._agents_waiting_for_movement[:]
        for agent in agents_to_process:
            # In a real spatial implementation, we would check if resources
            # have reached their target location
            # For now, we'll assume movement completes in one tick
            resources = self._movement_trackers[agent]
            
            # Remove from waiting list and eject
            self._agents_waiting_for_movement.remove(agent)
            del self._movement_trackers[agent]
            
            # Eject the agent now that resources have "moved"
            self._eject(agent)
    
    def available_count(self) -> int:
        """
        Convenience method to get how many resources are currently available.
        """
        return self.resource_pool.get_available_count()
    
    def needed_count(self) -> int:
        """
        Return the number of resources this block tries to seize.
        """
        return self.resource_count