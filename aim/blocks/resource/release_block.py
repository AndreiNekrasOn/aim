from typing import Optional
from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.core.simulator import Simulator
from aim.entities.resource.resource_pool import ResourcePool

class ReleaseBlock(BaseBlock):
    """
    Block that releases resources previously acquired by an agent in a Seize block.
    """
    
    def __init__(
        self,
        simulator: Simulator,
        resource_pool: ResourcePool
    ):
        """
        Initialize a Release block.
        
        :param simulator: The simulator instance
        :param resource_pool: The ResourcePool to release resources to
        """
        super().__init__(simulator)
        self.resource_pool = resource_pool
    
    def take(self, agent: BaseAgent) -> None:
        """
        Release resources for the agent and pass it to the next block.
        """
        # Enter the block first
        agent._enter_block(self)
        if self.on_enter:
            self.on_enter(agent)
        
        # Get the resources that were acquired by this agent
        if hasattr(agent, '_acquired_resources'):
            resources_to_release = agent._acquired_resources
            resource_pool = agent._resource_pool
            
            # Release the resources back to the pool
            released_count = resource_pool.release_resources(resources_to_release)
            
            # Clean up agent's resource tracking
            if hasattr(agent, '_acquired_resources'):
                delattr(agent, '_acquired_resources')
            if hasattr(agent, '_resource_pool'):
                delattr(agent, '_resource_pool')
        else:
            released_count = 0  # Agent didn't have any resources to release
        
        # Eject to next block
        self._eject(agent)
    
    def _tick(self) -> None:
        """
        Release block doesn't need special tick logic.
        """
        pass