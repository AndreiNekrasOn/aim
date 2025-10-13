from typing import List, Optional, Callable, Dict, Any
from aim.core.simulator import Simulator
from .resource_agent import ResourceAgent

class ResourcePool:
    """
    Manages a pool of ResourceAgent objects of a specific type.
    Single ResourcePool manages resources of a single type.
    """
    def __init__(
        self, 
        name: str, 
        simulator: Simulator, 
        resource_type: str,
        initial_resources: Optional[List[ResourceAgent]] = None,
        on_occupy: Optional[Callable[[ResourceAgent, 'BaseAgent'], None]] = None,
        on_free: Optional[Callable[[ResourceAgent], None]] = None,
        on_acquire: Optional[Callable[[ResourceAgent], None]] = None,
        on_release: Optional[Callable[[ResourceAgent], None]] = None
    ):
        self.name = name
        self.simulator = simulator
        self.resource_type = resource_type
        self.on_occupy = on_occupy
        self.on_free = on_free
        self.on_acquire = on_acquire
        self.on_release = on_release
        
        # Lists of available and occupied resources
        self.available_resources: List[ResourceAgent] = []
        self.occupied_resources: List[ResourceAgent] = []
        
        # Add initial resources if provided
        if initial_resources:
            for resource in initial_resources:
                if resource.is_available:
                    self.available_resources.append(resource)
                    simulator.add_agent(resource)
                else:
                    self.occupied_resources.append(resource)
                    simulator.add_agent(resource)
    
    def add_resource(self, resource: ResourceAgent) -> None:
        """
        Add a resource to the pool.
        """
        if resource.is_available:
            self.available_resources.append(resource)
        else:
            self.occupied_resources.append(resource)
        self.simulator.add_agent(resource)
    
    def seize_resources(self, count: int = 1) -> List[ResourceAgent]:
        """
        Attempt to seize resources.
        
        :param count: Number of resources to seize
        :return: List of seized resources, or empty list if not enough resources available
        """
        # If not enough resources available, return empty list
        if len(self.available_resources) < count:
            return []
        
        # Take first available resources
        selected_resources = self.available_resources[:count]
        
        # Move selected resources from available to occupied
        seized_resources = []
        for resource in selected_resources:
            self.available_resources.remove(resource)
            self.occupied_resources.append(resource)
            
            # Execute on_acquire callback if provided
            if self.on_acquire:
                self.on_acquire(resource)
            
            seized_resources.append(resource)
        
        return seized_resources
    
    def release_resources(self, resources: List[ResourceAgent]) -> int:
        """
        Release resources back to the pool.
        
        :param resources: List of resources to release
        :return: Number of resources successfully released
        """
        released_count = 0
        for resource in resources:
            if resource in self.occupied_resources:
                # Execute on_release callback if provided
                if self.on_release:
                    self.on_release(resource)
                
                # Mark as available and move to available list
                resource.is_available = True
                resource.occupied_by = None
                resource.occupied_since_tick = None
                
                self.occupied_resources.remove(resource)
                self.available_resources.append(resource)
                
                released_count += 1
        
        return released_count
    
    def get_available_count(self) -> int:
        """
        Get the number of available resources.
        """
        return len(self.available_resources)
    
    def get_occupied_count(self) -> int:
        """
        Get the number of occupied resources.
        """
        return len(self.occupied_resources)
    
    def has_any_available(self) -> bool:
        """
        Check if any resources are available.
        """
        return len(self.available_resources) > 0