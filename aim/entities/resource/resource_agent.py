from typing import Optional, Dict, Any
from aim.core.agent import BaseAgent

class ResourceAgent(BaseAgent):
    """
    Agent representing a resource that can be seized or released by other agents.
    """
    def __init__(self, resource_id: str, resource_type: str = "default", properties: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.properties = properties or {}
        self.is_available = True
        self.occupied_by: Optional[BaseAgent] = None
        self.occupied_since_tick: Optional[int] = None
        self.moving_to_task = False
        self.task_location = None
        
    def on_enter_block(self, block):
        """
        Called when resource enters a block.
        """
        pass
    
    def on_event(self, event: str):
        """
        Override this method to react to specific events.
        Events are delivered to all agents, so implement filtering here.
        """
        # Example of filtering - only respond to events relevant to this resource
        # if event.startswith(f"resource_{self.resource_id}_"):
        #     # Process resource-specific event
        #     pass
        
        # For now, this is just a placeholder for users to override
        pass